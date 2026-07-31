from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.auth.passwords import PasswordManager
from achiwave_backend.models import (
    Campaign,
    DeviceSession,
    PushToken,
    RegisteredDevice,
    User,
)
from achiwave_backend.services.account import AccountDeactivationService
from tests.auth.test_registration import (
    PASSWORD,
    auth_settings,
    create_auth_client,
    registration_payload,
)


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client) -> dict[str, object]:
    response = client.post("/api/v1/auth/register", json=registration_payload())
    assert response.status_code == 201
    return response.json()


def login(client) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "Person@example.com",
            "password": PASSWORD,
            "installation": registration_payload()["installation"],
        },
    )
    assert response.status_code == 200
    return response.json()


def test_deactivation_revokes_access_and_preserves_history(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    before = datetime.now(UTC)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        second_session = login(client)
        with auth_session_factory.begin() as session:
            user = session.scalar(select(User))
            device = session.scalar(select(RegisteredDevice))
            assert user is not None and device is not None
            session.add_all(
                (
                    Campaign(user_id=user.id, title="Preserved campaign"),
                    PushToken(
                        user_id=user.id,
                        device_id=device.id,
                        provider="expo",
                        platform=device.platform,
                        app_environment=device.app_environment,
                        token_value="private-push-token-sentinel",
                        token_hash=b"p" * 32,
                    ),
                )
            )
        response = client.post(
            "/api/v1/account/deactivate",
            headers=bearer(registration["access_token"]),
            json={"password": PASSWORD},
        )
        protected = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )
        refresh = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": second_session["refresh_token"],
                "installation": registration_payload()["installation"],
            },
        )
        later_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "Person@example.com",
                "password": PASSWORD,
                "installation": registration_payload()["installation"],
            },
        )
    after = datetime.now(UTC)

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_state"] == "deactivated"
    assert payload["record_version"] == 2
    assert before <= datetime.fromisoformat(payload["deactivated_at"]) <= after
    assert protected.status_code == 401
    assert refresh.status_code == 401
    assert later_login.status_code == 401
    assert later_login.json()["code"] == "account_deactivated"
    with auth_session_factory() as session:
        user = session.scalar(select(User))
        session_states = set(session.scalars(select(DeviceSession.session_state)))
        device_states = set(session.scalars(select(RegisteredDevice.device_state)))
        token_states = set(session.scalars(select(PushToken.token_state)))
        campaign_count = session.scalar(select(func.count()).select_from(Campaign))
    assert user is not None and user.account_state == "deactivated"
    assert user.deactivated_at is not None
    assert session_states == {"revoked"}
    assert device_states == {"revoked"}
    assert token_states == {"invalidated"}
    assert campaign_count == 1


def test_deactivation_rejects_wrong_password_without_side_effects(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.post(
            "/api/v1/account/deactivate",
            headers=bearer(registration["access_token"]),
            json={"password": "incorrect password value"},
        )
        still_active = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"
    assert still_active.status_code == 200
    with auth_session_factory() as session:
        user = session.scalar(select(User))
        device_session = session.scalar(select(DeviceSession))
        device = session.scalar(select(RegisteredDevice))
    assert user is not None and user.account_state == "active"
    assert device_session is not None and device_session.session_state == "active"
    assert device is not None and device.device_state == "active"


def test_deactivation_service_is_idempotent_for_retained_record(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
    service = AccountDeactivationService(
        PasswordManager(auth_settings(auth_database_url))
    )
    with auth_session_factory() as session:
        user = session.get(User, registration["user"]["id"])
        assert user is not None
        first = service.deactivate(session, user_id=user.id, password=PASSWORD)
        second = service.deactivate(session, user_id=user.id, password=PASSWORD)

    assert second.deactivated_at == first.deactivated_at
    assert second.record_version == first.record_version


def test_deactivation_rolls_back_every_change_when_commit_fails(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
    service = AccountDeactivationService(
        PasswordManager(auth_settings(auth_database_url))
    )
    with auth_session_factory() as session:
        user_id = registration["user"]["id"]
        session.commit = Mock(side_effect=RuntimeError("forced rollback"))
        with pytest.raises(RuntimeError, match="forced rollback"):
            service.deactivate(session, user_id=user_id, password=PASSWORD)

    with auth_session_factory() as session:
        user = session.get(User, user_id)
        device_session = session.scalar(select(DeviceSession))
        device = session.scalar(select(RegisteredDevice))
    assert user is not None and user.account_state == "active"
    assert device_session is not None and device_session.session_state == "active"
    assert device is not None and device.device_state == "active"

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import DeviceSession, RegisteredDevice, User
from tests.auth.test_registration import create_auth_client, registration_payload


def register(client) -> dict[str, object]:
    response = client.post("/api/v1/auth/register", json=registration_payload())
    assert response.status_code == 201
    return response.json()


def refresh_payload(
    registration: dict[str, object],
    *,
    app_environment: str = "development",
) -> dict[str, object]:
    installation = dict(registration_payload()["installation"])
    installation["app_environment"] = app_environment
    return {
        "refresh_token": registration["refresh_token"],
        "installation": installation,
    }


def test_refresh_rotates_credential_and_links_replacement(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(registration),
        )

    assert response.status_code == 200
    result = response.json()
    assert result["session_id"] != registration["session_id"]
    assert result["access_token"] != registration["access_token"]
    assert result["refresh_token"] != registration["refresh_token"]

    with auth_session_factory() as session:
        prior = session.get(DeviceSession, UUID(str(registration["session_id"])))
        replacement = session.get(DeviceSession, UUID(result["session_id"]))
    assert prior is not None and prior.session_state == "replaced"
    assert prior.replaced_at is not None
    assert prior.replaced_by_session_id == replacement.id
    assert replacement is not None and replacement.session_state == "active"


def test_expired_and_revoked_refresh_tokens_are_rejected(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        expired_registration = register(client)
        with auth_session_factory.begin() as session:
            current = session.get(
                DeviceSession,
                UUID(str(expired_registration["session_id"])),
            )
            assert current is not None
            current.expires_at = current.created_at + timedelta(microseconds=1)
        expired = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(expired_registration),
        )

        second_payload = registration_payload(
            email="second@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "20000000-0000-4000-8000-000000000002",
            },
        )
        second_response = client.post("/api/v1/auth/register", json=second_payload)
        assert second_response.status_code == 201
        revoked_registration = second_response.json()
        with auth_session_factory.begin() as session:
            current = session.get(
                DeviceSession,
                UUID(str(revoked_registration["session_id"])),
            )
            assert current is not None
            current.session_state = "revoked"
            current.revoked_at = datetime.now(UTC)
        revoked = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": revoked_registration["refresh_token"],
                "installation": second_payload["installation"],
            },
        )

    assert expired.status_code == 401
    assert expired.json()["code"] == "session_expired"
    assert revoked.status_code == 401
    assert revoked.json()["code"] == "session_revoked"


def test_replaced_token_reuse_revokes_replacement_chain(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        rotated = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(registration),
        )
        assert rotated.status_code == 200
        reuse = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(registration),
        )
        replacement_retry = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": rotated.json()["refresh_token"],
                "installation": registration_payload()["installation"],
            },
        )

    assert reuse.status_code == 401
    assert reuse.json()["code"] == "refresh_token_reuse_detected"
    assert replacement_retry.status_code == 401
    assert replacement_retry.json()["code"] == "session_revoked"
    with auth_session_factory() as session:
        active_count = session.scalar(
            select(func.count())
            .select_from(DeviceSession)
            .where(DeviceSession.session_state == "active")
        )
    assert active_count == 0


def test_concurrent_refresh_attempts_cannot_both_succeed(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
    payload = refresh_payload(registration)
    barrier = Barrier(2)

    def submit_refresh() -> int:
        with create_auth_client(auth_database_url, auth_session_factory) as client:
            barrier.wait(timeout=5)
            return client.post("/api/v1/auth/refresh", json=payload).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _: submit_refresh(), range(2)))

    assert statuses == [200, 401]
    with auth_session_factory() as session:
        active_count = session.scalar(
            select(func.count())
            .select_from(DeviceSession)
            .where(DeviceSession.session_state == "active")
        )
    assert active_count <= 1


def test_refresh_rejects_revoked_device_deactivated_user_and_wrong_environment(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        wrong_environment = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(registration, app_environment="preview"),
        )
        assert wrong_environment.status_code == 401
        assert wrong_environment.json()["code"] == "invalid_refresh_token"

        with auth_session_factory.begin() as session:
            device = session.get(
                RegisteredDevice,
                UUID(str(registration["device_id"])),
            )
            assert device is not None
            device.device_state = "revoked"
            device.revoked_at = datetime.now(UTC)
        revoked_device = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(registration),
        )
        assert revoked_device.status_code == 401
        assert revoked_device.json()["code"] == "device_revoked"

    with auth_session_factory.begin() as session:
        user = session.scalar(select(User))
        assert user is not None
        user.account_state = "deactivated"
        user.deactivated_at = datetime.now(UTC)
        device = session.get(
            RegisteredDevice,
            UUID(str(registration["device_id"])),
        )
        assert device is not None
        device.device_state = "active"
        device.revoked_at = None
        current = session.get(
            DeviceSession,
            UUID(str(registration["session_id"])),
        )
        assert current is not None
        current.session_state = "active"
        current.revoked_at = None
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        deactivated = client.post(
            "/api/v1/auth/refresh",
            json=refresh_payload(registration),
        )
    assert deactivated.status_code == 401
    assert deactivated.json()["code"] == "account_deactivated"


def test_rotation_failure_rolls_back_prior_session(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        monkeypatch.setattr(
            "achiwave_backend.auth.tokens.secrets.token_urlsafe",
            lambda _: registration["refresh_token"],
        )
        with pytest.raises(IntegrityError):
            client.post(
                "/api/v1/auth/refresh",
                json=refresh_payload(registration),
            )

    with auth_session_factory() as session:
        prior = session.get(DeviceSession, UUID(str(registration["session_id"])))
        count = session.scalar(select(func.count()).select_from(DeviceSession))
    assert prior is not None and prior.session_state == "active"
    assert count == 1

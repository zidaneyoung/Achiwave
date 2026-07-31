from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.models import DeviceSession, RegisteredDevice, User
from tests.auth.test_registration import (
    SIGNING_KEY,
    create_auth_client,
    registration_payload,
)


def register(client, **overrides: object) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json=registration_payload(**overrides),
    )
    assert response.status_code == 201
    return response.json()


def bearer(token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def rewrite_token(token: object, **claims: object) -> str:
    payload = jwt.decode(str(token), options={"verify_signature": False})
    payload.update(claims)
    return jwt.encode(payload, SIGNING_KEY, algorithm="HS256")


def test_current_user_requires_valid_bearer_token(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        missing = client.get("/api/v1/users/me")
        malformed = client.get(
            "/api/v1/users/me",
            headers=bearer("not-a-jwt"),
        )

    assert missing.status_code == 401
    assert malformed.status_code == 401
    assert missing.json()["code"] == "invalid_access_token"
    assert malformed.json()["code"] == "invalid_access_token"
    assert missing.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    ("token_factory", "expected_code"),
    [
        (
            lambda token: jwt.encode(
                jwt.decode(str(token), options={"verify_signature": False}),
                "different-signing-key-value-123456789012345",
                algorithm="HS256",
            ),
            "invalid_access_token",
        ),
        (lambda token: rewrite_token(token, iss="wrong-issuer"), "invalid_access_token"),
        (
            lambda token: rewrite_token(token, aud="wrong-audience"),
            "invalid_access_token",
        ),
        (
            lambda token: rewrite_token(
                token,
                exp=datetime.now(UTC) - timedelta(minutes=1),
            ),
            "session_expired",
        ),
    ],
)
def test_current_user_rejects_invalid_token_claims(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
    token_factory,
    expected_code: str,
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.get(
            "/api/v1/users/me",
            headers=bearer(token_factory(registration["access_token"])),
        )

    assert response.status_code == 401
    assert response.json()["code"] == expected_code


def test_current_user_rejects_revoked_and_replaced_sessions(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        with auth_session_factory.begin() as session:
            stored = session.get(
                DeviceSession,
                UUID(str(registration["session_id"])),
            )
            assert stored is not None
            stored.session_state = "revoked"
            stored.revoked_at = datetime.now(UTC)
        revoked = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )

    assert revoked.status_code == 401
    assert revoked.json()["code"] == "session_revoked"

    with auth_session_factory.begin() as session:
        stored = session.get(
            DeviceSession,
            UUID(str(registration["session_id"])),
        )
        assert stored is not None
        stored.session_state = "active"
        stored.revoked_at = None
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        rotation = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": registration["refresh_token"],
                "installation": registration_payload()["installation"],
            },
        )
        assert rotation.status_code == 200
        replaced = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )
    assert replaced.status_code == 401
    assert replaced.json()["code"] == "session_revoked"


def test_current_user_rejects_revoked_device_and_deactivated_user(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        with auth_session_factory.begin() as session:
            device = session.get(
                RegisteredDevice,
                UUID(str(registration["device_id"])),
            )
            assert device is not None
            device.device_state = "revoked"
            device.revoked_at = datetime.now(UTC)
        revoked_device = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )
    assert revoked_device.status_code == 401
    assert revoked_device.json()["code"] == "device_revoked"

    with auth_session_factory.begin() as session:
        device = session.get(
            RegisteredDevice,
            UUID(str(registration["device_id"])),
        )
        user = session.get(User, UUID(str(registration["user"]["id"])))
        assert device is not None and user is not None
        device.device_state = "active"
        device.revoked_at = None
        user.account_state = "deactivated"
        user.deactivated_at = datetime.now(UTC)
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        deactivated = client.get(
            "/api/v1/users/me",
            headers=bearer(registration["access_token"]),
        )
    assert deactivated.status_code == 401
    assert deactivated.json()["code"] == "account_deactivated"


def test_current_user_returns_only_authenticated_owner_and_rejects_cross_user_token(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        first = register(client)
        second = register(
            client,
            email="second@example.com",
            installation={
                **dict(registration_payload()["installation"]),
                "installation_id": "30000000-0000-4000-8000-000000000003",
            },
        )
        current = client.get(
            "/api/v1/users/me",
            headers=bearer(first["access_token"]),
        )
        mismatched = rewrite_token(
            first["access_token"],
            sub=second["user"]["id"],
        )
        cross_user = client.get(
            "/api/v1/users/me",
            headers=bearer(mismatched),
        )

    assert current.status_code == 200
    assert current.json() == first["user"]
    assert cross_user.status_code == 401
    assert cross_user.json()["code"] == "invalid_access_token"


def test_health_endpoints_remain_public(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

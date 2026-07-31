import hashlib
import logging
from io import StringIO
from unittest.mock import Mock
from uuid import UUID

from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.config import Settings
from achiwave_backend.logging_config import create_json_handler
from achiwave_backend.main import create_app
from achiwave_backend.models import (
    DeviceSession,
    RegisteredDevice,
    User,
    UserPreference,
)

SIGNING_KEY = "registration-test-signing-key-value-1234567890"
PASSWORD = "correct horse battery staple"


def auth_settings(database_url: str) -> Settings:
    return Settings(
        _env_file=None,
        app_environment="test",
        database_url=database_url,
        access_token_signing_key=SIGNING_KEY,
    )


def registration_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "email": "Person@example.com",
        "password": PASSWORD,
        "timezone_name": "America/Halifax",
        "installation": {
            "installation_id": "10000000-0000-4000-8000-000000000001",
            "platform": "android",
            "app_environment": "development",
            "app_version": "1.0.0",
            "build_version": "1",
        },
    }
    payload.update(overrides)
    return payload


def create_auth_client(
    database_url: str,
    session_factory: sessionmaker[Session],
    *,
    request_logger: logging.Logger | None = None,
) -> TestClient:
    return TestClient(
        create_app(
            auth_settings(database_url),
            database_check=Mock(),
            redis_check=Mock(),
            request_logger=request_logger,
            session_factory=session_factory,
        )
    )


def test_registration_creates_private_credentials_and_owned_records(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(
        auth_database_url,
        auth_session_factory,
    ) as client:
        response = client.post("/api/v1/auth/register", json=registration_payload())

    assert response.status_code == 201
    result = response.json()
    assert result["user"]["email"] == "Person@example.com"
    assert result["user"]["account_state"] == "active"
    assert result["timezone_name"] == "America/Halifax"
    assert result["timezone_was_defaulted"] is False
    assert result["token_type"] == "bearer"
    UUID(result["device_id"])
    UUID(result["session_id"])

    with auth_session_factory() as session:
        user = session.scalar(select(User))
        preference = session.scalar(select(UserPreference))
        device = session.scalar(select(RegisteredDevice))
        device_session = session.scalar(select(DeviceSession))

    assert user is not None
    assert user.canonical_email == "person@example.com"
    assert user.password_hash is not None
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash
    assert PasswordHasher().verify(user.password_hash, PASSWORD)
    assert preference is not None and preference.user_id == user.id
    assert device is not None and device.user_id == user.id
    assert device.installation_id == (
        "10000000-0000-4000-8000-000000000001"
    )
    assert device_session is not None and device_session.user_id == user.id
    assert device_session.device_id == device.id
    refresh_token = result["refresh_token"]
    assert refresh_token.encode() != device_session.credential_digest
    assert hashlib.sha256(refresh_token.encode()).digest() == (
        device_session.credential_digest
    )
    assert PASSWORD not in repr(user)
    assert user.password_hash not in repr(user)


def test_duplicate_canonical_email_is_safe_and_atomic(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(
        auth_database_url,
        auth_session_factory,
    ) as client:
        first = client.post("/api/v1/auth/register", json=registration_payload())
        duplicate = client.post(
            "/api/v1/auth/register",
            json=registration_payload(email="  PERSON@EXAMPLE.COM  "),
        )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json() == {
        "code": "email_already_registered",
        "message": "An account cannot be registered with those credentials.",
    }
    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1
        assert session.scalar(select(func.count()).select_from(UserPreference)) == 1
        assert session.scalar(select(func.count()).select_from(RegisteredDevice)) == 1
        assert session.scalar(select(func.count()).select_from(DeviceSession)) == 1


def test_registration_rejects_invalid_email_and_password_lengths(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(
        auth_database_url,
        auth_session_factory,
    ) as client:
        invalid_email = client.post(
            "/api/v1/auth/register",
            json=registration_payload(email="not-an-email"),
        )
        weak_password = client.post(
            "/api/v1/auth/register",
            json=registration_payload(password="too short"),
        )
        oversized_password = client.post(
            "/api/v1/auth/register",
            json=registration_payload(password="x" * 129),
        )

    assert invalid_email.status_code == 422
    assert invalid_email.json()["code"] == "validation_error"
    assert weak_password.status_code == 422
    assert weak_password.json()["code"] == "validation_error"
    assert oversized_password.status_code == 422
    assert oversized_password.json()["code"] == "validation_error"


def test_missing_or_invalid_timezone_defaults_to_utc(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(
        auth_database_url,
        auth_session_factory,
    ) as client:
        response = client.post(
            "/api/v1/auth/register",
            json=registration_payload(timezone_name="AST"),
        )

    assert response.status_code == 201
    assert response.json()["timezone_name"] == "UTC"
    assert response.json()["timezone_was_defaulted"] is True


def test_registration_logs_no_request_or_credential_secret(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    stream = StringIO()
    logger = logging.getLogger("achiwave.test.registration")
    logger.handlers = [create_json_handler(auth_settings(auth_database_url), stream)]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    with create_auth_client(
        auth_database_url,
        auth_session_factory,
        request_logger=logger,
    ) as client:
        response = client.post("/api/v1/auth/register", json=registration_payload())

    assert response.status_code == 201
    output = stream.getvalue()
    assert PASSWORD not in output
    assert response.json()["access_token"] not in output
    assert response.json()["refresh_token"] not in output

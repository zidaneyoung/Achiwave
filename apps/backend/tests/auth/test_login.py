import hashlib
import logging
from datetime import UTC, datetime
from io import StringIO

from argon2 import PasswordHasher
from argon2.low_level import Type
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.logging_config import create_json_handler
from achiwave_backend.models import DeviceSession, RegisteredDevice, User
from tests.auth.test_registration import (
    PASSWORD,
    auth_settings,
    create_auth_client,
    registration_payload,
)


def login_payload(**overrides: object) -> dict[str, object]:
    registration = registration_payload()
    payload = {
        "email": registration["email"],
        "password": registration["password"],
        "installation": registration["installation"],
    }
    payload.update(overrides)
    return payload


def register(client) -> dict[str, object]:
    response = client.post("/api/v1/auth/register", json=registration_payload())
    assert response.status_code == 201
    return response.json()


def test_login_reuses_owned_device_and_issues_new_session(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        response = client.post("/api/v1/auth/login", json=login_payload())

    assert response.status_code == 200
    result = response.json()
    assert result["user"]["email"] == "Person@example.com"
    assert result["device_id"] == registration["device_id"]
    assert result["session_id"] != registration["session_id"]
    assert result["access_token"] != registration["access_token"]
    assert result["refresh_token"] != registration["refresh_token"]

    with auth_session_factory() as session:
        assert session.scalar(select(func.count()).select_from(RegisteredDevice)) == 1
        assert session.scalar(select(func.count()).select_from(DeviceSession)) == 2
        login_session = session.get(DeviceSession, result["session_id"])
    assert login_session is not None
    assert hashlib.sha256(result["refresh_token"].encode()).digest() == (
        login_session.credential_digest
    )


def test_unknown_email_and_wrong_password_are_indistinguishable(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        register(client)
        wrong_password = client.post(
            "/api/v1/auth/login",
            json=login_payload(password="wrong password value"),
        )
        unknown_email = client.post(
            "/api/v1/auth/login",
            json=login_payload(email="unknown@example.com"),
        )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {
        "code": "invalid_credentials",
        "message": "The supplied credentials are invalid.",
    }
    assert wrong_password.headers["www-authenticate"] == "Bearer"
    assert unknown_email.headers["www-authenticate"] == "Bearer"


def test_deactivated_account_returns_controlled_result(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        register(client)
        with auth_session_factory.begin() as session:
            user = session.scalar(select(User))
            assert user is not None
            user.account_state = "deactivated"
            user.deactivated_at = datetime.now(UTC)
        response = client.post("/api/v1/auth/login", json=login_payload())

    assert response.status_code == 401
    assert response.json()["code"] == "account_deactivated"


def test_login_rejects_mismatched_known_device_context(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        register(client)
        with auth_session_factory.begin() as session:
            device = session.scalar(select(RegisteredDevice))
            assert device is not None
            device.platform = "ios"
        response = client.post("/api/v1/auth/login", json=login_payload())

    assert response.status_code == 409
    assert response.json()["code"] == "invalid_device_context"


def test_login_rehashes_outdated_argon2id_password(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    outdated_hash = PasswordHasher(
        time_cost=1,
        memory_cost=8192,
        parallelism=1,
        type=Type.ID,
    ).hash(PASSWORD)

    with create_auth_client(auth_database_url, auth_session_factory) as client:
        register(client)
        with auth_session_factory.begin() as session:
            user = session.scalar(select(User))
            assert user is not None
            user.password_hash = outdated_hash
        response = client.post("/api/v1/auth/login", json=login_payload())

    assert response.status_code == 200
    with auth_session_factory() as session:
        user = session.scalar(select(User))
    assert user is not None and user.password_hash is not None
    assert user.password_hash != outdated_hash
    assert PasswordHasher().verify(user.password_hash, PASSWORD)


def test_login_logs_no_credentials_or_tokens(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    stream = StringIO()
    logger = logging.getLogger("achiwave.test.login")
    logger.handlers = [create_json_handler(auth_settings(auth_database_url), stream)]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    with create_auth_client(
        auth_database_url,
        auth_session_factory,
        request_logger=logger,
    ) as client:
        register(client)
        response = client.post("/api/v1/auth/login", json=login_payload())

    assert response.status_code == 200
    output = stream.getvalue()
    assert PASSWORD not in output
    assert response.json()["access_token"] not in output
    assert response.json()["refresh_token"] not in output

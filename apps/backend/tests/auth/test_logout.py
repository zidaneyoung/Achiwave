import logging
from datetime import UTC, datetime, timedelta
from io import StringIO
from uuid import UUID

import jwt
from sqlalchemy.orm import Session, sessionmaker

from achiwave_backend.logging_config import create_json_handler
from achiwave_backend.models import DeviceSession
from tests.auth.test_registration import (
    SIGNING_KEY,
    auth_settings,
    create_auth_client,
    registration_payload,
)


def register(client) -> dict[str, object]:
    response = client.post("/api/v1/auth/register", json=registration_payload())
    assert response.status_code == 201
    return response.json()


def authorization(access_token: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_logout_revokes_session_and_is_idempotent(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        body = {"refresh_token": registration["refresh_token"]}
        headers = authorization(registration["access_token"])
        first = client.post("/api/v1/auth/logout", json=body, headers=headers)
        repeated = client.post("/api/v1/auth/logout", json=body, headers=headers)
        refresh = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": registration["refresh_token"],
                "installation": registration_payload()["installation"],
            },
        )

    assert first.status_code == 204 and first.content == b""
    assert repeated.status_code == 204 and repeated.content == b""
    assert refresh.status_code == 401
    assert refresh.json()["code"] == "session_revoked"
    with auth_session_factory() as session:
        stored = session.get(
            DeviceSession,
            UUID(str(registration["session_id"])),
        )
    assert stored is not None and stored.session_state == "revoked"
    assert stored.revoked_at is not None


def test_refresh_token_can_logout_when_access_token_expired(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        registration = register(client)
        claims = jwt.decode(
            str(registration["access_token"]),
            options={"verify_signature": False},
        )
        claims["exp"] = datetime.now(UTC) - timedelta(minutes=1)
        expired_access_token = jwt.encode(claims, SIGNING_KEY, algorithm="HS256")
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": registration["refresh_token"]},
            headers=authorization(expired_access_token),
        )

    assert response.status_code == 204
    with auth_session_factory() as session:
        stored = session.get(
            DeviceSession,
            UUID(str(registration["session_id"])),
        )
    assert stored is not None and stored.session_state == "revoked"


def test_logout_requires_a_retained_valid_credential(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    with create_auth_client(auth_database_url, auth_session_factory) as client:
        missing = client.post("/api/v1/auth/logout")
        invalid = client.post(
            "/api/v1/auth/logout",
            headers=authorization("not-a-valid-token"),
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.json()["code"] == "invalid_access_token"
    assert invalid.json()["code"] == "invalid_access_token"


def test_logout_request_logs_no_tokens(
    auth_database_url: str,
    auth_session_factory: sessionmaker[Session],
) -> None:
    stream = StringIO()
    logger = logging.getLogger("achiwave.test.logout")
    logger.handlers = [create_json_handler(auth_settings(auth_database_url), stream)]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    with create_auth_client(
        auth_database_url,
        auth_session_factory,
        request_logger=logger,
    ) as client:
        registration = register(client)
        response = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": registration["refresh_token"]},
            headers=authorization(registration["access_token"]),
        )

    assert response.status_code == 204
    output = stream.getvalue()
    assert registration["access_token"] not in output
    assert registration["refresh_token"] not in output

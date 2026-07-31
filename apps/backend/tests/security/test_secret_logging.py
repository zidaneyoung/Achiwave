import json
import logging
from datetime import UTC, datetime, timedelta
from io import StringIO
from uuid import UUID

from fastapi.testclient import TestClient

from achiwave_backend.auth.tokens import IssuedCredentials
from achiwave_backend.config import Settings
from achiwave_backend.logging_config import create_json_handler
from achiwave_backend.main import create_app
from achiwave_backend.models import DeviceSession, PushToken, RegisteredDevice
from achiwave_backend.schemas.account import AccountDeactivationRequest
from achiwave_backend.schemas.auth import (
    AndroidInstallationRequest,
    LoginRequest,
    RefreshRequest,
    RegistrationResponse,
    SafeUserResponse,
)

PASSWORD = "password-sentinel-84"
PASSWORD_HASH = "password-hash-sentinel-84"
ACCESS_TOKEN = "access-token-sentinel-84"
REFRESH_TOKEN = "refresh-token-sentinel-84" * 3
CREDENTIAL_DIGEST = b"credential-digest-sentinel-84"
INSTALLATION_ID = UUID("84000000-0000-4000-8000-000000000084")
INSTALLATION_SENTINEL = str(INSTALLATION_ID)
SIGNING_KEY = "signing-key-sentinel-84"
DATABASE_PASSWORD = "database-password-sentinel-84"
REDIS_PASSWORD = "redis-password-sentinel-84"
SECURE_STORE_VALUE = "secure-store-sentinel-84"
COOKIE_VALUE = "cookie-sentinel-84"
AUTHORIZATION_VALUE = "authorization-sentinel-84"
SENTINELS = (
    PASSWORD,
    PASSWORD_HASH,
    ACCESS_TOKEN,
    REFRESH_TOKEN,
    CREDENTIAL_DIGEST.decode(),
    INSTALLATION_SENTINEL,
    SIGNING_KEY,
    DATABASE_PASSWORD,
    REDIS_PASSWORD,
    SECURE_STORE_VALUE,
    COOKIE_VALUE,
    AUTHORIZATION_VALUE,
)


def create_security_logger() -> tuple[logging.Logger, StringIO]:
    stream = StringIO()
    settings = Settings(
        _env_file=None,
        app_environment="development",
        service_name="backend",
    )
    logger = logging.getLogger("achiwave.test.security")
    logger.handlers = [create_json_handler(settings, stream)]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger, stream


def assert_no_sentinels(output: str) -> None:
    for sentinel in SENTINELS:
        assert sentinel not in output


def test_normal_structured_logging_recursively_redacts_secret_fields() -> None:
    logger, stream = create_security_logger()
    correlation_id = "a" * 64

    logger.info(
        "authentication_event",
        extra={
            "correlation_id": correlation_id,
            "error_code": "invalid_credentials",
            "context": {
                "PaSsWoRd": PASSWORD,
                "password_hash": PASSWORD_HASH,
                "Authorization": f"Bearer {AUTHORIZATION_VALUE}",
                "Cookie": COOKIE_VALUE,
                "nested": [
                    {
                        "access_token": ACCESS_TOKEN,
                        "refresh_token": REFRESH_TOKEN,
                        "credential_digest": CREDENTIAL_DIGEST,
                        "SecureStoreValue": SECURE_STORE_VALUE,
                        "installation_id": INSTALLATION_SENTINEL,
                    }
                ],
                "database_url": (
                    "postgresql://user:"
                    f"{DATABASE_PASSWORD}@database/achiwave"
                ),
                "redis_url": f"redis://user:{REDIS_PASSWORD}@redis/0",
                "signing_key": SIGNING_KEY,
            },
        },
    )

    output = stream.getvalue()
    payload = json.loads(output)
    assert payload["message"] == "authentication_event"
    assert payload["correlation_id"] == correlation_id
    assert payload["error_code"] == "invalid_credentials"
    assert "[REDACTED]" in output
    assert_no_sentinels(output)


def test_exception_logging_redacts_arguments_and_exception_messages() -> None:
    logger, stream = create_security_logger()

    try:
        raise RuntimeError(f"refresh_token={REFRESH_TOKEN}")
    except RuntimeError:
        logger.exception(
            "authentication_failed %s",
            {
                "request_body": {"password": PASSWORD},
                "authorization": f"Bearer {AUTHORIZATION_VALUE}",
            },
            extra={"error_code": "authentication_failed"},
        )

    output = stream.getvalue()
    payload = json.loads(output)
    assert payload["exception_type"] == "RuntimeError"
    assert payload["error_code"] == "authentication_failed"
    assert "RuntimeError" in payload["stack"]
    assert_no_sentinels(output)


def test_http_middleware_omits_authentication_input_and_keeps_safe_context() -> None:
    logger, stream = create_security_logger()
    app = create_app(
        Settings(_env_file=None, app_environment="test"),
        database_check=lambda: True,
        redis_check=lambda: True,
        request_logger=logger,
    )

    @app.post("/security-probe")
    def security_probe() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        response = client.post(
            f"/security-probe?access_token={ACCESS_TOKEN}",
            headers={
                "Authorization": f"Bearer {AUTHORIZATION_VALUE}",
                "Cookie": f"session={COOKIE_VALUE}",
                "X-Correlation-ID": "stage4-http-84",
            },
            json={"password": PASSWORD, "refresh_token": REFRESH_TOKEN},
        )

    output = stream.getvalue()
    payload = json.loads(output)
    assert response.status_code == 200
    assert payload["message"] == "http_request"
    assert payload["route"] == "/security-probe"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] >= 0
    assert payload["correlation_id"] == "stage4-http-84"
    assert_no_sentinels(output)


def test_http_exception_log_does_not_serialize_request_credentials() -> None:
    logger, stream = create_security_logger()
    app = create_app(
        Settings(_env_file=None, app_environment="test"),
        database_check=lambda: True,
        redis_check=lambda: True,
        request_logger=logger,
    )

    @app.post("/security-error-probe")
    def security_error_probe() -> None:
        raise RuntimeError("controlled security probe failure")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            f"/security-error-probe?refresh_token={REFRESH_TOKEN}",
            headers={
                "Authorization": f"Bearer {AUTHORIZATION_VALUE}",
                "Cookie": f"session={COOKIE_VALUE}",
                "X-Correlation-ID": "stage4-http-error-84",
            },
            json={"password": PASSWORD, "access_token": ACCESS_TOKEN},
        )

    output = stream.getvalue()
    payload = json.loads(output)
    assert response.status_code == 500
    assert payload["message"] == "http_request_failed"
    assert payload["route"] == "/security-error-probe"
    assert payload["status_code"] == 500
    assert payload["duration_ms"] >= 0
    assert payload["correlation_id"] == "stage4-http-error-84"
    assert payload["exception_type"] == "RuntimeError"
    assert_no_sentinels(output)


def test_authentication_model_representations_omit_secret_fields() -> None:
    now = datetime.now(UTC)
    user_id = UUID("84000000-0000-4000-8000-000000000001")
    device_id = UUID("84000000-0000-4000-8000-000000000002")
    session_id = UUID("84000000-0000-4000-8000-000000000003")
    installation = AndroidInstallationRequest(
        installation_id=INSTALLATION_ID,
        app_environment="development",
    )
    models = (
        LoginRequest(
            email="security@example.com",
            password=PASSWORD,
            installation=installation,
        ),
        RefreshRequest(
            refresh_token=REFRESH_TOKEN,
            installation=installation,
        ),
        AccountDeactivationRequest(password=PASSWORD),
        RegistrationResponse(
            user=SafeUserResponse(
                id=user_id,
                email="security@example.com",
                display_name=None,
                account_state="active",
                record_version=1,
            ),
            timezone_name="UTC",
            timezone_was_defaulted=True,
            device_id=device_id,
            session_id=session_id,
            session_expires_at=now + timedelta(days=30),
            access_token=ACCESS_TOKEN,
            access_token_expires_at=now + timedelta(minutes=15),
            refresh_token=REFRESH_TOKEN,
        ),
        IssuedCredentials(
            access_token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            refresh_token_digest=CREDENTIAL_DIGEST,
            access_expires_at=now + timedelta(minutes=15),
            refresh_expires_at=now + timedelta(days=30),
        ),
        DeviceSession(
            id=session_id,
            user_id=user_id,
            device_id=device_id,
            credential_digest=CREDENTIAL_DIGEST,
            session_state="active",
        ),
        RegisteredDevice(
            id=device_id,
            user_id=user_id,
            platform="android",
            installation_id=INSTALLATION_SENTINEL,
            app_environment="development",
            device_state="active",
        ),
        PushToken(
            id=UUID("84000000-0000-4000-8000-000000000004"),
            user_id=user_id,
            device_id=device_id,
            provider="expo",
            platform="android",
            app_environment="development",
            token_value=ACCESS_TOKEN,
            token_hash=CREDENTIAL_DIGEST,
            token_state="active",
        ),
        Settings(
            _env_file=None,
            database_url=(
                "postgresql://user:"
                f"{DATABASE_PASSWORD}@database/achiwave"
            ),
            redis_url=f"redis://user:{REDIS_PASSWORD}@redis/0",
            access_token_signing_key=SIGNING_KEY,
        ),
    )

    output = "\n".join(repr(model) for model in models)
    assert "LoginRequest" in output
    assert "IssuedCredentials" in output
    assert "DeviceSession" in output
    assert_no_sentinels(output)

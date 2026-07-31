import json
import logging
import re
import sys
import traceback
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import TextIO

from achiwave_backend.config import Settings

SAFE_EXTRA_FIELDS = (
    "method",
    "route",
    "status_code",
    "duration_ms",
    "error_code",
    "correlation_id",
)
REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "access_token",
    "authorization",
    "cookie",
    "credential_digest",
    "database_url",
    "installation_id",
    "password",
    "private_key",
    "redis_url",
    "refresh_token",
    "request_body",
    "secure_store",
    "securestore",
    "secret",
    "signing_key",
    "token_hash",
    "token_value",
)
SENSITIVE_KEY_VALUE = re.compile(
    r"(?i)\b(authorization|cookie|password(?:_hash)?|secret|token|"
    r"access_token|refresh_token|credential_digest|installation_id|"
    r"database_url|redis_url|signing_key)\b"
    r"([\"']?\s*[:=]\s*[\"']?)([^\"'\s,;&}]+)"
)
SENSITIVE_URL = re.compile(
    r"(?i)\b([a-z][a-z0-9+.-]*://)([^@/\s]+)@"
)
BEARER_VALUE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-=]+")
JWT_VALUE = re.compile(
    r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."
    r"[A-Za-z0-9_-]{10,}(?![A-Za-z0-9_-])"
)
OPAQUE_CREDENTIAL_VALUE = re.compile(
    r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{43,}(?![A-Za-z0-9_-])"
)
STANDARD_LOG_RECORD_FIELDS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime"}


def _normalized_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _is_sensitive_key(key: object) -> bool:
    normalized = _normalized_key(key)
    return normalized == "token" or any(
        part in normalized for part in SENSITIVE_KEY_PARTS
    )


def redact_sensitive(value: str) -> str:
    redacted = SENSITIVE_URL.sub(rf"\1{REDACTED}@", value)
    redacted = BEARER_VALUE.sub(f"Bearer {REDACTED}", redacted)
    redacted = JWT_VALUE.sub(REDACTED, redacted)
    redacted = SENSITIVE_KEY_VALUE.sub(rf"\1\2{REDACTED}", redacted)
    redacted = OPAQUE_CREDENTIAL_VALUE.sub(REDACTED, redacted)
    return redacted


def redact_structure(value: object, *, key: object | None = None) -> object:
    """Return a JSON-safe value with nested secret-bearing fields removed."""
    if key is not None and _is_sensitive_key(key):
        return REDACTED
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return redact_sensitive(value)
    if isinstance(value, bytes | bytearray | memoryview):
        return "[BINARY]"
    if isinstance(value, Mapping):
        return {
            str(nested_key): redact_structure(
                nested_value,
                key=nested_key,
            )
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, Sequence):
        return [redact_structure(item) for item in value]
    if isinstance(value, BaseException):
        return {"exception_type": type(value).__name__}
    return f"<{type(value).__name__}>"


def _safe_log_message(record: logging.LogRecord) -> str:
    if not isinstance(record.msg, str):
        return redact_sensitive(str(redact_structure(record.msg)))
    if not record.args:
        return redact_sensitive(record.msg)
    safe_args = redact_structure(record.args)
    try:
        if isinstance(record.args, Mapping):
            return redact_sensitive(record.msg % safe_args)
        return redact_sensitive(record.msg % tuple(safe_args))
    except (KeyError, TypeError, ValueError):
        return redact_sensitive(record.msg)


class JsonFormatter(logging.Formatter):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.environment = settings.app_environment
        self.service_name = settings.service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            )
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "severity": record.levelname,
            "logger": record.name,
            "message": _safe_log_message(record),
            "environment": self.environment,
            "service": self.service_name,
        }

        for field in SAFE_EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = redact_structure(
                    getattr(record, field),
                    key=field,
                )

        for field, value in record.__dict__.items():
            if (
                field in STANDARD_LOG_RECORD_FIELDS
                or field in payload
                or field.startswith("_")
            ):
                continue
            payload[field] = redact_structure(value, key=field)

        if record.exc_info is not None:
            exception_type = record.exc_info[0]
            payload["exception_type"] = (
                exception_type.__name__
                if exception_type is not None
                else "Exception"
            )
            payload["stack"] = redact_sensitive(
                "".join(traceback.format_exception(*record.exc_info))
            )

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def create_json_handler(
    settings: Settings,
    stream: TextIO | None = None,
) -> logging.Handler:
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter(settings))
    return handler


def configure_logging(settings: Settings) -> None:
    """Configure one stdout JSON handler for API and Celery processes."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(create_json_handler(settings))
    root_logger.setLevel(settings.log_level)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "celery",
        "celery.worker",
        "celery.beat",
    ):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
        logger.propagate = True

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.disabled = True
    logging.captureWarnings(True)

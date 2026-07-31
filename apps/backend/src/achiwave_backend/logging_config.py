import json
import logging
import re
import sys
import traceback
from datetime import UTC, datetime
from typing import TextIO

from achiwave_backend.config import Settings

SAFE_EXTRA_FIELDS = (
    "method",
    "route",
    "status_code",
    "duration_ms",
)
SENSITIVE_KEY_VALUE = re.compile(
    r"(?i)\b(authorization|cookie|password|secret|token)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
SENSITIVE_URL = re.compile(
    r"(?i)\b([a-z][a-z0-9+.-]*://)([^/\s:@]+):([^@/\s]+)@"
)
BEARER_VALUE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-=]+")


def redact_sensitive(value: str) -> str:
    redacted = SENSITIVE_URL.sub(r"\1[REDACTED]@", value)
    redacted = BEARER_VALUE.sub("Bearer [REDACTED]", redacted)
    redacted = SENSITIVE_KEY_VALUE.sub(r"\1\2[REDACTED]", redacted)
    return redacted


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
            "message": redact_sensitive(record.getMessage()),
            "environment": self.environment,
            "service": self.service_name,
        }

        for field in SAFE_EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)

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

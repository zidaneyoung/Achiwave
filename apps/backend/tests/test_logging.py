import json
import logging
from io import StringIO
from unittest.mock import Mock

from fastapi.testclient import TestClient

from achiwave_backend.config import Settings
from achiwave_backend.logging_config import create_json_handler
from achiwave_backend.main import create_app


def create_test_logger(
    settings: Settings,
) -> tuple[logging.Logger, StringIO]:
    stream = StringIO()
    logger = logging.getLogger(f"achiwave.test.{settings.service_name}")
    logger.handlers = [create_json_handler(settings, stream)]
    logger.propagate = False
    logger.setLevel(settings.log_level)
    return logger, stream


def test_structured_log_is_valid_json_with_required_fields() -> None:
    settings = Settings(
        _env_file=None,
        app_environment="test",
        service_name="worker",
    )
    logger, stream = create_test_logger(settings)

    logger.info("worker_started")

    payload = json.loads(stream.getvalue())
    assert payload["severity"] == "INFO"
    assert payload["logger"] == logger.name
    assert payload["message"] == "worker_started"
    assert payload["environment"] == "test"
    assert payload["service"] == "worker"
    assert payload["timestamp"].endswith("Z")


def test_structured_exception_redacts_sensitive_values() -> None:
    settings = Settings(
        _env_file=None,
        app_environment="test",
        service_name="scheduler",
    )
    logger, stream = create_test_logger(settings)

    try:
        raise RuntimeError(
            "password=hidden "
            "postgresql://person:database-secret@private-db/achiwave"
        )
    except RuntimeError:
        logger.exception(
            "task_failed token=private-token "
            "Authorization: Bearer private-bearer"
        )

    output = stream.getvalue()
    payload = json.loads(output)
    assert payload["exception_type"] == "RuntimeError"
    assert "RuntimeError" in payload["stack"]
    assert "[REDACTED]" in output
    for sensitive_value in (
        "hidden",
        "database-secret",
        "private-token",
        "private-bearer",
    ):
        assert sensitive_value not in output


def test_configured_log_level_is_respected() -> None:
    settings = Settings(_env_file=None, log_level="WARNING")
    logger, stream = create_test_logger(settings)

    logger.info("ignored")
    logger.warning("emitted")

    payload = json.loads(stream.getvalue())
    assert payload["message"] == "emitted"


def test_http_log_contains_only_safe_route_metadata() -> None:
    request_logger = Mock(spec=logging.Logger)
    app = create_app(
        Settings(_env_file=None, app_environment="test"),
        database_check=Mock(),
        redis_check=Mock(),
        request_logger=request_logger,
    )

    with TestClient(app) as client:
        response = client.get("/not-a-route?token=private")

    assert response.status_code == 404
    request_logger.log.assert_called_once()
    level, message = request_logger.log.call_args.args
    metadata = request_logger.log.call_args.kwargs["extra"]
    assert level == logging.INFO
    assert message == "http_request"
    assert metadata["method"] == "GET"
    assert metadata["route"] == "<unmatched>"
    assert metadata["status_code"] == 404
    assert metadata["duration_ms"] >= 0
    assert "private" not in str(metadata)


def test_health_request_logs_at_debug_level() -> None:
    request_logger = Mock(spec=logging.Logger)
    app = create_app(
        Settings(_env_file=None, app_environment="test"),
        database_check=Mock(),
        redis_check=Mock(),
        request_logger=request_logger,
    )

    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert request_logger.log.call_args.args == (
        logging.DEBUG,
        "http_request",
    )

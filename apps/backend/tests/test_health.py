from unittest.mock import Mock

from fastapi.testclient import TestClient

from achiwave_backend.config import Settings
from achiwave_backend.database import DatabaseUnavailableError
from achiwave_backend.main import create_app
from achiwave_backend.redis_client import RedisUnavailableError


def create_test_client(
    database_check: Mock | None = None,
    redis_check: Mock | None = None,
) -> tuple[TestClient, Mock, Mock]:
    resolved_database_check = database_check or Mock()
    resolved_redis_check = redis_check or Mock()
    app = create_app(
        Settings(_env_file=None, app_environment="test"),
        database_check=resolved_database_check,
        redis_check=resolved_redis_check,
    )
    return (
        TestClient(app),
        resolved_database_check,
        resolved_redis_check,
    )


def test_liveness_succeeds_without_querying_dependencies() -> None:
    client, database_check, redis_check = create_test_client()

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    database_check.assert_not_called()
    redis_check.assert_not_called()


def test_readiness_succeeds_when_dependencies_are_available() -> None:
    client, database_check, redis_check = create_test_client()

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "postgresql": "ok",
            "redis": "ok",
        },
    }
    database_check.assert_called_once_with()
    redis_check.assert_called_once_with()


def test_readiness_reports_postgresql_failure_without_details() -> None:
    database_check = Mock(
        side_effect=DatabaseUnavailableError("private-db:5432")
    )
    client, _, redis_check = create_test_client(database_check=database_check)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "postgresql": "unavailable",
            "redis": "ok",
        },
    }
    assert "private-db" not in response.text
    redis_check.assert_called_once_with()


def test_readiness_reports_redis_failure_without_details() -> None:
    redis_check = Mock(side_effect=RedisUnavailableError("private-cache:6379"))
    client, database_check, _ = create_test_client(redis_check=redis_check)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "postgresql": "ok",
            "redis": "unavailable",
        },
    }
    assert "private-cache" not in response.text
    database_check.assert_called_once_with()


def test_readiness_reports_multiple_dependency_failures() -> None:
    database_check = Mock(
        side_effect=DatabaseUnavailableError("private-db:5432")
    )
    redis_check = Mock(side_effect=RedisUnavailableError("private-cache:6379"))
    client, _, _ = create_test_client(
        database_check=database_check,
        redis_check=redis_check,
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "postgresql": "unavailable",
            "redis": "unavailable",
        },
    }
    assert "private-db" not in response.text
    assert "private-cache" not in response.text

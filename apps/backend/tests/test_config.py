import pytest
from pydantic import ValidationError

from achiwave_backend.config import Settings


def test_database_url_accepts_postgresql_psycopg() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://localhost/achiwave",
    )

    assert (
        settings.require_database_url()
        == "postgresql+psycopg://localhost/achiwave"
    )


def test_database_url_is_required_for_database_operations() -> None:
    settings = Settings(_env_file=None, database_url=None)

    with pytest.raises(
        ValueError,
        match="ACHIWAVE_DATABASE_URL is required for database operations",
    ):
        settings.require_database_url()


def test_database_url_rejects_malformed_value() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="not-a-database-url")


def test_application_environment_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_environment="staging")


def test_redis_url_has_a_non_secret_local_default() -> None:
    settings = Settings(_env_file=None)

    assert settings.require_redis_url() == "redis://localhost:6379/0"


def test_redis_url_rejects_malformed_value() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, redis_url="not-a-redis-url")

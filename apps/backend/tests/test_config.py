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

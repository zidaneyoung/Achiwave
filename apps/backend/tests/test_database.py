from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from achiwave_backend.config import Settings
from achiwave_backend.database import (
    Base,
    DatabaseUnavailableError,
    create_database_engine,
    create_session_factory,
    ping_database,
    session_scope,
)
from achiwave_backend.models import DeviceSession, RegisteredDevice, User, UserPreference


def test_create_database_engine_uses_bounded_pool_settings() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://localhost/achiwave",
        database_connect_timeout_seconds=4,
        database_pool_size=6,
        database_max_overflow=2,
        database_pool_timeout_seconds=2.5,
    )

    with patch("achiwave_backend.database.create_engine") as create:
        create_database_engine(settings)

    create.assert_called_once_with(
        "postgresql+psycopg://localhost/achiwave",
        connect_args={"connect_timeout": 4},
        max_overflow=2,
        pool_pre_ping=True,
        pool_size=6,
        pool_timeout=2.5,
    )


def test_session_executes_query_and_closes() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    factory = create_session_factory(engine)

    with session_scope(factory) as session:
        assert session.scalar(text("SELECT 1")) == 1
        assert session.is_active

    assert not session.in_transaction()


def test_session_rolls_back_and_closes_after_error() -> None:
    session = MagicMock(spec=Session)
    factory = MagicMock(return_value=session)

    with pytest.raises(RuntimeError, match="query failed"):
        with session_scope(factory):
            raise RuntimeError("query failed")

    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()


def test_metadata_import_registers_models_without_connecting() -> None:
    engine = MagicMock(spec=Engine)

    assert set(Base.metadata.tables) == {
        "device_sessions",
        "registered_devices",
        "user_preferences",
        "users",
    }
    assert DeviceSession.__table__ is Base.metadata.tables["device_sessions"]
    assert RegisteredDevice.__table__ is Base.metadata.tables["registered_devices"]
    assert User.__table__ is Base.metadata.tables["users"]
    assert UserPreference.__table__ is Base.metadata.tables["user_preferences"]
    engine.begin.assert_not_called()


def test_ping_database_returns_true() -> None:
    connection = MagicMock()
    connection.scalar.return_value = 1
    engine = MagicMock(spec=Engine)
    engine.connect.return_value.__enter__.return_value = connection

    assert ping_database(engine) is True


def test_ping_database_raises_controlled_error() -> None:
    engine = MagicMock(spec=Engine)
    engine.connect.side_effect = OperationalError(
        "SELECT 1",
        {},
        Exception("private-host:5432"),
    )

    with pytest.raises(DatabaseUnavailableError) as captured:
        ping_database(engine)

    assert str(captured.value) == "PostgreSQL is unavailable."
    assert "private-host" not in str(captured.value)

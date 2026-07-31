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
from achiwave_backend.models import (
    AchievementDefinition,
    AchievementProgress,
    AchievementRule,
    Campaign,
    ClientMutation,
    DeviceSession,
    LevelDefinition,
    ProgressEvent,
    PushToken,
    Quest,
    QuestCompletion,
    QuestCompletionReversal,
    QuestOccurrence,
    QuestRecurrence,
    RegisteredDevice,
    SynchronizationOperation,
    Streak,
    StreakDay,
    StreakDaySource,
    User,
    UserPreference,
    XpLedgerEntry,
)


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
        "achievement_definitions",
        "achievement_progress",
        "achievement_rules",
        "campaigns",
        "client_mutations",
        "device_sessions",
        "level_definitions",
        "push_tokens",
        "progress_events",
        "quests",
        "quest_recurrences",
        "quest_occurrences",
        "quest_completions",
        "quest_completion_reversals",
        "registered_devices",
        "synchronization_operations",
        "streak_day_sources",
        "streak_days",
        "streaks",
        "user_preferences",
        "users",
        "xp_ledger_entries",
    }
    assert Campaign.__table__ is Base.metadata.tables["campaigns"]
    assert AchievementDefinition.__table__ is Base.metadata.tables["achievement_definitions"]
    assert AchievementProgress.__table__ is Base.metadata.tables["achievement_progress"]
    assert AchievementRule.__table__ is Base.metadata.tables["achievement_rules"]
    assert ClientMutation.__table__ is Base.metadata.tables["client_mutations"]
    assert DeviceSession.__table__ is Base.metadata.tables["device_sessions"]
    assert LevelDefinition.__table__ is Base.metadata.tables["level_definitions"]
    assert PushToken.__table__ is Base.metadata.tables["push_tokens"]
    assert ProgressEvent.__table__ is Base.metadata.tables["progress_events"]
    assert Quest.__table__ is Base.metadata.tables["quests"]
    assert QuestCompletion.__table__ is Base.metadata.tables["quest_completions"]
    assert (
        QuestCompletionReversal.__table__
        is Base.metadata.tables["quest_completion_reversals"]
    )
    assert QuestOccurrence.__table__ is Base.metadata.tables["quest_occurrences"]
    assert QuestRecurrence.__table__ is Base.metadata.tables["quest_recurrences"]
    assert RegisteredDevice.__table__ is Base.metadata.tables["registered_devices"]
    assert (
        SynchronizationOperation.__table__
        is Base.metadata.tables["synchronization_operations"]
    )
    assert Streak.__table__ is Base.metadata.tables["streaks"]
    assert StreakDay.__table__ is Base.metadata.tables["streak_days"]
    assert StreakDaySource.__table__ is Base.metadata.tables["streak_day_sources"]
    assert User.__table__ is Base.metadata.tables["users"]
    assert UserPreference.__table__ is Base.metadata.tables["user_preferences"]
    assert XpLedgerEntry.__table__ is Base.metadata.tables["xp_ledger_entries"]
    engine.begin.assert_not_called()


def test_push_token_model_repr_does_not_expose_sensitive_value() -> None:
    token = PushToken(token_value="private-token", token_hash=b"x" * 32)

    assert "private-token" not in repr(token)
    assert PushToken.__table__.c.token_value.info == {"sensitive": True}


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

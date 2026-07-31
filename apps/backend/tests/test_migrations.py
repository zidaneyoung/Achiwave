from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from achiwave_backend.database import Base
from achiwave_backend.models import (
    AchievementDefinition,
    AchievementProgress,
    AchievementRule,
    AchievementUnlock,
    Campaign,
    ClientMutation,
    DeviceSession,
    LevelDefinition,
    Notification,
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

BACKEND_ROOT = Path(__file__).parents[1]


def test_stage3_migrations_have_one_alembic_head() -> None:
    configuration = Config(BACKEND_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(configuration)

    assert scripts.get_heads() == ["20260731_0057"]


def test_stage3_metadata_registers_current_tables() -> None:
    assert set(Base.metadata.tables) == {
        "achievement_definitions",
        "achievement_progress",
        "achievement_rules",
        "achievement_unlocks",
        "campaigns",
        "client_mutations",
        "device_sessions",
        "level_definitions",
        "notifications",
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
    assert AchievementUnlock.__table__ is Base.metadata.tables["achievement_unlocks"]
    assert ClientMutation.__table__ is Base.metadata.tables["client_mutations"]
    assert DeviceSession.__table__ is Base.metadata.tables["device_sessions"]
    assert LevelDefinition.__table__ is Base.metadata.tables["level_definitions"]
    assert Notification.__table__ is Base.metadata.tables["notifications"]
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

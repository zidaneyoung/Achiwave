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
    EvidenceAttachment,
    LevelDefinition,
    Notification,
    NotificationDelivery,
    OutboxEvent,
    ProgressEvent,
    PushToken,
    Quest,
    QuestCompletion,
    QuestCompletionReversal,
    QuestOccurrence,
    QuestRecurrence,
    RegisteredDevice,
    Reminder,
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

    assert scripts.get_heads() == ["20260731_0062"]


def test_stage3_metadata_registers_current_tables() -> None:
    assert set(Base.metadata.tables) == {
        "achievement_definitions",
        "achievement_progress",
        "achievement_rules",
        "achievement_unlocks",
        "campaigns",
        "client_mutations",
        "device_sessions",
        "evidence_attachments",
        "level_definitions",
        "notifications",
        "notification_deliveries",
        "outbox_events",
        "push_tokens",
        "progress_events",
        "quests",
        "quest_recurrences",
        "quest_occurrences",
        "quest_completions",
        "quest_completion_reversals",
        "registered_devices",
        "reminders",
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
    assert EvidenceAttachment.__table__ is Base.metadata.tables["evidence_attachments"]
    assert LevelDefinition.__table__ is Base.metadata.tables["level_definitions"]
    assert Notification.__table__ is Base.metadata.tables["notifications"]
    assert NotificationDelivery.__table__ is Base.metadata.tables["notification_deliveries"]
    assert OutboxEvent.__table__ is Base.metadata.tables["outbox_events"]
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
    assert Reminder.__table__ is Base.metadata.tables["reminders"]
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


def test_stage3_foreign_keys_define_deletion_behaviour() -> None:
    foreign_keys = [
        foreign_key
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_key_constraints
    ]

    assert len(foreign_keys) == 51
    assert all(foreign_key.ondelete is not None for foreign_key in foreign_keys)
    assert {
        foreign_key.name
        for foreign_key in foreign_keys
        if foreign_key.ondelete == "CASCADE"
    } == {"fk_user_preferences_user_id_users"}
    assert all(
        foreign_key.ondelete == "CASCADE"
        or foreign_key.ondelete == "RESTRICT"
        for foreign_key in foreign_keys
    )

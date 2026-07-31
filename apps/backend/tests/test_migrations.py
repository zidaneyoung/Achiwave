from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from achiwave_backend.database import Base
from achiwave_backend.models import (
    Campaign,
    DeviceSession,
    PushToken,
    Quest,
    QuestRecurrence,
    RegisteredDevice,
    User,
    UserPreference,
)

BACKEND_ROOT = Path(__file__).parents[1]


def test_stage3_migrations_have_one_alembic_head() -> None:
    configuration = Config(BACKEND_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(configuration)

    assert scripts.get_heads() == ["20260731_0044"]


def test_stage3_metadata_registers_current_tables() -> None:
    assert set(Base.metadata.tables) == {
        "campaigns",
        "device_sessions",
        "push_tokens",
        "quests",
        "quest_recurrences",
        "registered_devices",
        "user_preferences",
        "users",
    }
    assert Campaign.__table__ is Base.metadata.tables["campaigns"]
    assert DeviceSession.__table__ is Base.metadata.tables["device_sessions"]
    assert PushToken.__table__ is Base.metadata.tables["push_tokens"]
    assert Quest.__table__ is Base.metadata.tables["quests"]
    assert QuestRecurrence.__table__ is Base.metadata.tables["quest_recurrences"]
    assert RegisteredDevice.__table__ is Base.metadata.tables["registered_devices"]
    assert User.__table__ is Base.metadata.tables["users"]
    assert UserPreference.__table__ is Base.metadata.tables["user_preferences"]

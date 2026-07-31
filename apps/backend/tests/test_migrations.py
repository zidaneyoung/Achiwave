from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from achiwave_backend.database import Base

BACKEND_ROOT = Path(__file__).parents[1]


def test_stage2_baseline_is_the_only_alembic_head() -> None:
    configuration = Config(BACKEND_ROOT / "alembic.ini")
    scripts = ScriptDirectory.from_config(configuration)

    assert scripts.get_heads() == ["20260731_0001"]


def test_stage2_baseline_has_no_domain_metadata() -> None:
    assert Base.metadata.tables == {}

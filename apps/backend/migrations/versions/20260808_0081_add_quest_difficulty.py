"""Add the quest difficulty vocabulary.

Revision ID: 20260808_0081
Revises: 20260808_0080
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260808_0081"
down_revision: str | Sequence[str] | None = "20260808_0080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("difficulty", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_quests_difficulty",
        "quests",
        "difficulty IS NULL OR difficulty IN ('easy', 'medium', 'hard')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_quests_difficulty", "quests", type_="check")
    op.drop_column("quests", "difficulty")

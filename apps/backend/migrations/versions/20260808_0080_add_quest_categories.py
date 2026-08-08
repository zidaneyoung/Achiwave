"""Add the optional quest category vocabulary.

Revision ID: 20260808_0080
Revises: 20260731_0079
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260808_0080"
down_revision: str | Sequence[str] | None = "20260731_0079"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("category", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_quests_category",
        "quests",
        "category IS NULL OR category IN "
        "('personal', 'health', 'learning', 'work', 'finance')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_quests_category", "quests", type_="check")
    op.drop_column("quests", "category")

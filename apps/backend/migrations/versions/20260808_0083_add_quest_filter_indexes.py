"""Add owner-scoped quest filter indexes.

Revision ID: 20260808_0083
Revises: 20260808_0082
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260808_0083"
down_revision: str | Sequence[str] | None = "20260808_0082"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_quests_user_state_category",
        "quests",
        ["user_id", "definition_state", "category"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_quests_user_due_at",
        "quests",
        ["user_id", "due_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL AND due_at IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_quests_user_due_at", table_name="quests")
    op.drop_index("ix_quests_user_state_category", table_name="quests")

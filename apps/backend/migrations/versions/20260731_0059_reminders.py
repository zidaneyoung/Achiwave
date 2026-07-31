"""Create timezone-aware reminder definitions.

Revision ID: 20260731_0059
Revises: 20260731_0058
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0059"
down_revision: str | Sequence[str] | None = "20260731_0058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_quests_id_user", "quests", ["id", "user_id"])
    op.create_unique_constraint("uq_quest_occurrences_id_user_quest", "quest_occurrences", ["id", "user_id", "quest_id"])
    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reminder_type", sa.Text(), nullable=False),
        sa.Column("scheduled_local_time", sa.Time(), nullable=False),
        sa.Column("timezone_name", sa.Text(), nullable=False),
        sa.Column("timezone_preference_version", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("reminder_type IN ('scheduled_local_time', 'before_occurrence', 'before_due')", name="ck_reminders_type"),
        sa.CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*$'",
            name="ck_reminders_timezone_shape",
        ),
        sa.CheckConstraint("timezone_preference_version >= 1", name="ck_reminders_timezone_version_positive"),
        sa.CheckConstraint(
            "(enabled = true AND disabled_at IS NULL AND deleted_at IS NULL) OR "
            "(enabled = false AND (disabled_at IS NOT NULL OR deleted_at IS NOT NULL))",
            name="ck_reminders_enabled_timestamps",
        ),
        sa.CheckConstraint("deleted_at IS NULL OR disabled_at IS NULL OR deleted_at >= disabled_at", name="ck_reminders_deleted_after_disabled"),
        sa.CheckConstraint("record_version >= 1", name="ck_reminders_record_version_positive"),
        sa.ForeignKeyConstraint(["quest_id", "user_id"], ["quests.id", "quests.user_id"], name="fk_reminders_quest_user", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["occurrence_id", "user_id", "quest_id"], ["quest_occurrences.id", "quest_occurrences.user_id", "quest_occurrences.quest_id"], name="fk_reminders_occurrence_user_quest", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_reminders"),
    )
    op.create_index("uq_reminders_occurrence_type", "reminders", ["occurrence_id", "reminder_type"], unique=True, postgresql_where=sa.text("occurrence_id IS NOT NULL AND deleted_at IS NULL"))
    op.create_index("uq_reminders_definition_schedule", "reminders", ["user_id", "quest_id", "reminder_type", "scheduled_local_time", "timezone_name"], unique=True, postgresql_where=sa.text("occurrence_id IS NULL AND deleted_at IS NULL"))
    op.create_index("ix_reminders_due", "reminders", ["next_due_at"], unique=False, postgresql_where=sa.text("enabled = true AND deleted_at IS NULL"))
    op.create_index("ix_reminders_user_enabled", "reminders", ["user_id", "enabled", "updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reminders_user_enabled", table_name="reminders")
    op.drop_index("ix_reminders_due", table_name="reminders")
    op.drop_index("uq_reminders_definition_schedule", table_name="reminders")
    op.drop_index("uq_reminders_occurrence_type", table_name="reminders")
    op.drop_table("reminders")
    op.drop_constraint("uq_quest_occurrences_id_user_quest", "quest_occurrences", type_="unique")
    op.drop_constraint("uq_quests_id_user", "quests", type_="unique")

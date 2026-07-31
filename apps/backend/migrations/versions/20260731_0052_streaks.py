"""Create reconstructable user-global streak data.

Revision ID: 20260731_0052
Revises: 20260731_0051
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0052"
down_revision: str | Sequence[str] | None = "20260731_0051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_quest_completions_id_user_effective_date",
        "quest_completions",
        ["id", "user_id", "completion_effective_date"],
    )
    op.create_table(
        "streaks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_streak_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_qualifying_local_date", sa.Date(), nullable=True),
        sa.Column(
            "calculated_through_event_sequence", sa.BigInteger(), server_default="0", nullable=False
        ),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.CheckConstraint("current_streak_days >= 0", name="ck_streaks_current_nonnegative"),
        sa.CheckConstraint(
            "longest_streak_days >= current_streak_days", name="ck_streaks_longest_at_least_current"
        ),
        sa.CheckConstraint(
            "(current_streak_days = 0 AND last_qualifying_local_date IS NULL) OR "
            "(current_streak_days > 0 AND last_qualifying_local_date IS NOT NULL)",
            name="ck_streaks_last_date_matches_current",
        ),
        sa.CheckConstraint(
            "calculated_through_event_sequence >= 0", name="ck_streaks_calculated_sequence_nonnegative"
        ),
        sa.CheckConstraint("record_version >= 1", name="ck_streaks_record_version_positive"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_streaks_user_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_streaks"),
    )
    op.create_table(
        "streak_days",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effective_local_date", sa.Date(), nullable=False),
        sa.Column("timezone_name", sa.Text(), nullable=False),
        sa.Column("timezone_preference_version", sa.Integer(), nullable=False),
        sa.Column("credit_state", sa.Text(), server_default="credited", nullable=False),
        sa.Column("active_source_count", sa.Integer(), nullable=False),
        sa.Column(
            "credited_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_streak_days_timezone_shape",
        ),
        sa.CheckConstraint(
            "timezone_preference_version >= 1", name="ck_streak_days_timezone_version_positive"
        ),
        sa.CheckConstraint(
            "credit_state IN ('credited', 'removed')", name="ck_streak_days_credit_state"
        ),
        sa.CheckConstraint(
            "active_source_count >= 0", name="ck_streak_days_source_count_nonnegative"
        ),
        sa.CheckConstraint(
            "(credit_state = 'credited' AND active_source_count >= 1 AND removed_at IS NULL) OR "
            "(credit_state = 'removed' AND active_source_count = 0 "
            "AND removed_at IS NOT NULL AND removed_at >= credited_at)",
            name="ck_streak_days_state_source_count",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_streak_days_user_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_streak_days"),
        sa.UniqueConstraint("user_id", "effective_local_date", name="uq_streak_days_user_date"),
        sa.UniqueConstraint(
            "id", "user_id", "effective_local_date", name="uq_streak_days_id_user_date"
        ),
    )
    op.create_index(
        "ix_streak_days_user_date_range",
        "streak_days",
        ["user_id", "effective_local_date"],
        unique=False,
    )
    op.create_table(
        "streak_day_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("streak_day_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reversal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("effective_local_date", sa.Date(), nullable=False),
        sa.Column("source_state", sa.Text(), server_default="active", nullable=False),
        sa.Column(
            "contributed_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.CheckConstraint(
            "source_state IN ('active', 'reversed')", name="ck_streak_day_sources_source_state"
        ),
        sa.CheckConstraint(
            "(source_state = 'active' AND reversal_id IS NULL AND reversed_at IS NULL) OR "
            "(source_state = 'reversed' AND reversal_id IS NOT NULL "
            "AND reversed_at IS NOT NULL AND reversed_at >= contributed_at)",
            name="ck_streak_day_sources_state_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["streak_day_id", "user_id", "effective_local_date"],
            ["streak_days.id", "streak_days.user_id", "streak_days.effective_local_date"],
            name="fk_streak_day_sources_day_user_date",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["completion_id", "user_id", "effective_local_date"],
            [
                "quest_completions.id",
                "quest_completions.user_id",
                "quest_completions.completion_effective_date",
            ],
            name="fk_streak_day_sources_completion_user_date",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reversal_id", "user_id"],
            ["quest_completion_reversals.id", "quest_completion_reversals.user_id"],
            name="fk_streak_day_sources_reversal_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_streak_day_sources"),
        sa.UniqueConstraint("completion_id", name="uq_streak_day_sources_completion"),
    )
    op.create_index(
        "ix_streak_day_sources_day_state",
        "streak_day_sources",
        ["streak_day_id", "source_state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_streak_day_sources_day_state", table_name="streak_day_sources")
    op.drop_table("streak_day_sources")
    op.drop_index("ix_streak_days_user_date_range", table_name="streak_days")
    op.drop_table("streak_days")
    op.drop_table("streaks")
    op.drop_constraint(
        "uq_quest_completions_id_user_effective_date",
        "quest_completions",
        type_="unique",
    )

"""Create backend-derived achievement progress.

Revision ID: 20260731_0055
Revises: 20260731_0054
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0055"
down_revision: str | Sequence[str] | None = "20260731_0054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "achievement_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("achievement_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("progress_model", sa.Text(), nullable=False),
        sa.Column("current_value", sa.BigInteger(), nullable=True),
        sa.Column("progress_state", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("satisfaction_state", sa.Text(), server_default="unsatisfied", nullable=False),
        sa.Column("satisfied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_progress_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_event_sequence", sa.BigInteger(), nullable=True),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("current_value IS NULL OR current_value >= 0", name="ck_achievement_progress_current_value_nonnegative"),
        sa.CheckConstraint("jsonb_typeof(progress_state) = 'object'", name="ck_achievement_progress_state_object"),
        sa.CheckConstraint("satisfaction_state IN ('unsatisfied', 'satisfied')", name="ck_achievement_progress_satisfaction_state"),
        sa.CheckConstraint(
            "(satisfaction_state = 'unsatisfied' AND satisfied_at IS NULL) OR "
            "(satisfaction_state = 'satisfied' AND satisfied_at IS NOT NULL)",
            name="ck_achievement_progress_satisfaction_timestamp",
        ),
        sa.CheckConstraint(
            "(last_progress_event_id IS NULL AND last_event_sequence IS NULL) OR "
            "(last_progress_event_id IS NOT NULL AND last_event_sequence IS NOT NULL)",
            name="ck_achievement_progress_last_event_pair",
        ),
        sa.CheckConstraint("record_version >= 1", name="ck_achievement_progress_record_version_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_achievement_progress_user_id_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["achievement_definition_id", "rule_version", "progress_model"],
            ["achievement_rules.achievement_definition_id", "achievement_rules.rule_version", "achievement_rules.rule_model"],
            name="fk_achievement_progress_rule_version_model",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["last_progress_event_id", "user_id", "last_event_sequence"],
            ["progress_events.id", "progress_events.user_id", "progress_events.event_sequence"],
            name="fk_achievement_progress_last_event_user_sequence",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_achievement_progress"),
        sa.UniqueConstraint(
            "user_id",
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_progress_user_definition_version",
        ),
        sa.UniqueConstraint(
            "id",
            "user_id",
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_progress_id_user_definition_version",
        ),
    )
    op.create_index(
        "ix_achievement_progress_user_satisfaction",
        "achievement_progress",
        ["user_id", "satisfaction_state", "updated_at"],
        unique=False,
    )
    op.create_index(
        "ix_achievement_progress_definition_satisfaction",
        "achievement_progress",
        ["achievement_definition_id", "rule_version", "satisfaction_state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_achievement_progress_definition_satisfaction", table_name="achievement_progress")
    op.drop_index("ix_achievement_progress_user_satisfaction", table_name="achievement_progress")
    op.drop_table("achievement_progress")

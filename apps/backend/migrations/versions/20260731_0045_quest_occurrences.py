"""Create quest occurrence snapshots.

Revision ID: 20260731_0045
Revises: 20260731_0044
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0045"
down_revision: str | Sequence[str] | None = "20260731_0044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quest_occurrences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quest_type", sa.Text(), nullable=False),
        sa.Column("occurrence_state", sa.Text(), nullable=False),
        sa.Column("occurrence_local_date", sa.Date(), nullable=False),
        sa.Column("scheduled_local_time", sa.Time(timezone=False), nullable=True),
        sa.Column("timezone_name", sa.Text(), nullable=False),
        sa.Column("timezone_data_version", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("eligibility_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reward_xp", sa.Integer(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "occurrence_state IN "
            "('scheduled', 'available', 'completed', 'reversed', 'expired', 'voided')",
            name="ck_quest_occurrences_occurrence_state",
        ),
        sa.CheckConstraint(
            "quest_type IN ('one_time', 'recurring')",
            name="ck_quest_occurrences_quest_type",
        ),
        sa.CheckConstraint(
            "quest_type <> 'recurring' OR scheduled_local_time IS NOT NULL",
            name="ck_quest_occurrences_recurring_scheduled_time",
        ),
        sa.CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_quest_occurrences_timezone_shape",
        ),
        sa.CheckConstraint(
            "timezone_data_version = btrim(timezone_data_version) "
            "AND timezone_data_version <> ''",
            name="ck_quest_occurrences_timezone_data_version_nonblank",
        ),
        sa.CheckConstraint(
            "rule_version >= 1",
            name="ck_quest_occurrences_rule_version_positive",
        ),
        sa.CheckConstraint(
            "reward_xp >= 0",
            name="ck_quest_occurrences_reward_xp_nonnegative",
        ),
        sa.CheckConstraint(
            "record_version >= 1",
            name="ck_quest_occurrences_record_version_positive",
        ),
        sa.CheckConstraint(
            "eligibility_expires_at IS NULL OR eligibility_expires_at > available_at",
            name="ck_quest_occurrences_expiration_after_availability",
        ),
        sa.CheckConstraint(
            "(occurrence_state = 'completed' AND completed_at IS NOT NULL) "
            "OR (occurrence_state = 'reversed' AND reversed_at IS NOT NULL) "
            "OR (occurrence_state = 'expired' AND expired_at IS NOT NULL) "
            "OR (occurrence_state = 'voided' AND voided_at IS NOT NULL) "
            "OR occurrence_state IN ('scheduled', 'available')",
            name="ck_quest_occurrences_state_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["quest_id", "user_id", "campaign_id", "quest_type"],
            ["quests.id", "quests.user_id", "quests.campaign_id", "quests.quest_type"],
            name="fk_quest_occurrences_quest_owner_type",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quest_occurrences"),
        sa.UniqueConstraint(
            "id", "user_id", name="uq_quest_occurrences_id_user_id"
        ),
    )
    op.create_index(
        "uq_quest_occurrences_recurring_local_date",
        "quest_occurrences",
        ["quest_id", "occurrence_local_date"],
        unique=True,
        postgresql_where=sa.text("quest_type = 'recurring'"),
    )
    op.create_index(
        "uq_quest_occurrences_one_time_quest",
        "quest_occurrences",
        ["quest_id"],
        unique=True,
        postgresql_where=sa.text("quest_type = 'one_time'"),
    )
    op.create_index(
        "ix_quest_occurrences_scheduled_available_at",
        "quest_occurrences",
        ["available_at"],
        unique=False,
        postgresql_where=sa.text("occurrence_state = 'scheduled'"),
    )
    op.create_index(
        "ix_quest_occurrences_available_expiration",
        "quest_occurrences",
        ["eligibility_expires_at"],
        unique=False,
        postgresql_where=sa.text(
            "occurrence_state = 'available' AND eligibility_expires_at IS NOT NULL"
        ),
    )
    op.create_index(
        "ix_quest_occurrences_user_local_date",
        "quest_occurrences",
        ["user_id", "occurrence_local_date"],
        unique=False,
    )
    op.create_index(
        "ix_quest_occurrences_quest_history",
        "quest_occurrences",
        ["quest_id", "occurrence_local_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_quest_occurrences_quest_history", table_name="quest_occurrences")
    op.drop_index(
        "ix_quest_occurrences_user_local_date", table_name="quest_occurrences"
    )
    op.drop_index(
        "ix_quest_occurrences_available_expiration", table_name="quest_occurrences"
    )
    op.drop_index(
        "ix_quest_occurrences_scheduled_available_at", table_name="quest_occurrences"
    )
    op.drop_index(
        "uq_quest_occurrences_one_time_quest", table_name="quest_occurrences"
    )
    op.drop_index(
        "uq_quest_occurrences_recurring_local_date", table_name="quest_occurrences"
    )
    op.drop_table("quest_occurrences")

"""Create quest recurrence definitions.

Revision ID: 20260731_0044
Revises: 20260731_0043
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0044"
down_revision: str | Sequence[str] | None = "20260731_0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quest_recurrences",
        sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quest_type", sa.Text(), nullable=False),
        sa.Column("frequency", sa.Text(), nullable=False),
        sa.Column("weekly_days", postgresql.ARRAY(sa.SmallInteger()), nullable=True),
        sa.Column("monthly_day", sa.SmallInteger(), nullable=True),
        sa.Column("start_local_date", sa.Date(), nullable=False),
        sa.Column("end_local_date", sa.Date(), nullable=True),
        sa.Column("max_occurrences", sa.Integer(), nullable=True),
        sa.Column("scheduled_local_time", sa.Time(timezone=False), nullable=False),
        sa.Column("timezone_name", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Integer(), server_default="1", nullable=False),
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
            "quest_type = 'recurring'",
            name="ck_quest_recurrences_recurring_quest_type",
        ),
        sa.CheckConstraint(
            "frequency IN ('daily', 'weekly', 'monthly')",
            name="ck_quest_recurrences_frequency",
        ),
        sa.CheckConstraint(
            "(frequency = 'daily' AND weekly_days IS NULL AND monthly_day IS NULL) "
            "OR (frequency = 'weekly' AND weekly_days IS NOT NULL "
            "AND cardinality(weekly_days) >= 1 "
            "AND weekly_days <@ ARRAY[1,2,3,4,5,6,7]::smallint[] "
            "AND monthly_day IS NULL) "
            "OR (frequency = 'monthly' AND weekly_days IS NULL "
            "AND monthly_day BETWEEN 1 AND 31)",
            name="ck_quest_recurrences_frequency_fields",
        ),
        sa.CheckConstraint(
            "end_local_date IS NULL OR max_occurrences IS NULL",
            name="ck_quest_recurrences_single_end_condition",
        ),
        sa.CheckConstraint(
            "end_local_date IS NULL OR end_local_date >= start_local_date",
            name="ck_quest_recurrences_end_not_before_start",
        ),
        sa.CheckConstraint(
            "max_occurrences IS NULL OR max_occurrences >= 1",
            name="ck_quest_recurrences_max_occurrences_positive",
        ),
        sa.CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_quest_recurrences_timezone_shape",
        ),
        sa.CheckConstraint(
            "rule_version >= 1",
            name="ck_quest_recurrences_rule_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["quest_id", "user_id", "campaign_id", "quest_type"],
            ["quests.id", "quests.user_id", "quests.campaign_id", "quests.quest_type"],
            name="fk_quest_recurrences_quest_owner_type",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("quest_id", name="pk_quest_recurrences"),
    )
    op.create_index(
        "ix_quest_recurrences_user_timezone_start",
        "quest_recurrences",
        ["user_id", "timezone_name", "start_local_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_quest_recurrences_user_timezone_start", table_name="quest_recurrences"
    )
    op.drop_table("quest_recurrences")

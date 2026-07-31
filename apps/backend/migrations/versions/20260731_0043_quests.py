"""Create quest definitions.

Revision ID: 20260731_0043
Revises: 20260731_0042
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0043"
down_revision: str | Sequence[str] | None = "20260731_0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quest_type", sa.Text(), nullable=False),
        sa.Column("definition_state", sa.Text(), server_default="active", nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reward_xp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("available_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("one_time_timezone_name", sa.Text(), nullable=True),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("restored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
            "quest_type IN ('one_time', 'recurring')",
            name="ck_quests_quest_type",
        ),
        sa.CheckConstraint(
            "definition_state IN ('active', 'archived')",
            name="ck_quests_definition_state",
        ),
        sa.CheckConstraint(
            "title = btrim(title) AND title <> ''",
            name="ck_quests_title_nonblank",
        ),
        sa.CheckConstraint(
            "reward_xp >= 0", name="ck_quests_reward_xp_nonnegative"
        ),
        sa.CheckConstraint(
            "display_order >= 0", name="ck_quests_display_order_nonnegative"
        ),
        sa.CheckConstraint(
            "record_version >= 1", name="ck_quests_record_version_positive"
        ),
        sa.CheckConstraint(
            "due_at IS NULL OR available_from IS NULL OR due_at >= available_from",
            name="ck_quests_due_not_before_availability",
        ),
        sa.CheckConstraint(
            "one_time_timezone_name IS NULL OR one_time_timezone_name = 'UTC' "
            "OR one_time_timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_quests_one_time_timezone_shape",
        ),
        sa.CheckConstraint(
            "quest_type = 'one_time' OR (available_from IS NULL AND due_at IS NULL "
            "AND one_time_timezone_name IS NULL)",
            name="ck_quests_recurring_excludes_one_time_schedule",
        ),
        sa.CheckConstraint(
            "definition_state <> 'archived' OR archived_at IS NOT NULL",
            name="ck_quests_archived_timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id", "user_id"],
            ["campaigns.id", "campaigns.user_id"],
            name="fk_quests_campaign_user_campaigns",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quests"),
        sa.UniqueConstraint(
            "id",
            "user_id",
            "campaign_id",
            "quest_type",
            name="uq_quests_id_user_campaign_type",
        ),
    )
    op.create_index(
        "ix_quests_user_campaign_state_order",
        "quests",
        ["user_id", "campaign_id", "definition_state", "display_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_quests_user_campaign_state_order", table_name="quests")
    op.drop_table("quests")

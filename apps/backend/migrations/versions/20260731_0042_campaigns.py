"""Create campaigns.

Revision ID: 20260731_0042
Revises: 20260731_0041
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0042"
down_revision: str | Sequence[str] | None = "20260731_0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("campaign_state", sa.Text(), server_default="active", nullable=False),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("completion_reason", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
            "title = btrim(title) AND title <> ''",
            name="ck_campaigns_title_nonblank",
        ),
        sa.CheckConstraint(
            "display_order >= 0",
            name="ck_campaigns_display_order_nonnegative",
        ),
        sa.CheckConstraint(
            "campaign_state IN ('active', 'completed', 'archived')",
            name="ck_campaigns_campaign_state",
        ),
        sa.CheckConstraint(
            "record_version >= 1",
            name="ck_campaigns_record_version_positive",
        ),
        sa.CheckConstraint(
            "campaign_state <> 'completed' OR completed_at IS NOT NULL",
            name="ck_campaigns_completed_timestamp",
        ),
        sa.CheckConstraint(
            "campaign_state <> 'archived' OR archived_at IS NOT NULL",
            name="ck_campaigns_archived_timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_campaigns_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_campaigns"),
        sa.UniqueConstraint("id", "user_id", name="uq_campaigns_id_user_id"),
    )
    op.create_index(
        "ix_campaigns_user_active_order",
        "campaigns",
        ["user_id", "display_order", "id"],
        unique=False,
        postgresql_where=sa.text("campaign_state = 'active' AND deleted_at IS NULL"),
    )
    op.create_index(
        "ix_campaigns_user_archived_at",
        "campaigns",
        ["user_id", "archived_at"],
        unique=False,
        postgresql_where=sa.text("campaign_state = 'archived'"),
    )


def downgrade() -> None:
    op.drop_index("ix_campaigns_user_archived_at", table_name="campaigns")
    op.drop_index("ix_campaigns_user_active_order", table_name="campaigns")
    op.drop_table("campaigns")

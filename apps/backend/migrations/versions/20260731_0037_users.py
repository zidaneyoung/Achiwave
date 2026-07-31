"""Create the authoritative users table.

Revision ID: 20260731_0037
Revises: 20260731_0001
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0037"
down_revision: str | Sequence[str] | None = "20260731_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_email", sa.Text(), nullable=False),
        sa.Column("display_email", sa.Text(), nullable=False),
        sa.Column("account_state", sa.Text(), server_default="active", nullable=False),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "next_event_sequence", sa.BigInteger(), server_default="1", nullable=False
        ),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
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
            "canonical_email = lower(btrim(canonical_email)) "
            "AND canonical_email <> '' "
            "AND position('@' in canonical_email) > 1",
            name="ck_users_canonical_email_normalized",
        ),
        sa.CheckConstraint(
            "display_email = btrim(display_email) AND display_email <> ''",
            name="ck_users_display_email_nonblank",
        ),
        sa.CheckConstraint(
            "account_state IN ('active', 'deactivated', 'deletion_pending')",
            name="ck_users_account_state",
        ),
        sa.CheckConstraint(
            "record_version >= 1", name="ck_users_record_version_positive"
        ),
        sa.CheckConstraint(
            "next_event_sequence >= 1",
            name="ck_users_next_event_sequence_positive",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("canonical_email", name="uq_users_canonical_email"),
    )


def downgrade() -> None:
    op.drop_table("users")

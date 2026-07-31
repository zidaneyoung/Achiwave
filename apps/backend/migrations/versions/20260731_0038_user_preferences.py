"""Create one-to-one user preferences.

Revision ID: 20260731_0038
Revises: 20260731_0037
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0038"
down_revision: str | Sequence[str] | None = "20260731_0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timezone_name", sa.Text(), server_default="UTC", nullable=False),
        sa.Column("timezone_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "timezone_effective_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "notification_preference",
            sa.Text(),
            server_default="unspecified",
            nullable=False,
        ),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
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
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_user_preferences_timezone_name_shape",
        ),
        sa.CheckConstraint(
            "timezone_version >= 1",
            name="ck_user_preferences_timezone_version_positive",
        ),
        sa.CheckConstraint(
            "notification_preference IN ('unspecified', 'enabled', 'disabled')",
            name="ck_user_preferences_notification_preference",
        ),
        sa.CheckConstraint(
            "record_version >= 1",
            name="ck_user_preferences_record_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_preferences_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_user_preferences"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")

"""Create registered devices.

Revision ID: 20260731_0039
Revises: 20260731_0038
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0039"
down_revision: str | Sequence[str] | None = "20260731_0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "registered_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("installation_id", sa.Text(), nullable=False),
        sa.Column("app_environment", sa.Text(), nullable=False),
        sa.Column("app_version", sa.Text(), nullable=True),
        sa.Column("build_version", sa.Text(), nullable=True),
        sa.Column("device_state", sa.Text(), server_default="active", nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
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
            "platform IN ('android', 'ios')",
            name="ck_registered_devices_platform",
        ),
        sa.CheckConstraint(
            "app_environment IN ('development', 'preview', 'production')",
            name="ck_registered_devices_app_environment",
        ),
        sa.CheckConstraint(
            "device_state IN ('active', 'revoked', 'removed')",
            name="ck_registered_devices_device_state",
        ),
        sa.CheckConstraint(
            "installation_id = btrim(installation_id) AND installation_id <> ''",
            name="ck_registered_devices_installation_id_nonblank",
        ),
        sa.CheckConstraint(
            "record_version >= 1",
            name="ck_registered_devices_record_version_positive",
        ),
        sa.CheckConstraint(
            "(device_state = 'active' AND revoked_at IS NULL AND removed_at IS NULL) "
            "OR (device_state = 'revoked' AND revoked_at IS NOT NULL) "
            "OR (device_state = 'removed' AND removed_at IS NOT NULL)",
            name="ck_registered_devices_state_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_registered_devices_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_registered_devices"),
        sa.UniqueConstraint(
            "id", "user_id", name="uq_registered_devices_id_user_id"
        ),
    )
    op.create_index(
        "uq_registered_devices_active_installation",
        "registered_devices",
        ["user_id", "app_environment", "installation_id"],
        unique=True,
        postgresql_where=sa.text("device_state = 'active'"),
    )
    op.create_index(
        "ix_registered_devices_user_state_last_seen",
        "registered_devices",
        ["user_id", "device_state", "last_seen_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_registered_devices_user_state_last_seen",
        table_name="registered_devices",
    )
    op.drop_index(
        "uq_registered_devices_active_installation",
        table_name="registered_devices",
    )
    op.drop_table("registered_devices")

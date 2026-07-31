"""Create device sessions.

Revision ID: 20260731_0040
Revises: 20260731_0039
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0040"
down_revision: str | Sequence[str] | None = "20260731_0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "device_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("credential_digest", sa.LargeBinary(), nullable=True),
        sa.Column("session_state", sa.Text(), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaced_by_session_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "session_state IN ('active', 'revoked', 'expired', 'replaced')",
            name="ck_device_sessions_session_state",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_device_sessions_expiration_after_creation",
        ),
        sa.CheckConstraint(
            "record_version >= 1",
            name="ck_device_sessions_record_version_positive",
        ),
        sa.CheckConstraint(
            "(session_state = 'active' AND revoked_at IS NULL "
            "AND replaced_at IS NULL AND replaced_by_session_id IS NULL) "
            "OR (session_state = 'revoked' AND revoked_at IS NOT NULL) "
            "OR session_state = 'expired' "
            "OR (session_state = 'replaced' AND replaced_at IS NOT NULL "
            "AND replaced_by_session_id IS NOT NULL)",
            name="ck_device_sessions_state_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_device_sessions_device_user_registered_devices",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_session_id", "user_id"],
            ["device_sessions.id", "device_sessions.user_id"],
            name="fk_device_sessions_replaced_by_user_device_sessions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_device_sessions"),
        sa.UniqueConstraint("id", "user_id", name="uq_device_sessions_id_user_id"),
    )
    op.create_index(
        "ix_device_sessions_user_device_state",
        "device_sessions",
        ["user_id", "device_id", "session_state"],
        unique=False,
    )
    op.create_index(
        "ix_device_sessions_active_expiration",
        "device_sessions",
        ["expires_at"],
        unique=False,
        postgresql_where=sa.text("session_state = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_device_sessions_active_expiration", table_name="device_sessions"
    )
    op.drop_index(
        "ix_device_sessions_user_device_state", table_name="device_sessions"
    )
    op.drop_table("device_sessions")

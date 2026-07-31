"""Create private push-token associations.

Revision ID: 20260731_0041
Revises: 20260731_0040
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0041"
down_revision: str | Sequence[str] | None = "20260731_0040"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_registered_devices_id_user_platform_environment",
        "registered_devices",
        ["id", "user_id", "platform", "app_environment"],
    )
    op.create_table(
        "push_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("app_environment", sa.Text(), nullable=False),
        sa.Column("token_value", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.LargeBinary(), nullable=False),
        sa.Column("token_state", sa.Text(), server_default="active", nullable=False),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaced_by_push_token_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.Column("record_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "provider IN ('expo', 'fcm', 'apns')",
            name="ck_push_tokens_provider",
        ),
        sa.CheckConstraint(
            "platform IN ('android', 'ios')",
            name="ck_push_tokens_platform",
        ),
        sa.CheckConstraint(
            "app_environment IN ('development', 'preview', 'production')",
            name="ck_push_tokens_app_environment",
        ),
        sa.CheckConstraint(
            "token_state IN ('active', 'invalidated', 'replaced')",
            name="ck_push_tokens_token_state",
        ),
        sa.CheckConstraint(
            "token_value <> ''",
            name="ck_push_tokens_token_value_nonblank",
        ),
        sa.CheckConstraint(
            "octet_length(token_hash) >= 16",
            name="ck_push_tokens_token_hash_minimum_length",
        ),
        sa.CheckConstraint(
            "record_version >= 1",
            name="ck_push_tokens_record_version_positive",
        ),
        sa.CheckConstraint(
            "(token_state = 'active' AND invalidated_at IS NULL "
            "AND replaced_at IS NULL AND replaced_by_push_token_id IS NULL) "
            "OR (token_state = 'invalidated' AND invalidated_at IS NOT NULL) "
            "OR (token_state = 'replaced' AND replaced_at IS NOT NULL "
            "AND replaced_by_push_token_id IS NOT NULL)",
            name="ck_push_tokens_state_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["device_id", "user_id", "platform", "app_environment"],
            [
                "registered_devices.id",
                "registered_devices.user_id",
                "registered_devices.platform",
                "registered_devices.app_environment",
            ],
            name="fk_push_tokens_device_user_platform_environment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_push_token_id", "user_id", "device_id"],
            ["push_tokens.id", "push_tokens.user_id", "push_tokens.device_id"],
            name="fk_push_tokens_replaced_by_user_device_push_tokens",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_push_tokens"),
        sa.UniqueConstraint(
            "id", "user_id", "device_id", name="uq_push_tokens_id_user_device"
        ),
    )
    op.create_index(
        "uq_push_tokens_active_hash",
        "push_tokens",
        ["provider", "app_environment", "token_hash"],
        unique=True,
        postgresql_where=sa.text("token_state = 'active'"),
    )
    op.create_index(
        "uq_push_tokens_active_device_provider",
        "push_tokens",
        ["user_id", "device_id", "provider", "app_environment"],
        unique=True,
        postgresql_where=sa.text("token_state = 'active'"),
    )
    op.create_index(
        "ix_push_tokens_user_device_state",
        "push_tokens",
        ["user_id", "device_id", "token_state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_push_tokens_user_device_state", table_name="push_tokens")
    op.drop_index(
        "uq_push_tokens_active_device_provider", table_name="push_tokens"
    )
    op.drop_index("uq_push_tokens_active_hash", table_name="push_tokens")
    op.drop_table("push_tokens")
    op.drop_constraint(
        "uq_registered_devices_id_user_platform_environment",
        "registered_devices",
        type_="unique",
    )

"""Create notification delivery-attempt audit history.

Revision ID: 20260731_0058
Revises: 20260731_0057
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0058"
down_revision: str | Sequence[str] | None = "20260731_0057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_push_tokens_id_user_device_provider",
        "push_tokens",
        ["id", "user_id", "device_id", "provider"],
    )
    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("push_token_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("delivery_state", sa.Text(), server_default="pending", nullable=False),
        sa.Column("provider_receipt_id", sa.Text(), nullable=True),
        sa.Column("safe_failure_class", sa.Text(), nullable=True),
        sa.Column("outbox_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("worker_task_reference", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("token_invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("channel = 'push'", name="ck_notification_deliveries_channel"),
        sa.CheckConstraint("provider IN ('expo', 'fcm', 'apns')", name="ck_notification_deliveries_provider"),
        sa.CheckConstraint("attempt_number >= 1", name="ck_notification_deliveries_attempt_number_positive"),
        sa.CheckConstraint(
            "delivery_state IN ('pending', 'attempting', 'accepted', 'delivered', "
            "'failed', 'invalid_token', 'cancelled')",
            name="ck_notification_deliveries_state",
        ),
        sa.CheckConstraint(
            "(delivery_state = 'pending' AND attempted_at IS NULL) OR "
            "(delivery_state = 'attempting' AND attempted_at IS NOT NULL) OR "
            "(delivery_state = 'accepted' AND attempted_at IS NOT NULL AND accepted_at IS NOT NULL AND accepted_at >= attempted_at) OR "
            "(delivery_state = 'delivered' AND attempted_at IS NOT NULL AND accepted_at IS NOT NULL AND delivered_at IS NOT NULL AND accepted_at >= attempted_at AND delivered_at >= accepted_at) OR "
            "(delivery_state = 'failed' AND attempted_at IS NOT NULL AND failed_at IS NOT NULL AND failed_at >= attempted_at AND safe_failure_class IS NOT NULL) OR "
            "(delivery_state = 'invalid_token' AND attempted_at IS NOT NULL AND failed_at IS NOT NULL AND token_invalidated_at IS NOT NULL AND failed_at >= attempted_at AND token_invalidated_at >= failed_at AND safe_failure_class IS NOT NULL) OR "
            "delivery_state = 'cancelled'",
            name="ck_notification_deliveries_state_timestamps",
        ),
        sa.ForeignKeyConstraint(["notification_id", "user_id"], ["notifications.id", "notifications.user_id"], name="fk_notification_deliveries_notification_user", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["device_id", "user_id"], ["registered_devices.id", "registered_devices.user_id"], name="fk_notification_deliveries_device_user", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["push_token_id", "user_id", "device_id", "provider"],
            ["push_tokens.id", "push_tokens.user_id", "push_tokens.device_id", "push_tokens.provider"],
            name="fk_notification_deliveries_token_user_device_provider",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notification_deliveries"),
        sa.UniqueConstraint("notification_id", "device_id", "channel", "attempt_number", name="uq_notification_deliveries_notification_device_channel_attempt"),
    )
    op.create_index("uq_notification_deliveries_provider_receipt", "notification_deliveries", ["provider", "provider_receipt_id"], unique=True, postgresql_where=sa.text("provider_receipt_id IS NOT NULL"))
    op.create_index("ix_notification_deliveries_notification_attempt", "notification_deliveries", ["notification_id", "attempt_number"], unique=False)
    op.create_index("ix_notification_deliveries_user_state", "notification_deliveries", ["user_id", "delivery_state", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_user_state", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_notification_attempt", table_name="notification_deliveries")
    op.drop_index("uq_notification_deliveries_provider_receipt", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    op.drop_constraint("uq_push_tokens_id_user_device_provider", "push_tokens", type_="unique")

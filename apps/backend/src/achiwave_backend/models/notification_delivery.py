from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class NotificationDelivery(Base):
    """Append-only notification delivery-attempt audit record."""

    __tablename__ = "notification_deliveries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["outbox_event_id", "user_id"],
            ["outbox_events.id", "outbox_events.user_id"],
            name="fk_notification_deliveries_outbox_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["notification_id", "user_id"],
            ["notifications.id", "notifications.user_id"],
            name="fk_notification_deliveries_notification_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_notification_deliveries_device_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["push_token_id", "user_id", "device_id", "provider"],
            [
                "push_tokens.id",
                "push_tokens.user_id",
                "push_tokens.device_id",
                "push_tokens.provider",
            ],
            name="fk_notification_deliveries_token_user_device_provider",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "notification_id",
            "device_id",
            "channel",
            "attempt_number",
            name="uq_notification_deliveries_notification_device_channel_attempt",
        ),
        CheckConstraint("channel = 'push'", name="ck_notification_deliveries_channel"),
        CheckConstraint(
            "provider IN ('expo', 'fcm', 'apns')",
            name="ck_notification_deliveries_provider",
        ),
        CheckConstraint(
            "attempt_number >= 1",
            name="ck_notification_deliveries_attempt_number_positive",
        ),
        CheckConstraint(
            "provider_receipt_id IS NULL OR "
            "(provider_receipt_id = btrim(provider_receipt_id) "
            "AND provider_receipt_id <> '')",
            name="ck_notification_deliveries_receipt_nonblank",
        ),
        CheckConstraint(
            "safe_failure_class IS NULL OR "
            "(safe_failure_class = btrim(safe_failure_class) "
            "AND safe_failure_class <> '')",
            name="ck_notification_deliveries_failure_class_nonblank",
        ),
        CheckConstraint(
            "delivery_state IN ('pending', 'attempting', 'accepted', 'delivered', "
            "'failed', 'invalid_token', 'cancelled')",
            name="ck_notification_deliveries_state",
        ),
        CheckConstraint(
            "(delivery_state = 'pending' AND attempted_at IS NULL) OR "
            "(delivery_state = 'attempting' AND attempted_at IS NOT NULL) OR "
            "(delivery_state = 'accepted' AND attempted_at IS NOT NULL "
            "AND accepted_at IS NOT NULL AND accepted_at >= attempted_at) OR "
            "(delivery_state = 'delivered' AND attempted_at IS NOT NULL "
            "AND accepted_at IS NOT NULL AND delivered_at IS NOT NULL "
            "AND accepted_at >= attempted_at AND delivered_at >= accepted_at) OR "
            "(delivery_state = 'failed' AND attempted_at IS NOT NULL "
            "AND failed_at IS NOT NULL AND failed_at >= attempted_at "
            "AND safe_failure_class IS NOT NULL) OR "
            "(delivery_state = 'invalid_token' AND attempted_at IS NOT NULL "
            "AND failed_at IS NOT NULL AND token_invalidated_at IS NOT NULL "
            "AND failed_at >= attempted_at "
            "AND token_invalidated_at >= failed_at AND safe_failure_class IS NOT NULL) OR "
            "delivery_state = 'cancelled'",
            name="ck_notification_deliveries_state_timestamps",
        ),
        Index(
            "uq_notification_deliveries_provider_receipt",
            "provider",
            "provider_receipt_id",
            unique=True,
            postgresql_where=text("provider_receipt_id IS NOT NULL"),
        ),
        Index(
            "ix_notification_deliveries_notification_attempt",
            "notification_id",
            "attempt_number",
        ),
        Index(
            "ix_notification_deliveries_user_state",
            "user_id",
            "delivery_state",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    notification_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    device_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    push_token_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    delivery_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    provider_receipt_id: Mapped[str | None] = mapped_column(Text)
    safe_failure_class: Mapped[str | None] = mapped_column(Text)
    outbox_event_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    worker_task_reference: Mapped[str | None] = mapped_column(Text)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    token_invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

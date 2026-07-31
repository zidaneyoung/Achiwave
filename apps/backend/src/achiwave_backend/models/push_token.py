from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    LargeBinary,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class PushToken(Base):
    """Private push association; token values must never enter logs or public APIs."""

    __tablename__ = "push_tokens"
    __table_args__ = (
        ForeignKeyConstraint(
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
        ForeignKeyConstraint(
            ["replaced_by_push_token_id", "user_id", "device_id"],
            ["push_tokens.id", "push_tokens.user_id", "push_tokens.device_id"],
            name="fk_push_tokens_replaced_by_user_device_push_tokens",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id", "user_id", "device_id", name="uq_push_tokens_id_user_device"
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "device_id",
            "provider",
            name="uq_push_tokens_id_user_device_provider",
        ),
        CheckConstraint(
            "provider IN ('expo', 'fcm', 'apns')",
            name="ck_push_tokens_provider",
        ),
        CheckConstraint(
            "platform IN ('android', 'ios')",
            name="ck_push_tokens_platform",
        ),
        CheckConstraint(
            "app_environment IN ('development', 'preview', 'production')",
            name="ck_push_tokens_app_environment",
        ),
        CheckConstraint(
            "token_state IN ('active', 'invalidated', 'replaced')",
            name="ck_push_tokens_token_state",
        ),
        CheckConstraint(
            "token_value <> ''",
            name="ck_push_tokens_token_value_nonblank",
        ),
        CheckConstraint(
            "octet_length(token_hash) >= 16",
            name="ck_push_tokens_token_hash_minimum_length",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_push_tokens_record_version_positive",
        ),
        CheckConstraint(
            "(token_state = 'active' AND invalidated_at IS NULL "
            "AND replaced_at IS NULL AND replaced_by_push_token_id IS NULL) "
            "OR (token_state = 'invalidated' AND invalidated_at IS NOT NULL) "
            "OR (token_state = 'replaced' AND replaced_at IS NOT NULL "
            "AND replaced_by_push_token_id IS NOT NULL)",
            name="ck_push_tokens_state_timestamps",
        ),
        Index(
            "uq_push_tokens_active_hash",
            "provider",
            "app_environment",
            "token_hash",
            unique=True,
            postgresql_where=text("token_state = 'active'"),
        ),
        Index(
            "uq_push_tokens_active_device_provider",
            "user_id",
            "device_id",
            "provider",
            "app_environment",
            unique=True,
            postgresql_where=text("token_state = 'active'"),
        ),
        Index(
            "ix_push_tokens_user_device_state",
            "user_id",
            "device_id",
            "token_state",
        ),
        Index(
            "ix_push_tokens_replaced_by",
            "replaced_by_push_token_id",
            "user_id",
            "device_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    device_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    app_environment: Mapped[str] = mapped_column(Text, nullable=False)
    token_value: Mapped[str] = mapped_column(
        Text, nullable=False, info={"sensitive": True}
    )
    token_hash: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
        info={"sensitive": True},
    )
    token_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_push_token_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True)
    )
    invalidation_reason: Mapped[str | None] = mapped_column(Text)
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    def __repr__(self) -> str:
        return (
            f"PushToken(id={self.id!r}, user_id={self.user_id!r}, "
            f"device_id={self.device_id!r}, provider={self.provider!r}, "
            f"token_state={self.token_state!r})"
        )

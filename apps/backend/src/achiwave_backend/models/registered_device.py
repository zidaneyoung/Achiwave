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


class RegisteredDevice(Base):
    """Revocable installation registration used only as device context."""

    __tablename__ = "registered_devices"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_registered_devices_user_id_users",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "user_id", name="uq_registered_devices_id_user_id"),
        UniqueConstraint(
            "id",
            "user_id",
            "platform",
            "app_environment",
            name="uq_registered_devices_id_user_platform_environment",
        ),
        CheckConstraint(
            "platform IN ('android', 'ios')",
            name="ck_registered_devices_platform",
        ),
        CheckConstraint(
            "app_environment IN ('development', 'preview', 'production')",
            name="ck_registered_devices_app_environment",
        ),
        CheckConstraint(
            "device_state IN ('active', 'revoked', 'removed')",
            name="ck_registered_devices_device_state",
        ),
        CheckConstraint(
            "installation_id = btrim(installation_id) AND installation_id <> ''",
            name="ck_registered_devices_installation_id_nonblank",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_registered_devices_record_version_positive",
        ),
        CheckConstraint(
            "(device_state = 'active' AND revoked_at IS NULL AND removed_at IS NULL) "
            "OR (device_state = 'revoked' AND revoked_at IS NOT NULL) "
            "OR (device_state = 'removed' AND removed_at IS NOT NULL)",
            name="ck_registered_devices_state_timestamps",
        ),
        Index(
            "uq_registered_devices_active_installation",
            "user_id",
            "app_environment",
            "installation_id",
            unique=True,
            postgresql_where=text("device_state = 'active'"),
        ),
        Index(
            "ix_registered_devices_user_state_last_seen",
            "user_id",
            "device_state",
            "last_seen_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False)
    installation_id: Mapped[str] = mapped_column(Text, nullable=False)
    app_environment: Mapped[str] = mapped_column(Text, nullable=False)
    app_version: Mapped[str | None] = mapped_column(Text)
    build_version: Mapped[str | None] = mapped_column(Text)
    device_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

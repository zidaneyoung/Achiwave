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


class DeviceSession(Base):
    """Revocable session metadata without token issuance or refresh behavior."""

    __tablename__ = "device_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_device_sessions_device_user_registered_devices",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["replaced_by_session_id", "user_id"],
            ["device_sessions.id", "device_sessions.user_id"],
            name="fk_device_sessions_replaced_by_user_device_sessions",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "user_id", name="uq_device_sessions_id_user_id"),
        CheckConstraint(
            "session_state IN ('active', 'revoked', 'expired', 'replaced')",
            name="ck_device_sessions_session_state",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_device_sessions_expiration_after_creation",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_device_sessions_record_version_positive",
        ),
        CheckConstraint(
            "(session_state = 'active' AND revoked_at IS NULL "
            "AND replaced_at IS NULL AND replaced_by_session_id IS NULL) "
            "OR (session_state = 'revoked' AND revoked_at IS NOT NULL) "
            "OR session_state = 'expired' "
            "OR (session_state = 'replaced' AND replaced_at IS NOT NULL "
            "AND replaced_by_session_id IS NOT NULL)",
            name="ck_device_sessions_state_timestamps",
        ),
        Index(
            "ix_device_sessions_user_device_state",
            "user_id",
            "device_id",
            "session_state",
        ),
        Index(
            "ix_device_sessions_active_expiration",
            "expires_at",
            postgresql_where=text("session_state = 'active'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    device_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    credential_digest: Mapped[bytes | None] = mapped_column(LargeBinary)
    session_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_session_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True)
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

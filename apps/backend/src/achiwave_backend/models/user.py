from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class User(Base):
    """Authoritative account identity without authentication implementation."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("canonical_email", name="uq_users_canonical_email"),
        CheckConstraint(
            "canonical_email = lower(btrim(canonical_email)) "
            "AND canonical_email <> '' "
            "AND position('@' in canonical_email) > 1",
            name="ck_users_canonical_email_normalized",
        ),
        CheckConstraint(
            "display_email = btrim(display_email) AND display_email <> ''",
            name="ck_users_display_email_nonblank",
        ),
        CheckConstraint(
            "password_hash IS NULL OR btrim(password_hash) <> ''",
            name="ck_users_password_hash_nonblank",
        ),
        CheckConstraint(
            "account_state IN ('active', 'deactivated', 'deletion_pending')",
            name="ck_users_account_state",
        ),
        CheckConstraint("record_version >= 1", name="ck_users_record_version_positive"),
        CheckConstraint(
            "next_event_sequence >= 1",
            name="ck_users_next_event_sequence_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    canonical_email: Mapped[str] = mapped_column(Text)
    display_email: Mapped[str] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(
        Text,
        info={"sensitive": True},
    )
    account_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    next_event_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, account_state={self.account_state!r}, "
            f"record_version={self.record_version!r})"
        )

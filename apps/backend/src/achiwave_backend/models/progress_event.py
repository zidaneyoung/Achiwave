from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class ProgressEvent(Base):
    """Append-only authoritative progression event."""

    __tablename__ = "progress_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_progress_events_user_id_users",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_progress_events_user_client_mutation",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id", "user_id", "event_sequence", name="uq_progress_events_id_user_sequence"
        ),
        UniqueConstraint(
            "user_id", "event_sequence", name="uq_progress_events_user_sequence"
        ),
        UniqueConstraint(
            "user_id",
            "event_type",
            "source_type",
            "source_id",
            name="uq_progress_events_user_source_identity",
        ),
        CheckConstraint(
            "event_sequence >= 1", name="ck_progress_events_event_sequence_positive"
        ),
        CheckConstraint(
            "event_type = btrim(event_type) AND event_type <> ''",
            name="ck_progress_events_event_type_nonblank",
        ),
        CheckConstraint(
            "source_type = btrim(source_type) AND source_type <> ''",
            name="ck_progress_events_source_type_nonblank",
        ),
        CheckConstraint(
            "rule_version IS NULL OR rule_version >= 1",
            name="ck_progress_events_rule_version_positive",
        ),
        CheckConstraint(
            "server_processed_at IS NULL OR server_processed_at >= server_received_at",
            name="ck_progress_events_processing_after_receipt",
        ),
        CheckConstraint(
            "jsonb_typeof(event_metadata) = 'object'",
            name="ck_progress_events_metadata_object",
        ),
        Index(
            "ix_progress_events_user_source",
            "user_id",
            "source_type",
            "source_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    client_mutation_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    server_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_local_date: Mapped[date | None] = mapped_column(Date)
    rule_version: Mapped[int | None] = mapped_column(Integer)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

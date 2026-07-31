from datetime import datetime
from typing import Any
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
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class OutboxEvent(Base):
    """Transactional outbox state for later worker publication."""

    __tablename__ = "outbox_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_outbox_events_user_id_users",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "user_id", name="uq_outbox_events_id_user"),
        CheckConstraint(
            "aggregate_type = btrim(aggregate_type) AND aggregate_type <> ''",
            name="ck_outbox_events_aggregate_type_nonblank",
        ),
        CheckConstraint(
            "event_type = btrim(event_type) AND event_type <> ''",
            name="ck_outbox_events_event_type_nonblank",
        ),
        CheckConstraint(
            "event_schema_version >= 1",
            name="ck_outbox_events_schema_version_positive",
        ),
        CheckConstraint(
            "jsonb_typeof(event_payload) = 'object'",
            name="ck_outbox_events_payload_object",
        ),
        CheckConstraint(
            "NOT event_payload ?| ARRAY['access_token', 'refresh_token', "
            "'password_hash', 'push_token', 'achievement_rule', 'evidence_content']",
            name="ck_outbox_events_forbidden_payload_keys",
        ),
        CheckConstraint(
            "processing_state IN ('pending', 'in_flight', 'published', 'failed', 'cancelled')",
            name="ck_outbox_events_processing_state",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_outbox_events_attempt_count_nonnegative",
        ),
        CheckConstraint(
            "(attempt_count = 0 AND last_attempt_at IS NULL) OR "
            "(attempt_count >= 1 AND last_attempt_at IS NOT NULL)",
            name="ck_outbox_events_attempt_timestamp",
        ),
        CheckConstraint(
            "(locked_at IS NULL AND lease_expires_at IS NULL) OR "
            "(locked_at IS NOT NULL AND lease_expires_at IS NOT NULL "
            "AND lease_expires_at > locked_at)",
            name="ck_outbox_events_lease_pair",
        ),
        CheckConstraint(
            "processing_state <> 'in_flight' OR "
            "(locked_at IS NOT NULL AND attempt_count >= 1)",
            name="ck_outbox_events_in_flight_lease",
        ),
        CheckConstraint(
            "(processing_state = 'published' AND published_at IS NOT NULL) OR "
            "(processing_state <> 'published' AND published_at IS NULL)",
            name="ck_outbox_events_published_timestamp",
        ),
        CheckConstraint(
            "processing_state <> 'failed' OR safe_failure_class IS NOT NULL",
            name="ck_outbox_events_failed_classification",
        ),
        CheckConstraint(
            "safe_failure_class IS NULL OR "
            "(safe_failure_class = btrim(safe_failure_class) "
            "AND safe_failure_class <> '')",
            name="ck_outbox_events_failure_class_nonblank",
        ),
        CheckConstraint(
            "available_at >= created_at",
            name="ck_outbox_events_available_after_creation",
        ),
        Index(
            "ix_outbox_events_due",
            "available_at",
            "created_at",
            postgresql_where=text("processing_state IN ('pending', 'failed')"),
        ),
        Index(
            "ix_outbox_events_stale_lease",
            "lease_expires_at",
            postgresql_where=text("processing_state = 'in_flight'"),
        ),
        Index(
            "ix_outbox_events_aggregate",
            "aggregate_type",
            "aggregate_id",
            "created_at",
        ),
        Index("ix_outbox_events_user", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    aggregate_type: Mapped[str] = mapped_column(Text, nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    event_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, info={"sensitive": True}
    )
    event_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    processing_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    safe_failure_class: Mapped[str | None] = mapped_column(Text)

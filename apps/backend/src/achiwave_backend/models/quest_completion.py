from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class QuestCompletion(Base):
    """Accepted completion history; reversal marks it inactive without deleting it."""

    __tablename__ = "quest_completions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["occurrence_id", "user_id"],
            ["quest_occurrences.id", "quest_occurrences.user_id"],
            name="fk_quest_completions_occurrence_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_quest_completions_device_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_quest_completions_user_client_mutation",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id", "user_id", name="uq_quest_completions_id_user"
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "completion_effective_date",
            name="uq_quest_completions_id_user_effective_date",
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "occurrence_id",
            name="uq_quest_completions_id_user_occurrence",
        ),
        UniqueConstraint(
            "user_id",
            "event_sequence",
            name="uq_quest_completions_user_event_sequence",
        ),
        CheckConstraint(
            "event_sequence >= 1",
            name="ck_quest_completions_event_sequence_positive",
        ),
        CheckConstraint(
            "server_processed_at IS NULL OR server_processed_at >= server_received_at",
            name="ck_quest_completions_processing_after_receipt",
        ),
        CheckConstraint(
            "(device_observed_at IS NULL AND client_time_valid IS NULL) "
            "OR (device_observed_at IS NOT NULL AND client_time_valid IS NOT NULL)",
            name="ck_quest_completions_client_time_pair",
        ),
        CheckConstraint(
            "device_timezone_name IS NULL OR device_timezone_name = 'UTC' "
            "OR device_timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_quest_completions_device_timezone_shape",
        ),
        Index(
            "uq_quest_completions_active_occurrence",
            "occurrence_id",
            unique=True,
            postgresql_where=text("reversed_at IS NULL"),
        ),
        Index(
            "uq_quest_completions_user_client_mutation",
            "user_id",
            "client_mutation_id",
            unique=True,
            postgresql_where=text("client_mutation_id IS NOT NULL"),
        ),
        Index(
            "ix_quest_completions_user_effective_date",
            "user_id",
            "completion_effective_date",
        ),
        Index(
            "ix_quest_completions_occurrence_received",
            "occurrence_id",
            "server_received_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    occurrence_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    device_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    client_mutation_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True)
    )
    server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    server_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completion_effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    device_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_timezone_name: Mapped[str | None] = mapped_column(Text)
    client_time_valid: Mapped[bool | None] = mapped_column(Boolean)
    event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class QuestCompletionReversal(Base):
    """Append-only reversal event linked to one historical completion."""

    __tablename__ = "quest_completion_reversals"
    __table_args__ = (
        ForeignKeyConstraint(
            ["completion_id", "user_id", "occurrence_id"],
            [
                "quest_completions.id",
                "quest_completions.user_id",
                "quest_completions.occurrence_id",
            ],
            name="fk_quest_completion_reversals_completion_owner_occurrence",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_quest_completion_reversals_device_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_quest_completion_reversals_user_client_mutation",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id", "user_id", name="uq_quest_completion_reversals_id_user"
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "completion_id",
            name="uq_quest_completion_reversals_id_user_completion",
        ),
        UniqueConstraint(
            "completion_id",
            name="uq_quest_completion_reversals_completion_id",
        ),
        UniqueConstraint(
            "user_id",
            "event_sequence",
            name="uq_quest_completion_reversals_user_event_sequence",
        ),
        CheckConstraint(
            "reason = btrim(reason) AND reason <> ''",
            name="ck_quest_completion_reversals_reason_nonblank",
        ),
        CheckConstraint(
            "event_sequence >= 1",
            name="ck_quest_completion_reversals_event_sequence_positive",
        ),
        CheckConstraint(
            "server_processed_at IS NULL OR server_processed_at >= server_received_at",
            name="ck_quest_completion_reversals_processing_after_receipt",
        ),
        Index(
            "uq_quest_completion_reversals_user_client_mutation",
            "user_id",
            "client_mutation_id",
            unique=True,
            postgresql_where=text("client_mutation_id IS NOT NULL"),
        ),
        Index(
            "ix_quest_completion_reversals_user_received",
            "user_id",
            "server_received_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    occurrence_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    completion_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    device_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    client_mutation_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True)
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    server_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

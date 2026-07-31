from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
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


class XpLedgerEntry(Base):
    """Immutable XP award or exact compensating reversal."""

    __tablename__ = "xp_ledger_entries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_xp_ledger_entries_user_id_users",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["completion_id", "user_id"],
            ["quest_completions.id", "quest_completions.user_id"],
            name="fk_xp_ledger_entries_completion_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reversal_id", "user_id"],
            ["quest_completion_reversals.id", "quest_completion_reversals.user_id"],
            name="fk_xp_ledger_entries_reversal_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["progress_event_id", "user_id", "event_sequence"],
            ["progress_events.id", "progress_events.user_id", "progress_events.event_sequence"],
            name="fk_xp_ledger_entries_progress_event_user_sequence",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_xp_ledger_entries_user_client_mutation",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            [
                "reverses_ledger_entry_id",
                "user_id",
                "source_award_amount",
                "source_award_reason",
            ],
            [
                "xp_ledger_entries.id",
                "xp_ledger_entries.user_id",
                "xp_ledger_entries.xp_delta",
                "xp_ledger_entries.reason",
            ],
            name="fk_xp_ledger_entries_exact_source_award",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "xp_delta",
            "reason",
            name="uq_xp_ledger_entries_id_user_delta_reason",
        ),
        UniqueConstraint(
            "user_id", "event_sequence", name="uq_xp_ledger_entries_user_sequence"
        ),
        UniqueConstraint(
            "progress_event_id", name="uq_xp_ledger_entries_progress_event"
        ),
        CheckConstraint(
            "reason IN ('quest_completion', 'completion_reversal')",
            name="ck_xp_ledger_entries_reason",
        ),
        CheckConstraint(
            "event_sequence >= 1", name="ck_xp_ledger_entries_event_sequence_positive"
        ),
        CheckConstraint(
            "rule_version >= 1", name="ck_xp_ledger_entries_rule_version_positive"
        ),
        CheckConstraint(
            "source_award_amount IS NULL OR source_award_amount >= 0",
            name="ck_xp_ledger_entries_source_award_nonnegative",
        ),
        CheckConstraint(
            "(reason = 'quest_completion' AND completion_id IS NOT NULL "
            "AND reversal_id IS NULL AND reverses_ledger_entry_id IS NULL "
            "AND source_award_amount IS NULL AND source_award_reason IS NULL "
            "AND xp_delta >= 0) OR "
            "(reason = 'completion_reversal' AND completion_id IS NULL "
            "AND reversal_id IS NOT NULL AND reverses_ledger_entry_id IS NOT NULL "
            "AND source_award_amount IS NOT NULL "
            "AND source_award_reason = 'quest_completion' "
            "AND xp_delta = -source_award_amount)",
            name="ck_xp_ledger_entries_reason_source_delta",
        ),
        Index(
            "uq_xp_ledger_entries_completion_award",
            "completion_id",
            unique=True,
            postgresql_where=text("reason = 'quest_completion'"),
        ),
        Index(
            "uq_xp_ledger_entries_reversal_compensation",
            "reversal_id",
            unique=True,
            postgresql_where=text("reason = 'completion_reversal'"),
        ),
        Index(
            "uq_xp_ledger_entries_reverses_award",
            "reverses_ledger_entry_id",
            unique=True,
            postgresql_where=text("reverses_ledger_entry_id IS NOT NULL"),
        ),
        Index("ix_xp_ledger_entries_user_recorded", "user_id", "server_recorded_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    xp_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    completion_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    reversal_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    progress_event_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    client_mutation_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_award_amount: Mapped[int | None] = mapped_column(Integer)
    source_award_reason: Mapped[str | None] = mapped_column(Text)
    reverses_ledger_entry_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True)
    )
    event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    server_recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

from datetime import date, datetime, time
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class QuestOccurrence(Base):
    """Authoritative immutable schedule and reward snapshot for one quest instance."""

    __tablename__ = "quest_occurrences"
    __table_args__ = (
        ForeignKeyConstraint(
            ["quest_id", "user_id", "campaign_id", "quest_type"],
            ["quests.id", "quests.user_id", "quests.campaign_id", "quests.quest_type"],
            name="fk_quest_occurrences_quest_owner_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id", "user_id", name="uq_quest_occurrences_id_user_id"
        ),
        UniqueConstraint(
            "id", "user_id", "quest_id", name="uq_quest_occurrences_id_user_quest"
        ),
        CheckConstraint(
            "occurrence_state IN "
            "('scheduled', 'available', 'completed', 'reversed', 'expired', 'voided')",
            name="ck_quest_occurrences_occurrence_state",
        ),
        CheckConstraint(
            "quest_type IN ('one_time', 'recurring')",
            name="ck_quest_occurrences_quest_type",
        ),
        CheckConstraint(
            "quest_type <> 'recurring' OR scheduled_local_time IS NOT NULL",
            name="ck_quest_occurrences_recurring_scheduled_time",
        ),
        CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(/[A-Za-z0-9_+-]+)*$'",
            name="ck_quest_occurrences_timezone_shape",
        ),
        CheckConstraint(
            "timezone_data_version = btrim(timezone_data_version) "
            "AND timezone_data_version <> ''",
            name="ck_quest_occurrences_timezone_data_version_nonblank",
        ),
        CheckConstraint(
            "rule_version >= 1",
            name="ck_quest_occurrences_rule_version_positive",
        ),
        CheckConstraint(
            "reward_xp >= 0",
            name="ck_quest_occurrences_reward_xp_nonnegative",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_quest_occurrences_record_version_positive",
        ),
        CheckConstraint(
            "eligibility_expires_at IS NULL OR eligibility_expires_at > available_at",
            name="ck_quest_occurrences_expiration_after_availability",
        ),
        CheckConstraint(
            "(occurrence_state = 'completed' AND completed_at IS NOT NULL) "
            "OR (occurrence_state = 'reversed' AND reversed_at IS NOT NULL) "
            "OR (occurrence_state = 'expired' AND expired_at IS NOT NULL) "
            "OR (occurrence_state = 'voided' AND voided_at IS NOT NULL) "
            "OR occurrence_state IN ('scheduled', 'available')",
            name="ck_quest_occurrences_state_timestamps",
        ),
        Index(
            "uq_quest_occurrences_recurring_local_date",
            "quest_id",
            "occurrence_local_date",
            unique=True,
            postgresql_where=text("quest_type = 'recurring'"),
        ),
        Index(
            "uq_quest_occurrences_one_time_quest",
            "quest_id",
            unique=True,
            postgresql_where=text("quest_type = 'one_time'"),
        ),
        Index(
            "ix_quest_occurrences_scheduled_available_at",
            "available_at",
            postgresql_where=text("occurrence_state = 'scheduled'"),
        ),
        Index(
            "ix_quest_occurrences_available_expiration",
            "eligibility_expires_at",
            postgresql_where=text(
                "occurrence_state = 'available' AND eligibility_expires_at IS NOT NULL"
            ),
        ),
        Index(
            "ix_quest_occurrences_user_local_date",
            "user_id",
            "occurrence_local_date",
        ),
        Index(
            "ix_quest_occurrences_quest_history",
            "quest_id",
            "occurrence_local_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    quest_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    quest_type: Mapped[str] = mapped_column(Text, nullable=False)
    occurrence_state: Mapped[str] = mapped_column(Text, nullable=False)
    occurrence_local_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_local_time: Mapped[time | None] = mapped_column(Time(timezone=False))
    timezone_name: Mapped[str] = mapped_column(Text, nullable=False)
    timezone_data_version: Mapped[str] = mapped_column(Text, nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    eligibility_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

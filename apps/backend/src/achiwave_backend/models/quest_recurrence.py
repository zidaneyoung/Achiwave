from datetime import date, datetime, time
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    Text,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class QuestRecurrence(Base):
    """One MVP recurrence rule for one recurring quest definition."""

    __tablename__ = "quest_recurrences"
    __table_args__ = (
        ForeignKeyConstraint(
            ["quest_id", "user_id", "campaign_id", "quest_type"],
            ["quests.id", "quests.user_id", "quests.campaign_id", "quests.quest_type"],
            name="fk_quest_recurrences_quest_owner_type",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "quest_type = 'recurring'",
            name="ck_quest_recurrences_recurring_quest_type",
        ),
        CheckConstraint(
            "frequency IN ('daily', 'weekly', 'monthly')",
            name="ck_quest_recurrences_frequency",
        ),
        CheckConstraint(
            "(frequency = 'daily' AND weekly_days IS NULL AND monthly_day IS NULL) "
            "OR (frequency = 'weekly' AND weekly_days IS NOT NULL "
            "AND cardinality(weekly_days) >= 1 "
            "AND weekly_days <@ ARRAY[1,2,3,4,5,6,7]::smallint[] "
            "AND monthly_day IS NULL) "
            "OR (frequency = 'monthly' AND weekly_days IS NULL "
            "AND monthly_day BETWEEN 1 AND 31)",
            name="ck_quest_recurrences_frequency_fields",
        ),
        CheckConstraint(
            "end_local_date IS NULL OR max_occurrences IS NULL",
            name="ck_quest_recurrences_single_end_condition",
        ),
        CheckConstraint(
            "end_local_date IS NULL OR end_local_date >= start_local_date",
            name="ck_quest_recurrences_end_not_before_start",
        ),
        CheckConstraint(
            "max_occurrences IS NULL OR max_occurrences >= 1",
            name="ck_quest_recurrences_max_occurrences_positive",
        ),
        CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_quest_recurrences_timezone_shape",
        ),
        CheckConstraint(
            "rule_version >= 1",
            name="ck_quest_recurrences_rule_version_positive",
        ),
        Index(
            "ix_quest_recurrences_user_timezone_start",
            "user_id",
            "timezone_name",
            "start_local_date",
        ),
    )

    quest_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    quest_type: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[str] = mapped_column(Text, nullable=False)
    weekly_days: Mapped[list[int] | None] = mapped_column(ARRAY(SmallInteger))
    monthly_day: Mapped[int | None] = mapped_column(SmallInteger)
    start_local_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_local_date: Mapped[date | None] = mapped_column(Date)
    max_occurrences: Mapped[int | None] = mapped_column(Integer)
    scheduled_local_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    timezone_name: Mapped[str] = mapped_column(Text, nullable=False)
    rule_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

from datetime import date, datetime
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
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class Streak(Base):
    """Derived user-global streak summary rebuildable from credited days."""

    __tablename__ = "streaks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_streaks_user_id_users",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "current_streak_days >= 0", name="ck_streaks_current_nonnegative"
        ),
        CheckConstraint(
            "longest_streak_days >= current_streak_days",
            name="ck_streaks_longest_at_least_current",
        ),
        CheckConstraint(
            "(current_streak_days = 0 AND last_qualifying_local_date IS NULL) OR "
            "(current_streak_days > 0 AND last_qualifying_local_date IS NOT NULL)",
            name="ck_streaks_last_date_matches_current",
        ),
        CheckConstraint(
            "calculated_through_event_sequence >= 0",
            name="ck_streaks_calculated_sequence_nonnegative",
        ),
        CheckConstraint("record_version >= 1", name="ck_streaks_record_version_positive"),
    )

    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    current_streak_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    longest_streak_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    last_qualifying_local_date: Mapped[date | None] = mapped_column(Date)
    calculated_through_event_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class StreakDay(Base):
    """One authoritative user-local date credit, retained after removal."""

    __tablename__ = "streak_days"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_streak_days_user_id_users",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "user_id", "effective_local_date", name="uq_streak_days_user_date"
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "effective_local_date",
            name="uq_streak_days_id_user_date",
        ),
        CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*$'",
            name="ck_streak_days_timezone_shape",
        ),
        CheckConstraint(
            "timezone_preference_version >= 1",
            name="ck_streak_days_timezone_version_positive",
        ),
        CheckConstraint(
            "credit_state IN ('credited', 'removed')",
            name="ck_streak_days_credit_state",
        ),
        CheckConstraint(
            "active_source_count >= 0", name="ck_streak_days_source_count_nonnegative"
        ),
        CheckConstraint(
            "(credit_state = 'credited' AND active_source_count >= 1 AND removed_at IS NULL) OR "
            "(credit_state = 'removed' AND active_source_count = 0 "
            "AND removed_at IS NOT NULL AND removed_at >= credited_at)",
            name="ck_streak_days_state_source_count",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    effective_local_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone_name: Mapped[str] = mapped_column(Text, nullable=False)
    timezone_preference_version: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'credited'")
    )
    active_source_count: Mapped[int] = mapped_column(Integer, nullable=False)
    credited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class StreakDaySource(Base):
    """Completion source retained so a day can survive partial reversal."""

    __tablename__ = "streak_day_sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["streak_day_id", "user_id", "effective_local_date"],
            ["streak_days.id", "streak_days.user_id", "streak_days.effective_local_date"],
            name="fk_streak_day_sources_day_user_date",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["completion_id", "user_id", "effective_local_date"],
            [
                "quest_completions.id",
                "quest_completions.user_id",
                "quest_completions.completion_effective_date",
            ],
            name="fk_streak_day_sources_completion_user_date",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reversal_id", "user_id", "completion_id"],
            [
                "quest_completion_reversals.id",
                "quest_completion_reversals.user_id",
                "quest_completion_reversals.completion_id",
            ],
            name="fk_streak_day_sources_reversal_user",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("completion_id", name="uq_streak_day_sources_completion"),
        CheckConstraint(
            "source_state IN ('active', 'reversed')",
            name="ck_streak_day_sources_source_state",
        ),
        CheckConstraint(
            "(source_state = 'active' AND reversal_id IS NULL AND reversed_at IS NULL) OR "
            "(source_state = 'reversed' AND reversal_id IS NOT NULL "
            "AND reversed_at IS NOT NULL AND reversed_at >= contributed_at)",
            name="ck_streak_day_sources_state_timestamps",
        ),
        Index("ix_streak_day_sources_day_state", "streak_day_id", "source_state"),
        Index(
            "ix_streak_day_sources_reversal",
            "reversal_id",
            "user_id",
            "completion_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    streak_day_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    completion_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    reversal_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    effective_local_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    contributed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

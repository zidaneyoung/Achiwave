from datetime import datetime, time
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    Time,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class Reminder(Base):
    """Timezone-aware reminder definition without scheduling behavior."""

    __tablename__ = "reminders"
    __table_args__ = (
        ForeignKeyConstraint(
            ["quest_id", "user_id"],
            ["quests.id", "quests.user_id"],
            name="fk_reminders_quest_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["occurrence_id", "user_id", "quest_id"],
            ["quest_occurrences.id", "quest_occurrences.user_id", "quest_occurrences.quest_id"],
            name="fk_reminders_occurrence_user_quest",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "reminder_type IN ('scheduled_local_time', 'before_occurrence', 'before_due')",
            name="ck_reminders_type",
        ),
        CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*$'",
            name="ck_reminders_timezone_shape",
        ),
        CheckConstraint(
            "timezone_preference_version >= 1",
            name="ck_reminders_timezone_version_positive",
        ),
        CheckConstraint(
            "(enabled = true AND disabled_at IS NULL AND deleted_at IS NULL) OR "
            "(enabled = false AND (disabled_at IS NOT NULL OR deleted_at IS NOT NULL))",
            name="ck_reminders_enabled_timestamps",
        ),
        CheckConstraint(
            "deleted_at IS NULL OR disabled_at IS NULL OR deleted_at >= disabled_at",
            name="ck_reminders_deleted_after_disabled",
        ),
        CheckConstraint("record_version >= 1", name="ck_reminders_record_version_positive"),
        Index(
            "uq_reminders_occurrence_type",
            "occurrence_id",
            "reminder_type",
            unique=True,
            postgresql_where=text("occurrence_id IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index(
            "uq_reminders_definition_schedule",
            "user_id",
            "quest_id",
            "reminder_type",
            "scheduled_local_time",
            "timezone_name",
            unique=True,
            postgresql_where=text("occurrence_id IS NULL AND deleted_at IS NULL"),
        ),
        Index(
            "ix_reminders_due",
            "next_due_at",
            postgresql_where=text("enabled = true AND deleted_at IS NULL"),
        ),
        Index("ix_reminders_user_enabled", "user_id", "enabled", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    quest_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    occurrence_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    reminder_type: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_local_time: Mapped[time] = mapped_column(Time, nullable=False)
    timezone_name: Mapped[str] = mapped_column(Text, nullable=False)
    timezone_preference_version: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

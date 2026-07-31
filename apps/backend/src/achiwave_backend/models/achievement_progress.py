from datetime import datetime
from typing import Any
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
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class AchievementProgress(Base):
    """Mutable backend-derived progress for one user and rule version."""

    __tablename__ = "achievement_progress"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_achievement_progress_user_id_users",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["achievement_definition_id", "rule_version", "progress_model"],
            [
                "achievement_rules.achievement_definition_id",
                "achievement_rules.rule_version",
                "achievement_rules.rule_model",
            ],
            name="fk_achievement_progress_rule_version_model",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["last_progress_event_id", "user_id", "last_event_sequence"],
            ["progress_events.id", "progress_events.user_id", "progress_events.event_sequence"],
            name="fk_achievement_progress_last_event_user_sequence",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "user_id",
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_progress_user_definition_version",
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_progress_id_user_definition_version",
        ),
        CheckConstraint(
            "current_value IS NULL OR current_value >= 0",
            name="ck_achievement_progress_current_value_nonnegative",
        ),
        CheckConstraint(
            "jsonb_typeof(progress_state) = 'object'",
            name="ck_achievement_progress_state_object",
        ),
        CheckConstraint(
            "satisfaction_state IN ('unsatisfied', 'satisfied')",
            name="ck_achievement_progress_satisfaction_state",
        ),
        CheckConstraint(
            "(satisfaction_state = 'unsatisfied' AND satisfied_at IS NULL) OR "
            "(satisfaction_state = 'satisfied' AND satisfied_at IS NOT NULL)",
            name="ck_achievement_progress_satisfaction_timestamp",
        ),
        CheckConstraint(
            "(last_progress_event_id IS NULL AND last_event_sequence IS NULL) OR "
            "(last_progress_event_id IS NOT NULL AND last_event_sequence IS NOT NULL)",
            name="ck_achievement_progress_last_event_pair",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_achievement_progress_record_version_positive",
        ),
        Index(
            "ix_achievement_progress_user_satisfaction",
            "user_id",
            "satisfaction_state",
            "updated_at",
        ),
        Index(
            "ix_achievement_progress_definition_satisfaction",
            "achievement_definition_id",
            "rule_version",
            "satisfaction_state",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    achievement_definition_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    progress_model: Mapped[str] = mapped_column(Text, nullable=False)
    current_value: Mapped[int | None] = mapped_column(BigInteger)
    progress_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    satisfaction_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'unsatisfied'")
    )
    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_progress_event_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    last_event_sequence: Mapped[int | None] = mapped_column(BigInteger)
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class AchievementUnlock(Base):
    """Immutable first unlock; later progress reduction never removes it."""

    __tablename__ = "achievement_unlocks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_achievement_unlocks_user_id_users",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["achievement_definition_id", "rule_version"],
            ["achievement_definitions.id", "achievement_definitions.rule_version"],
            name="fk_achievement_unlocks_definition_version",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            [
                "achievement_progress_id",
                "user_id",
                "achievement_definition_id",
                "rule_version",
            ],
            [
                "achievement_progress.id",
                "achievement_progress.user_id",
                "achievement_progress.achievement_definition_id",
                "achievement_progress.rule_version",
            ],
            name="fk_achievement_unlocks_progress_user_definition_version",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            [
                "source_progress_event_id",
                "user_id",
                "source_progress_event_sequence",
            ],
            ["progress_events.id", "progress_events.user_id", "progress_events.event_sequence"],
            name="fk_achievement_unlocks_source_event_user_sequence",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "user_id",
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_unlocks_user_definition_version",
        ),
        UniqueConstraint(
            "user_id", "event_sequence", name="uq_achievement_unlocks_user_sequence"
        ),
        UniqueConstraint("id", "user_id", name="uq_achievement_unlocks_id_user"),
        CheckConstraint(
            "rule_version >= 1",
            name="ck_achievement_unlocks_rule_version_positive",
        ),
        CheckConstraint(
            "source_progress_event_sequence >= 1",
            name="ck_achievement_unlocks_source_sequence_positive",
        ),
        CheckConstraint(
            "event_sequence >= 1",
            name="ck_achievement_unlocks_event_sequence_positive",
        ),
        CheckConstraint(
            "created_at >= unlocked_at",
            name="ck_achievement_unlocks_created_after_unlock",
        ),
        Index("ix_achievement_unlocks_user_unlocked", "user_id", "unlocked_at"),
        Index(
            "ix_achievement_unlocks_definition_unlocked",
            "achievement_definition_id",
            "rule_version",
            "unlocked_at",
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
    achievement_progress_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    source_progress_event_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    source_progress_event_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

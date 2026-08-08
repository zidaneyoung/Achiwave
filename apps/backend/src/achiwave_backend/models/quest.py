from datetime import datetime
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
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class Quest(Base):
    """Immutable-owner quest definition; recurring definitions never complete."""

    __tablename__ = "quests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["campaign_id", "user_id"],
            ["campaigns.id", "campaigns.user_id"],
            name="fk_quests_campaign_user_campaigns",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "id", "user_id", name="uq_quests_id_user"
        ),
        UniqueConstraint(
            "id",
            "user_id",
            "campaign_id",
            "quest_type",
            name="uq_quests_id_user_campaign_type",
        ),
        CheckConstraint(
            "quest_type IN ('one_time', 'recurring')",
            name="ck_quests_quest_type",
        ),
        CheckConstraint(
            "definition_state IN ('active', 'archived')",
            name="ck_quests_definition_state",
        ),
        CheckConstraint(
            "title = btrim(title) AND title <> ''",
            name="ck_quests_title_nonblank",
        ),
        CheckConstraint("reward_xp >= 0", name="ck_quests_reward_xp_nonnegative"),
        CheckConstraint(
            "category IS NULL OR category IN "
            "('personal', 'health', 'learning', 'work', 'finance')",
            name="ck_quests_category",
        ),
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('easy', 'medium', 'hard')",
            name="ck_quests_difficulty",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="ck_quests_display_order_nonnegative",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_quests_record_version_positive",
        ),
        CheckConstraint(
            "due_at IS NULL OR available_from IS NULL OR due_at >= available_from",
            name="ck_quests_due_not_before_availability",
        ),
        CheckConstraint(
            "one_time_timezone_name IS NULL OR one_time_timezone_name = 'UTC' "
            "OR one_time_timezone_name ~ "
            "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(/[A-Za-z0-9_+-]+)*$'",
            name="ck_quests_one_time_timezone_shape",
        ),
        CheckConstraint(
            "quest_type = 'one_time' OR (available_from IS NULL AND due_at IS NULL "
            "AND one_time_timezone_name IS NULL)",
            name="ck_quests_recurring_excludes_one_time_schedule",
        ),
        CheckConstraint(
            "definition_state <> 'archived' OR archived_at IS NOT NULL",
            name="ck_quests_archived_timestamp",
        ),
        Index(
            "ix_quests_user_campaign_state_order",
            "user_id",
            "campaign_id",
            "definition_state",
            "display_order",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    quest_type: Mapped[str] = mapped_column(Text, nullable=False)
    definition_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str | None] = mapped_column(Text)
    reward_xp: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    available_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    one_time_timezone_name: Mapped[str | None] = mapped_column(Text)
    record_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    restored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

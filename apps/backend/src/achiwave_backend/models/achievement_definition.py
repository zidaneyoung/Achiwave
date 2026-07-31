from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class AchievementDefinition(Base):
    """Versioned backend-owned achievement presentation definition."""

    __tablename__ = "achievement_definitions"
    __table_args__ = (
        UniqueConstraint(
            "definition_key",
            "rule_version",
            name="uq_achievement_definitions_key_rule_version",
        ),
        UniqueConstraint(
            "id",
            "rule_version",
            name="uq_achievement_definitions_id_rule_version",
        ),
        UniqueConstraint(
            "id",
            "rule_version",
            "progress_model",
            name="uq_achievement_definitions_id_rule_version_model",
        ),
        CheckConstraint(
            "definition_key ~ '^[a-z0-9]+(?:_[a-z0-9]+)*$'",
            name="ck_achievement_definitions_key_shape",
        ),
        CheckConstraint(
            "rule_version >= 1",
            name="ck_achievement_definitions_rule_version_positive",
        ),
        CheckConstraint(
            "visibility IN ('visible', 'progress_hidden', 'secret')",
            name="ck_achievement_definitions_visibility",
        ),
        CheckConstraint(
            "progress_model IN ('boolean_condition', 'monotonic_counter', "
            "'recalculable_counter', 'maximum_observed', "
            "'distinct_source_count', 'threshold')",
            name="ck_achievement_definitions_progress_model",
        ),
        CheckConstraint(
            "(progress_model = 'boolean_condition' AND threshold_value IS NULL) OR "
            "(progress_model <> 'boolean_condition' AND threshold_value >= 1)",
            name="ck_achievement_definitions_threshold_model",
        ),
        CheckConstraint(
            "public_name = btrim(public_name) AND public_name <> ''",
            name="ck_achievement_definitions_public_name_nonblank",
        ),
        CheckConstraint(
            "public_description = btrim(public_description) AND public_description <> ''",
            name="ck_achievement_definitions_public_description_nonblank",
        ),
        CheckConstraint(
            "icon_key ~ '^[a-z0-9]+(?:[_-][a-z0-9]+)*$'",
            name="ck_achievement_definitions_icon_key_shape",
        ),
        CheckConstraint(
            "accessible_label = btrim(accessible_label) AND accessible_label <> ''",
            name="ck_achievement_definitions_accessible_label_nonblank",
        ),
        CheckConstraint(
            "visibility = 'visible' OR progress_exposure_enabled = false",
            name="ck_achievement_definitions_hidden_progress_not_exposed",
        ),
        CheckConstraint(
            "(visibility = 'secret' "
            "AND locked_placeholder_name_key = 'achievement.secret.name' "
            "AND locked_placeholder_accessible_label_key = "
            "'achievement.secret.accessible_label') OR "
            "(visibility <> 'secret' AND locked_placeholder_name_key IS NULL "
            "AND locked_placeholder_accessible_label_key IS NULL)",
            name="ck_achievement_definitions_secret_placeholder",
        ),
        CheckConstraint(
            "definition_state IN ('draft', 'active', 'retired')",
            name="ck_achievement_definitions_state",
        ),
        CheckConstraint(
            "(definition_state = 'draft' AND activated_at IS NULL "
            "AND retired_at IS NULL) OR "
            "(definition_state = 'active' AND activated_at IS NOT NULL "
            "AND retired_at IS NULL) OR "
            "(definition_state = 'retired' AND activated_at IS NOT NULL "
            "AND retired_at IS NOT NULL AND retired_at >= activated_at)",
            name="ck_achievement_definitions_state_timestamps",
        ),
        Index(
            "ix_achievement_definitions_active_visibility",
            "visibility",
            "definition_key",
            postgresql_where=text("definition_state = 'active'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    definition_key: Mapped[str] = mapped_column(Text, nullable=False)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    visibility: Mapped[str] = mapped_column(Text, nullable=False)
    progress_model: Mapped[str] = mapped_column(Text, nullable=False)
    threshold_value: Mapped[int | None] = mapped_column(BigInteger)
    public_name: Mapped[str] = mapped_column(Text, nullable=False)
    public_description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_key: Mapped[str] = mapped_column(Text, nullable=False)
    accessible_label: Mapped[str] = mapped_column(Text, nullable=False)
    progress_exposure_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    locked_placeholder_name_key: Mapped[str | None] = mapped_column(Text)
    locked_placeholder_accessible_label_key: Mapped[str | None] = mapped_column(Text)
    retroactive_evaluation_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    definition_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'draft'")
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

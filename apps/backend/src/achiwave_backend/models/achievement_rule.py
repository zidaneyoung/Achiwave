from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    LargeBinary,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class AchievementRule(Base):
    """Private structured rule; never part of public serialization."""

    __tablename__ = "achievement_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["achievement_definition_id", "rule_version", "rule_model"],
            [
                "achievement_definitions.id",
                "achievement_definitions.rule_version",
                "achievement_definitions.progress_model",
            ],
            name="fk_achievement_rules_definition_version_model",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_rules_definition_version",
        ),
        UniqueConstraint(
            "achievement_definition_id",
            "rule_version",
            "rule_model",
            name="uq_achievement_rules_definition_version_model",
        ),
        CheckConstraint(
            "rule_schema_version >= 1",
            name="ck_achievement_rules_schema_version_positive",
        ),
        CheckConstraint(
            "jsonb_typeof(rule_configuration) = 'object'",
            name="ck_achievement_rules_configuration_object",
        ),
        CheckConstraint(
            "jsonb_typeof(authoritative_event_inputs) = 'array' "
            "AND jsonb_array_length(authoritative_event_inputs) >= 1",
            name="ck_achievement_rules_event_inputs_nonempty_array",
        ),
        CheckConstraint(
            "octet_length(integrity_hash) >= 16",
            name="ck_achievement_rules_integrity_hash_minimum_length",
        ),
        CheckConstraint(
            "activated_at IS NULL OR activated_at >= created_at",
            name="ck_achievement_rules_activation_after_creation",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    achievement_definition_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_model: Mapped[str] = mapped_column(Text, nullable=False)
    rule_configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, info={"sensitive": True}
    )
    authoritative_event_inputs: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, info={"sensitive": True}
    )
    rule_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    integrity_hash: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, info={"sensitive": True}
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class LevelDefinition(Base):
    """One threshold in a versioned backend-owned level curve."""

    __tablename__ = "level_definitions"
    __table_args__ = (
        UniqueConstraint(
            "curve_version",
            "minimum_total_xp",
            name="uq_level_definitions_curve_threshold",
        ),
        CheckConstraint(
            "curve_version >= 1", name="ck_level_definitions_curve_version_positive"
        ),
        CheckConstraint(
            "level_number >= 1", name="ck_level_definitions_level_number_positive"
        ),
        CheckConstraint(
            "minimum_total_xp >= 0", name="ck_level_definitions_threshold_nonnegative"
        ),
        CheckConstraint(
            "level_number <> 1 OR minimum_total_xp = 0",
            name="ck_level_definitions_level_one_zero",
        ),
        CheckConstraint(
            "activation_state IN ('draft', 'active', 'retired')",
            name="ck_level_definitions_activation_state",
        ),
        CheckConstraint(
            "(activation_state = 'draft' AND activated_at IS NULL AND retired_at IS NULL) OR "
            "(activation_state = 'active' AND activated_at IS NOT NULL AND retired_at IS NULL) OR "
            "(activation_state = 'retired' AND activated_at IS NOT NULL "
            "AND retired_at IS NOT NULL AND retired_at >= activated_at)",
            name="ck_level_definitions_activation_timestamps",
        ),
        Index(
            "ix_level_definitions_state_curve",
            "activation_state",
            "curve_version",
            "level_number",
        ),
    )

    curve_version: Mapped[int] = mapped_column(Integer, primary_key=True)
    level_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    minimum_total_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    activation_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'draft'")
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

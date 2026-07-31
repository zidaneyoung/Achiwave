from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class UserPreference(Base):
    """One authoritative preference row per user."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_preferences_user_id_users",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "timezone_name = 'UTC' OR timezone_name ~ "
            "'^[A-Za-z]+([_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(/[A-Za-z0-9_+-]+)*$'",
            name="ck_user_preferences_timezone_name_shape",
        ),
        CheckConstraint(
            "timezone_version >= 1",
            name="ck_user_preferences_timezone_version_positive",
        ),
        CheckConstraint(
            "notification_preference IN ('unspecified', 'enabled', 'disabled')",
            name="ck_user_preferences_notification_preference",
        ),
        CheckConstraint(
            "date_format IN ("
            "'system', 'day_month_year', 'month_day_year', 'year_month_day')",
            name="ck_user_preferences_date_format",
        ),
        CheckConstraint(
            "record_version >= 1",
            name="ck_user_preferences_record_version_positive",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    timezone_name: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'UTC'")
    )
    timezone_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    timezone_effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    notification_preference: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'unspecified'")
    )
    date_format: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'system'")
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

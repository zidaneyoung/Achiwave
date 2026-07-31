from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class Notification(Base):
    """User notification intent/history; never progression authority."""

    __tablename__ = "notifications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_notifications_user_id_users",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "user_id", name="uq_notifications_id_user"),
        UniqueConstraint(
            "user_id",
            "notification_type",
            "source_type",
            "source_id",
            name="uq_notifications_user_source_identity",
        ),
        CheckConstraint(
            "notification_type = btrim(notification_type) AND notification_type <> ''",
            name="ck_notifications_type_nonblank",
        ),
        CheckConstraint(
            "source_type = btrim(source_type) AND source_type <> ''",
            name="ck_notifications_source_type_nonblank",
        ),
        CheckConstraint(
            "privacy_classification IN ('public', 'private', 'secret')",
            name="ck_notifications_privacy_classification",
        ),
        CheckConstraint(
            "content_mode IN ('literal', 'localized')",
            name="ck_notifications_content_mode",
        ),
        CheckConstraint(
            "(content_mode = 'literal' AND title IS NOT NULL "
            "AND title = btrim(title) AND title <> '' AND body IS NOT NULL "
            "AND body = btrim(body) AND body <> '' AND localization_key IS NULL) OR "
            "(content_mode = 'localized' AND title IS NULL AND body IS NULL "
            "AND localization_key IS NOT NULL "
            "AND localization_key = btrim(localization_key) AND localization_key <> '')",
            name="ck_notifications_content_shape",
        ),
        CheckConstraint(
            "jsonb_typeof(localization_parameters) = 'object'",
            name="ck_notifications_localization_parameters_object",
        ),
        CheckConstraint(
            "privacy_classification <> 'secret' OR "
            "(lock_screen_title_key IS NOT NULL "
            "AND lock_screen_title_key = 'notification.generic.title' "
            "AND lock_screen_body_key IS NOT NULL "
            "AND lock_screen_body_key = 'notification.generic.body')",
            name="ck_notifications_secret_lock_screen_generic",
        ),
        CheckConstraint(
            "presentation_state IN ('unread', 'read', 'dismissed', 'archived')",
            name="ck_notifications_presentation_state",
        ),
        CheckConstraint(
            "(presentation_state = 'unread' AND read_at IS NULL "
            "AND dismissed_at IS NULL AND archived_at IS NULL) OR "
            "(presentation_state = 'read' AND read_at IS NOT NULL "
            "AND dismissed_at IS NULL AND archived_at IS NULL) OR "
            "(presentation_state = 'dismissed' AND dismissed_at IS NOT NULL "
            "AND archived_at IS NULL) OR "
            "(presentation_state = 'archived' AND archived_at IS NOT NULL)",
            name="ck_notifications_presentation_timestamps",
        ),
        CheckConstraint(
            "available_at >= created_at",
            name="ck_notifications_available_after_creation",
        ),
        CheckConstraint(
            "(deep_link_route IS NULL AND deep_link_target_id IS NULL) OR "
            "(deep_link_route IN ('campaign', 'quest', 'achievement', 'notifications') "
            "AND deep_link_target_id IS NOT NULL)",
            name="ck_notifications_deep_link_shape",
        ),
        Index(
            "ix_notifications_user_state_available",
            "user_id",
            "presentation_state",
            "available_at",
        ),
        Index("ix_notifications_user_source", "user_id", "source_type", "source_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    notification_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    privacy_classification: Mapped[str] = mapped_column(Text, nullable=False)
    content_mode: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    localization_key: Mapped[str | None] = mapped_column(Text)
    localization_parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    lock_screen_title_key: Mapped[str | None] = mapped_column(Text)
    lock_screen_body_key: Mapped[str | None] = mapped_column(Text)
    presentation_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'unread'")
    )
    deep_link_route: Mapped[str | None] = mapped_column(Text)
    deep_link_target_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

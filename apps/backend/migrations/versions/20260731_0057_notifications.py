"""Create notification intent and presentation history.

Revision ID: 20260731_0057
Revises: 20260731_0056
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0057"
down_revision: str | Sequence[str] | None = "20260731_0056"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_type", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("privacy_classification", sa.Text(), nullable=False),
        sa.Column("content_mode", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("localization_key", sa.Text(), nullable=True),
        sa.Column("localization_parameters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("lock_screen_title_key", sa.Text(), nullable=True),
        sa.Column("lock_screen_body_key", sa.Text(), nullable=True),
        sa.Column("presentation_state", sa.Text(), server_default="unread", nullable=False),
        sa.Column("deep_link_route", sa.Text(), nullable=True),
        sa.Column("deep_link_target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("notification_type = btrim(notification_type) AND notification_type <> ''", name="ck_notifications_type_nonblank"),
        sa.CheckConstraint("source_type = btrim(source_type) AND source_type <> ''", name="ck_notifications_source_type_nonblank"),
        sa.CheckConstraint("privacy_classification IN ('public', 'private', 'secret')", name="ck_notifications_privacy_classification"),
        sa.CheckConstraint("content_mode IN ('literal', 'localized')", name="ck_notifications_content_mode"),
        sa.CheckConstraint(
            "(content_mode = 'literal' AND title IS NOT NULL "
            "AND title = btrim(title) AND title <> '' AND body IS NOT NULL "
            "AND body = btrim(body) AND body <> '' AND localization_key IS NULL) OR "
            "(content_mode = 'localized' AND title IS NULL AND body IS NULL "
            "AND localization_key IS NOT NULL "
            "AND localization_key = btrim(localization_key) AND localization_key <> '')",
            name="ck_notifications_content_shape",
        ),
        sa.CheckConstraint("jsonb_typeof(localization_parameters) = 'object'", name="ck_notifications_localization_parameters_object"),
        sa.CheckConstraint(
            "privacy_classification <> 'secret' OR "
            "(lock_screen_title_key IS NOT NULL "
            "AND lock_screen_title_key = 'notification.generic.title' "
            "AND lock_screen_body_key IS NOT NULL "
            "AND lock_screen_body_key = 'notification.generic.body')",
            name="ck_notifications_secret_lock_screen_generic",
        ),
        sa.CheckConstraint("presentation_state IN ('unread', 'read', 'dismissed', 'archived')", name="ck_notifications_presentation_state"),
        sa.CheckConstraint(
            "(presentation_state = 'unread' AND read_at IS NULL AND dismissed_at IS NULL AND archived_at IS NULL) OR "
            "(presentation_state = 'read' AND read_at IS NOT NULL AND dismissed_at IS NULL AND archived_at IS NULL) OR "
            "(presentation_state = 'dismissed' AND dismissed_at IS NOT NULL AND archived_at IS NULL) OR "
            "(presentation_state = 'archived' AND archived_at IS NOT NULL)",
            name="ck_notifications_presentation_timestamps",
        ),
        sa.CheckConstraint("available_at >= created_at", name="ck_notifications_available_after_creation"),
        sa.CheckConstraint(
            "(deep_link_route IS NULL AND deep_link_target_id IS NULL) OR "
            "(deep_link_route IN ('campaign', 'quest', 'achievement', 'notifications') "
            "AND deep_link_target_id IS NOT NULL)",
            name="ck_notifications_deep_link_shape",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_notifications_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
        sa.UniqueConstraint("id", "user_id", name="uq_notifications_id_user"),
        sa.UniqueConstraint("user_id", "notification_type", "source_type", "source_id", name="uq_notifications_user_source_identity"),
    )
    op.create_index("ix_notifications_user_state_available", "notifications", ["user_id", "presentation_state", "available_at"], unique=False)
    op.create_index("ix_notifications_user_source", "notifications", ["user_id", "source_type", "source_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_user_source", table_name="notifications")
    op.drop_index("ix_notifications_user_state_available", table_name="notifications")
    op.drop_table("notifications")

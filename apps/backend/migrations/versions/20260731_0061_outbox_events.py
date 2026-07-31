"""Create transactional outbox events.

Revision ID: 20260731_0061
Revises: 20260731_0060
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0061"
down_revision: str | Sequence[str] | None = "20260731_0060"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("aggregate_type", sa.Text(), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("event_schema_version", sa.Integer(), nullable=False),
        sa.Column("processing_state", sa.Text(), server_default="pending", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safe_failure_class", sa.Text(), nullable=True),
        sa.CheckConstraint("aggregate_type = btrim(aggregate_type) AND aggregate_type <> ''", name="ck_outbox_events_aggregate_type_nonblank"),
        sa.CheckConstraint("event_type = btrim(event_type) AND event_type <> ''", name="ck_outbox_events_event_type_nonblank"),
        sa.CheckConstraint("event_schema_version >= 1", name="ck_outbox_events_schema_version_positive"),
        sa.CheckConstraint("jsonb_typeof(event_payload) = 'object'", name="ck_outbox_events_payload_object"),
        sa.CheckConstraint("NOT event_payload ?| ARRAY['access_token', 'refresh_token', 'password_hash', 'push_token', 'achievement_rule', 'evidence_content']", name="ck_outbox_events_forbidden_payload_keys"),
        sa.CheckConstraint("processing_state IN ('pending', 'in_flight', 'published', 'failed', 'cancelled')", name="ck_outbox_events_processing_state"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_outbox_events_attempt_count_nonnegative"),
        sa.CheckConstraint("(attempt_count = 0 AND last_attempt_at IS NULL) OR (attempt_count >= 1 AND last_attempt_at IS NOT NULL)", name="ck_outbox_events_attempt_timestamp"),
        sa.CheckConstraint("(locked_at IS NULL AND lease_expires_at IS NULL) OR (locked_at IS NOT NULL AND lease_expires_at IS NOT NULL AND lease_expires_at > locked_at)", name="ck_outbox_events_lease_pair"),
        sa.CheckConstraint("processing_state <> 'in_flight' OR (locked_at IS NOT NULL AND attempt_count >= 1)", name="ck_outbox_events_in_flight_lease"),
        sa.CheckConstraint("(processing_state = 'published' AND published_at IS NOT NULL) OR (processing_state <> 'published' AND published_at IS NULL)", name="ck_outbox_events_published_timestamp"),
        sa.CheckConstraint("processing_state <> 'failed' OR safe_failure_class IS NOT NULL", name="ck_outbox_events_failed_classification"),
        sa.CheckConstraint("available_at >= created_at", name="ck_outbox_events_available_after_creation"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_outbox_events_user_id_users", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_outbox_events"),
        sa.UniqueConstraint("id", "user_id", name="uq_outbox_events_id_user"),
    )
    op.create_index("ix_outbox_events_due", "outbox_events", ["available_at", "created_at"], unique=False, postgresql_where=sa.text("processing_state IN ('pending', 'failed')"))
    op.create_index("ix_outbox_events_stale_lease", "outbox_events", ["lease_expires_at"], unique=False, postgresql_where=sa.text("processing_state = 'in_flight'"))
    op.create_index("ix_outbox_events_aggregate", "outbox_events", ["aggregate_type", "aggregate_id", "created_at"], unique=False)
    op.create_foreign_key(
        "fk_notification_deliveries_outbox_user",
        "notification_deliveries",
        "outbox_events",
        ["outbox_event_id", "user_id"],
        ["id", "user_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_notification_deliveries_outbox_user", "notification_deliveries", type_="foreignkey")
    op.drop_index("ix_outbox_events_aggregate", table_name="outbox_events")
    op.drop_index("ix_outbox_events_stale_lease", table_name="outbox_events")
    op.drop_index("ix_outbox_events_due", table_name="outbox_events")
    op.drop_table("outbox_events")

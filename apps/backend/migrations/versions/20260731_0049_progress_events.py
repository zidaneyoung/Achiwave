"""Create authoritative progress events.

Revision ID: 20260731_0049
Revises: 20260731_0048
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0049"
down_revision: str | Sequence[str] | None = "20260731_0048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "progress_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_mutation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "server_received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("server_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_local_date", sa.Date(), nullable=True),
        sa.Column("rule_version", sa.Integer(), nullable=True),
        sa.Column(
            "event_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_sequence >= 1", name="ck_progress_events_event_sequence_positive"
        ),
        sa.CheckConstraint(
            "event_type = btrim(event_type) AND event_type <> ''",
            name="ck_progress_events_event_type_nonblank",
        ),
        sa.CheckConstraint(
            "source_type = btrim(source_type) AND source_type <> ''",
            name="ck_progress_events_source_type_nonblank",
        ),
        sa.CheckConstraint(
            "rule_version IS NULL OR rule_version >= 1",
            name="ck_progress_events_rule_version_positive",
        ),
        sa.CheckConstraint(
            "server_processed_at IS NULL OR server_processed_at >= server_received_at",
            name="ck_progress_events_processing_after_receipt",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(event_metadata) = 'object'",
            name="ck_progress_events_metadata_object",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_progress_events_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_progress_events_user_client_mutation",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_progress_events"),
        sa.UniqueConstraint(
            "id", "user_id", "event_sequence", name="uq_progress_events_id_user_sequence"
        ),
        sa.UniqueConstraint(
            "user_id", "event_sequence", name="uq_progress_events_user_sequence"
        ),
        sa.UniqueConstraint(
            "user_id",
            "event_type",
            "source_type",
            "source_id",
            name="uq_progress_events_user_source_identity",
        ),
    )
    op.create_index(
        "ix_progress_events_user_sequence",
        "progress_events",
        ["user_id", "event_sequence"],
        unique=False,
    )
    op.create_index(
        "ix_progress_events_user_source",
        "progress_events",
        ["user_id", "source_type", "source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_progress_events_user_source", table_name="progress_events")
    op.drop_index("ix_progress_events_user_sequence", table_name="progress_events")
    op.drop_table("progress_events")

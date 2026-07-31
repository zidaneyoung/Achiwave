"""Create private evidence attachment metadata.

Revision ID: 20260731_0060
Revises: 20260731_0059
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0060"
down_revision: str | Sequence[str] | None = "20260731_0059"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quest_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("storage_provider", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("content_digest", sa.LargeBinary(), nullable=False),
        sa.Column("upload_state", sa.Text(), server_default="pending", nullable=False),
        sa.Column("attachment_metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("upload_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("storage_provider IN ('s3', 'supabase_storage')", name="ck_evidence_attachments_storage_provider"),
        sa.CheckConstraint("storage_key = btrim(storage_key) AND storage_key <> ''", name="ck_evidence_attachments_storage_key_nonblank"),
        sa.CheckConstraint("original_filename = btrim(original_filename) AND original_filename <> '' AND char_length(original_filename) <= 255 AND position('/' in original_filename) = 0 AND position(chr(92) in original_filename) = 0", name="ck_evidence_attachments_filename_safe"),
        sa.CheckConstraint("media_type ~ '^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$'", name="ck_evidence_attachments_media_type_shape"),
        sa.CheckConstraint("byte_size >= 0", name="ck_evidence_attachments_byte_size_nonnegative"),
        sa.CheckConstraint("octet_length(content_digest) >= 16", name="ck_evidence_attachments_content_digest_minimum_length"),
        sa.CheckConstraint("upload_state IN ('pending', 'uploading', 'uploaded', 'processing', 'ready', 'rejected', 'deleted')", name="ck_evidence_attachments_upload_state"),
        sa.CheckConstraint("completion_id IS NULL OR occurrence_id IS NOT NULL", name="ck_evidence_attachments_completion_requires_occurrence"),
        sa.CheckConstraint("upload_state NOT IN ('uploaded', 'processing', 'ready') OR upload_completed_at IS NOT NULL", name="ck_evidence_attachments_uploaded_timestamp"),
        sa.CheckConstraint("upload_state <> 'ready' OR processing_completed_at IS NOT NULL", name="ck_evidence_attachments_ready_timestamp"),
        sa.CheckConstraint("upload_state <> 'rejected' OR (rejected_at IS NOT NULL AND rejection_reason IS NOT NULL)", name="ck_evidence_attachments_rejected_details"),
        sa.CheckConstraint("upload_state <> 'deleted' OR deleted_at IS NOT NULL", name="ck_evidence_attachments_deleted_timestamp"),
        sa.CheckConstraint("upload_completed_at IS NULL OR upload_completed_at >= created_at", name="ck_evidence_attachments_upload_after_creation"),
        sa.CheckConstraint("processing_completed_at IS NULL OR (upload_completed_at IS NOT NULL AND processing_completed_at >= upload_completed_at)", name="ck_evidence_attachments_processing_after_upload"),
        sa.CheckConstraint("jsonb_typeof(attachment_metadata) = 'object'", name="ck_evidence_attachments_metadata_object"),
        sa.ForeignKeyConstraint(["quest_id", "user_id"], ["quests.id", "quests.user_id"], name="fk_evidence_attachments_quest_user", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["occurrence_id", "user_id", "quest_id"], ["quest_occurrences.id", "quest_occurrences.user_id", "quest_occurrences.quest_id"], name="fk_evidence_attachments_occurrence_user_quest", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["completion_id", "user_id", "occurrence_id"], ["quest_completions.id", "quest_completions.user_id", "quest_completions.occurrence_id"], name="fk_evidence_attachments_completion_user_occurrence", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_evidence_attachments"),
        sa.UniqueConstraint("storage_provider", "storage_key", name="uq_evidence_attachments_provider_storage_key"),
        sa.UniqueConstraint("id", "user_id", name="uq_evidence_attachments_id_user"),
    )
    op.create_index("ix_evidence_attachments_user_quest_state", "evidence_attachments", ["user_id", "quest_id", "upload_state"], unique=False)
    op.create_index("ix_evidence_attachments_user_occurrence", "evidence_attachments", ["user_id", "occurrence_id"], unique=False)
    op.create_index("ix_evidence_attachments_user_digest", "evidence_attachments", ["user_id", "content_digest"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_evidence_attachments_user_digest", table_name="evidence_attachments")
    op.drop_index("ix_evidence_attachments_user_occurrence", table_name="evidence_attachments")
    op.drop_index("ix_evidence_attachments_user_quest_state", table_name="evidence_attachments")
    op.drop_table("evidence_attachments")

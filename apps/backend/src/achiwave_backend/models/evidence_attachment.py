from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    LargeBinary,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class EvidenceAttachment(Base):
    """Private object-storage metadata only; PostgreSQL stores no file contents."""

    __tablename__ = "evidence_attachments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["quest_id", "user_id"],
            ["quests.id", "quests.user_id"],
            name="fk_evidence_attachments_quest_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["occurrence_id", "user_id", "quest_id"],
            ["quest_occurrences.id", "quest_occurrences.user_id", "quest_occurrences.quest_id"],
            name="fk_evidence_attachments_occurrence_user_quest",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["completion_id", "user_id", "occurrence_id"],
            ["quest_completions.id", "quest_completions.user_id", "quest_completions.occurrence_id"],
            name="fk_evidence_attachments_completion_user_occurrence",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "storage_provider",
            "storage_key",
            name="uq_evidence_attachments_provider_storage_key",
        ),
        UniqueConstraint("id", "user_id", name="uq_evidence_attachments_id_user"),
        CheckConstraint(
            "storage_provider IN ('s3', 'supabase_storage')",
            name="ck_evidence_attachments_storage_provider",
        ),
        CheckConstraint(
            "storage_key = btrim(storage_key) AND storage_key <> ''",
            name="ck_evidence_attachments_storage_key_nonblank",
        ),
        CheckConstraint(
            "original_filename = btrim(original_filename) "
            "AND original_filename <> '' AND char_length(original_filename) <= 255 "
            "AND position('/' in original_filename) = 0 "
            "AND position(chr(92) in original_filename) = 0",
            name="ck_evidence_attachments_filename_safe",
        ),
        CheckConstraint(
            "media_type ~ '^[a-z0-9][a-z0-9!#$&^_.+-]*/[a-z0-9][a-z0-9!#$&^_.+-]*$'",
            name="ck_evidence_attachments_media_type_shape",
        ),
        CheckConstraint("byte_size >= 0", name="ck_evidence_attachments_byte_size_nonnegative"),
        CheckConstraint(
            "octet_length(content_digest) >= 16",
            name="ck_evidence_attachments_content_digest_minimum_length",
        ),
        CheckConstraint(
            "upload_state IN ('pending', 'uploading', 'uploaded', 'processing', "
            "'ready', 'rejected', 'deleted')",
            name="ck_evidence_attachments_upload_state",
        ),
        CheckConstraint(
            "completion_id IS NULL OR occurrence_id IS NOT NULL",
            name="ck_evidence_attachments_completion_requires_occurrence",
        ),
        CheckConstraint(
            "upload_state NOT IN ('uploaded', 'processing', 'ready') "
            "OR upload_completed_at IS NOT NULL",
            name="ck_evidence_attachments_uploaded_timestamp",
        ),
        CheckConstraint(
            "upload_state <> 'ready' OR processing_completed_at IS NOT NULL",
            name="ck_evidence_attachments_ready_timestamp",
        ),
        CheckConstraint(
            "upload_state <> 'rejected' OR "
            "(rejected_at IS NOT NULL AND rejection_reason IS NOT NULL)",
            name="ck_evidence_attachments_rejected_details",
        ),
        CheckConstraint(
            "upload_state <> 'deleted' OR deleted_at IS NOT NULL",
            name="ck_evidence_attachments_deleted_timestamp",
        ),
        CheckConstraint(
            "upload_completed_at IS NULL OR upload_completed_at >= created_at",
            name="ck_evidence_attachments_upload_after_creation",
        ),
        CheckConstraint(
            "processing_completed_at IS NULL OR "
            "(upload_completed_at IS NOT NULL AND processing_completed_at >= upload_completed_at)",
            name="ck_evidence_attachments_processing_after_upload",
        ),
        CheckConstraint(
            "jsonb_typeof(attachment_metadata) = 'object'",
            name="ck_evidence_attachments_metadata_object",
        ),
        Index("ix_evidence_attachments_user_quest_state", "user_id", "quest_id", "upload_state"),
        Index("ix_evidence_attachments_user_occurrence", "user_id", "occurrence_id"),
        Index("ix_evidence_attachments_user_digest", "user_id", "content_digest"),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    quest_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    occurrence_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    completion_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    storage_provider: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False, info={"sensitive": True})
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_digest: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    upload_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    attachment_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb"), info={"sensitive": True}
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    upload_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

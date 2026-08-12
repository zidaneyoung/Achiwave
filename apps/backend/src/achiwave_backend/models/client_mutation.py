from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
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


class ClientMutation(Base):
    """Durable per-user binding for exact replay and payload mismatch detection."""

    __tablename__ = "client_mutations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_client_mutations_user_id_users",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_client_mutations_device_user",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "user_id",
            "client_mutation_id",
            name="uq_client_mutations_user_client_mutation",
        ),
        UniqueConstraint("id", "user_id", name="uq_client_mutations_id_user"),
        CheckConstraint(
            "operation_type = btrim(operation_type) AND operation_type <> ''",
            name="ck_client_mutations_operation_type_nonblank",
        ),
        CheckConstraint(
            "target_type = btrim(target_type) AND target_type <> ''",
            name="ck_client_mutations_target_type_nonblank",
        ),
        CheckConstraint(
            "octet_length(payload_hash) >= 16",
            name="ck_client_mutations_payload_hash_minimum_length",
        ),
        CheckConstraint(
            "processing_status IN "
            "('received', 'processing', 'succeeded', 'permanent_failure')",
            name="ck_client_mutations_processing_status",
        ),
        CheckConstraint(
            "processing_status NOT IN ('succeeded', 'permanent_failure') "
            "OR processed_at IS NOT NULL",
            name="ck_client_mutations_terminal_processed_timestamp",
        ),
        CheckConstraint(
            "result_payload IS NULL OR jsonb_typeof(result_payload) = 'object'",
            name="ck_client_mutations_result_payload_object",
        ),
        Index(
            "ix_client_mutations_unfinished_received",
            "first_server_received_at",
            postgresql_where=text(
                "processing_status IN ('received', 'processing')"
            ),
        ),
        Index("ix_client_mutations_device", "device_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    client_mutation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    device_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    operation_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    first_server_received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    processing_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'received'")
    )
    result_type: Mapped[str | None] = mapped_column(Text)
    result_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, info={"sensitive": True}
    )
    safe_error_class: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

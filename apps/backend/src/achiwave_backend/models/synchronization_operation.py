from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from achiwave_backend.database import Base


class SynchronizationOperation(Base):
    """Auditable server-side synchronization state without queue processing logic."""

    __tablename__ = "synchronization_operations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_synchronization_operations_device_user",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_synchronization_operations_user_client_mutation",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "user_id",
            "client_mutation_id",
            name="uq_synchronization_operations_user_client_mutation",
        ),
        CheckConstraint(
            "operation_type = btrim(operation_type) AND operation_type <> ''",
            name="ck_synchronization_operations_operation_type_nonblank",
        ),
        CheckConstraint(
            "target_type = btrim(target_type) AND target_type <> ''",
            name="ck_synchronization_operations_target_type_nonblank",
        ),
        CheckConstraint(
            "expected_target_version IS NULL OR expected_target_version >= 1",
            name="ck_synchronization_operations_expected_version_positive",
        ),
        CheckConstraint(
            "operation_state IN ('pending', 'in_flight', 'succeeded', "
            "'retryable_failure', 'permanent_failure', 'cancelled')",
            name="ck_synchronization_operations_operation_state",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="ck_synchronization_operations_attempt_count_nonnegative",
        ),
        CheckConstraint(
            "(attempt_count = 0 AND last_attempt_at IS NULL) OR "
            "(attempt_count >= 1 AND last_attempt_at IS NOT NULL)",
            name="ck_synchronization_operations_attempt_timestamp",
        ),
        CheckConstraint(
            "operation_state <> 'in_flight' OR "
            "(lease_expires_at IS NOT NULL AND attempt_count >= 1)",
            name="ck_synchronization_operations_in_flight_lease",
        ),
        CheckConstraint(
            "operation_state <> 'succeeded' OR synchronized_at IS NOT NULL",
            name="ck_synchronization_operations_success_timestamp",
        ),
        Index(
            "ix_synchronization_operations_due",
            "next_attempt_at",
            "created_at",
            postgresql_where=text(
                "operation_state IN ('pending', 'retryable_failure')"
            ),
        ),
        Index(
            "ix_synchronization_operations_stale_lease",
            "lease_expires_at",
            postgresql_where=text("operation_state = 'in_flight'"),
        ),
        Index(
            "ix_synchronization_operations_user_state",
            "user_id",
            "operation_state",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    device_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    client_mutation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), nullable=False
    )
    operation_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False)
    expected_target_version: Mapped[int | None] = mapped_column(Integer)
    operation_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    safe_error_class: Mapped[str | None] = mapped_column(Text)
    result_type: Mapped[str | None] = mapped_column(Text)
    result_id: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    synchronized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

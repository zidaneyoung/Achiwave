"""Create synchronization operation audit state.

Revision ID: 20260731_0048
Revises: 20260731_0047
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0048"
down_revision: str | Sequence[str] | None = "20260731_0047"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synchronization_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_mutation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_type", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expected_target_version", sa.Integer(), nullable=True),
        sa.Column("operation_state", sa.Text(), server_default="pending", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("safe_error_class", sa.Text(), nullable=True),
        sa.Column("result_type", sa.Text(), nullable=True),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("synchronized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "operation_type = btrim(operation_type) AND operation_type <> ''",
            name="ck_synchronization_operations_operation_type_nonblank",
        ),
        sa.CheckConstraint(
            "target_type = btrim(target_type) AND target_type <> ''",
            name="ck_synchronization_operations_target_type_nonblank",
        ),
        sa.CheckConstraint(
            "expected_target_version IS NULL OR expected_target_version >= 1",
            name="ck_synchronization_operations_expected_version_positive",
        ),
        sa.CheckConstraint(
            "operation_state IN ('pending', 'in_flight', 'succeeded', "
            "'retryable_failure', 'permanent_failure', 'cancelled')",
            name="ck_synchronization_operations_operation_state",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0",
            name="ck_synchronization_operations_attempt_count_nonnegative",
        ),
        sa.CheckConstraint(
            "(attempt_count = 0 AND last_attempt_at IS NULL) OR "
            "(attempt_count >= 1 AND last_attempt_at IS NOT NULL)",
            name="ck_synchronization_operations_attempt_timestamp",
        ),
        sa.CheckConstraint(
            "operation_state <> 'in_flight' OR "
            "(lease_expires_at IS NOT NULL AND attempt_count >= 1)",
            name="ck_synchronization_operations_in_flight_lease",
        ),
        sa.CheckConstraint(
            "operation_state <> 'succeeded' OR synchronized_at IS NOT NULL",
            name="ck_synchronization_operations_success_timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_synchronization_operations_device_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_synchronization_operations_user_client_mutation",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_synchronization_operations"),
        sa.UniqueConstraint(
            "user_id",
            "client_mutation_id",
            name="uq_synchronization_operations_user_client_mutation",
        ),
    )
    op.create_index(
        "ix_synchronization_operations_due",
        "synchronization_operations",
        ["next_attempt_at", "created_at"],
        unique=False,
        postgresql_where=sa.text(
            "operation_state IN ('pending', 'retryable_failure')"
        ),
    )
    op.create_index(
        "ix_synchronization_operations_stale_lease",
        "synchronization_operations",
        ["lease_expires_at"],
        unique=False,
        postgresql_where=sa.text("operation_state = 'in_flight'"),
    )
    op.create_index(
        "ix_synchronization_operations_user_state",
        "synchronization_operations",
        ["user_id", "operation_state", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_synchronization_operations_user_state",
        table_name="synchronization_operations",
    )
    op.drop_index(
        "ix_synchronization_operations_stale_lease",
        table_name="synchronization_operations",
    )
    op.drop_index(
        "ix_synchronization_operations_due",
        table_name="synchronization_operations",
    )
    op.drop_table("synchronization_operations")

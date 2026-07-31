"""Create durable client mutation bindings.

Revision ID: 20260731_0047
Revises: 20260731_0046
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0047"
down_revision: str | Sequence[str] | None = "20260731_0046"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_mutations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_mutation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_type", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.LargeBinary(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "first_server_received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "processing_status", sa.Text(), server_default="received", nullable=False
        ),
        sa.Column("result_type", sa.Text(), nullable=True),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("safe_error_class", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
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
            name="ck_client_mutations_operation_type_nonblank",
        ),
        sa.CheckConstraint(
            "target_type = btrim(target_type) AND target_type <> ''",
            name="ck_client_mutations_target_type_nonblank",
        ),
        sa.CheckConstraint(
            "octet_length(payload_hash) >= 16",
            name="ck_client_mutations_payload_hash_minimum_length",
        ),
        sa.CheckConstraint(
            "processing_status IN "
            "('received', 'processing', 'succeeded', 'permanent_failure')",
            name="ck_client_mutations_processing_status",
        ),
        sa.CheckConstraint(
            "processing_status NOT IN ('succeeded', 'permanent_failure') "
            "OR processed_at IS NOT NULL",
            name="ck_client_mutations_terminal_processed_timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_client_mutations_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_client_mutations"),
        sa.UniqueConstraint(
            "user_id",
            "client_mutation_id",
            name="uq_client_mutations_user_client_mutation",
        ),
        sa.UniqueConstraint("id", "user_id", name="uq_client_mutations_id_user"),
    )
    op.create_index(
        "ix_client_mutations_unfinished_received",
        "client_mutations",
        ["first_server_received_at"],
        unique=False,
        postgresql_where=sa.text(
            "processing_status IN ('received', 'processing')"
        ),
    )
    op.create_foreign_key(
        "fk_quest_completions_user_client_mutation",
        "quest_completions",
        "client_mutations",
        ["user_id", "client_mutation_id"],
        ["user_id", "client_mutation_id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_quest_completion_reversals_user_client_mutation",
        "quest_completion_reversals",
        "client_mutations",
        ["user_id", "client_mutation_id"],
        ["user_id", "client_mutation_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_quest_completion_reversals_user_client_mutation",
        "quest_completion_reversals",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_quest_completions_user_client_mutation",
        "quest_completions",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_client_mutations_unfinished_received", table_name="client_mutations"
    )
    op.drop_table("client_mutations")

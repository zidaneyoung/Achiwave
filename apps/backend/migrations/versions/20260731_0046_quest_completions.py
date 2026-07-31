"""Create completion and reversal history.

Revision ID: 20260731_0046
Revises: 20260731_0045
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0046"
down_revision: str | Sequence[str] | None = "20260731_0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quest_completions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_mutation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "server_received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("server_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_effective_date", sa.Date(), nullable=False),
        sa.Column("device_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_timezone_name", sa.Text(), nullable=True),
        sa.Column("client_time_valid", sa.Boolean(), nullable=True),
        sa.Column("event_sequence", sa.BigInteger(), nullable=False),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_sequence >= 1",
            name="ck_quest_completions_event_sequence_positive",
        ),
        sa.CheckConstraint(
            "server_processed_at IS NULL OR server_processed_at >= server_received_at",
            name="ck_quest_completions_processing_after_receipt",
        ),
        sa.CheckConstraint(
            "(device_observed_at IS NULL AND client_time_valid IS NULL) "
            "OR (device_observed_at IS NOT NULL AND client_time_valid IS NOT NULL)",
            name="ck_quest_completions_client_time_pair",
        ),
        sa.CheckConstraint(
            "device_timezone_name IS NULL OR device_timezone_name = 'UTC' "
            "OR device_timezone_name ~ "
            "'^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
            "(?:/[A-Za-z0-9_+-]+)*$'",
            name="ck_quest_completions_device_timezone_shape",
        ),
        sa.ForeignKeyConstraint(
            ["occurrence_id", "user_id"],
            ["quest_occurrences.id", "quest_occurrences.user_id"],
            name="fk_quest_completions_occurrence_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_quest_completions_device_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quest_completions"),
        sa.UniqueConstraint(
            "id",
            "user_id",
            "occurrence_id",
            name="uq_quest_completions_id_user_occurrence",
        ),
        sa.UniqueConstraint(
            "user_id",
            "event_sequence",
            name="uq_quest_completions_user_event_sequence",
        ),
    )
    op.create_index(
        "uq_quest_completions_active_occurrence",
        "quest_completions",
        ["occurrence_id"],
        unique=True,
        postgresql_where=sa.text("reversed_at IS NULL"),
    )
    op.create_index(
        "uq_quest_completions_user_client_mutation",
        "quest_completions",
        ["user_id", "client_mutation_id"],
        unique=True,
        postgresql_where=sa.text("client_mutation_id IS NOT NULL"),
    )
    op.create_index(
        "ix_quest_completions_user_effective_date",
        "quest_completions",
        ["user_id", "completion_effective_date"],
        unique=False,
    )
    op.create_index(
        "ix_quest_completions_occurrence_received",
        "quest_completions",
        ["occurrence_id", "server_received_at"],
        unique=False,
    )
    op.create_table(
        "quest_completion_reversals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurrence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("completion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_mutation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "server_received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("server_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_sequence", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reason = btrim(reason) AND reason <> ''",
            name="ck_quest_completion_reversals_reason_nonblank",
        ),
        sa.CheckConstraint(
            "event_sequence >= 1",
            name="ck_quest_completion_reversals_event_sequence_positive",
        ),
        sa.CheckConstraint(
            "server_processed_at IS NULL OR server_processed_at >= server_received_at",
            name="ck_quest_completion_reversals_processing_after_receipt",
        ),
        sa.ForeignKeyConstraint(
            ["completion_id", "user_id", "occurrence_id"],
            [
                "quest_completions.id",
                "quest_completions.user_id",
                "quest_completions.occurrence_id",
            ],
            name="fk_quest_completion_reversals_completion_owner_occurrence",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["device_id", "user_id"],
            ["registered_devices.id", "registered_devices.user_id"],
            name="fk_quest_completion_reversals_device_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_quest_completion_reversals"),
        sa.UniqueConstraint(
            "id", "user_id", name="uq_quest_completion_reversals_id_user"
        ),
        sa.UniqueConstraint(
            "completion_id",
            name="uq_quest_completion_reversals_completion_id",
        ),
        sa.UniqueConstraint(
            "user_id",
            "event_sequence",
            name="uq_quest_completion_reversals_user_event_sequence",
        ),
    )
    op.create_index(
        "uq_quest_completion_reversals_user_client_mutation",
        "quest_completion_reversals",
        ["user_id", "client_mutation_id"],
        unique=True,
        postgresql_where=sa.text("client_mutation_id IS NOT NULL"),
    )
    op.create_index(
        "ix_quest_completion_reversals_user_received",
        "quest_completion_reversals",
        ["user_id", "server_received_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_quest_completion_reversals_user_received",
        table_name="quest_completion_reversals",
    )
    op.drop_index(
        "uq_quest_completion_reversals_user_client_mutation",
        table_name="quest_completion_reversals",
    )
    op.drop_table("quest_completion_reversals")
    op.drop_index(
        "ix_quest_completions_occurrence_received", table_name="quest_completions"
    )
    op.drop_index(
        "ix_quest_completions_user_effective_date", table_name="quest_completions"
    )
    op.drop_index(
        "uq_quest_completions_user_client_mutation", table_name="quest_completions"
    )
    op.drop_index(
        "uq_quest_completions_active_occurrence", table_name="quest_completions"
    )
    op.drop_table("quest_completions")

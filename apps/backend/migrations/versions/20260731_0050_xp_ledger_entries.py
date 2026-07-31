"""Create immutable XP ledger entries.

Revision ID: 20260731_0050
Revises: 20260731_0049
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0050"
down_revision: str | Sequence[str] | None = "20260731_0049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_quest_completions_id_user",
        "quest_completions",
        ["id", "user_id"],
    )
    op.create_table(
        "xp_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("xp_delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("completion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reversal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("progress_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_mutation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("source_award_amount", sa.Integer(), nullable=True),
        sa.Column("reverses_ledger_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_sequence", sa.BigInteger(), nullable=False),
        sa.Column(
            "server_recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reason IN ('quest_completion', 'completion_reversal')",
            name="ck_xp_ledger_entries_reason",
        ),
        sa.CheckConstraint(
            "event_sequence >= 1", name="ck_xp_ledger_entries_event_sequence_positive"
        ),
        sa.CheckConstraint(
            "rule_version >= 1", name="ck_xp_ledger_entries_rule_version_positive"
        ),
        sa.CheckConstraint(
            "source_award_amount IS NULL OR source_award_amount >= 0",
            name="ck_xp_ledger_entries_source_award_nonnegative",
        ),
        sa.CheckConstraint(
            "(reason = 'quest_completion' AND completion_id IS NOT NULL "
            "AND reversal_id IS NULL AND reverses_ledger_entry_id IS NULL "
            "AND source_award_amount IS NULL AND xp_delta >= 0) OR "
            "(reason = 'completion_reversal' AND completion_id IS NULL "
            "AND reversal_id IS NOT NULL AND reverses_ledger_entry_id IS NOT NULL "
            "AND source_award_amount IS NOT NULL AND xp_delta = -source_award_amount)",
            name="ck_xp_ledger_entries_reason_source_delta",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_xp_ledger_entries_user_id_users", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["completion_id", "user_id"],
            ["quest_completions.id", "quest_completions.user_id"],
            name="fk_xp_ledger_entries_completion_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reversal_id", "user_id"],
            ["quest_completion_reversals.id", "quest_completion_reversals.user_id"],
            name="fk_xp_ledger_entries_reversal_user",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["progress_event_id", "user_id", "event_sequence"],
            ["progress_events.id", "progress_events.user_id", "progress_events.event_sequence"],
            name="fk_xp_ledger_entries_progress_event_user_sequence",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "client_mutation_id"],
            ["client_mutations.user_id", "client_mutations.client_mutation_id"],
            name="fk_xp_ledger_entries_user_client_mutation",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reverses_ledger_entry_id", "user_id", "source_award_amount"],
            ["xp_ledger_entries.id", "xp_ledger_entries.user_id", "xp_ledger_entries.xp_delta"],
            name="fk_xp_ledger_entries_exact_source_award",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_xp_ledger_entries"),
        sa.UniqueConstraint(
            "id", "user_id", "xp_delta", name="uq_xp_ledger_entries_id_user_delta"
        ),
        sa.UniqueConstraint(
            "user_id", "event_sequence", name="uq_xp_ledger_entries_user_sequence"
        ),
        sa.UniqueConstraint("progress_event_id", name="uq_xp_ledger_entries_progress_event"),
    )
    op.create_index(
        "uq_xp_ledger_entries_completion_award",
        "xp_ledger_entries",
        ["completion_id"],
        unique=True,
        postgresql_where=sa.text("reason = 'quest_completion'"),
    )
    op.create_index(
        "uq_xp_ledger_entries_reversal_compensation",
        "xp_ledger_entries",
        ["reversal_id"],
        unique=True,
        postgresql_where=sa.text("reason = 'completion_reversal'"),
    )
    op.create_index(
        "uq_xp_ledger_entries_reverses_award",
        "xp_ledger_entries",
        ["reverses_ledger_entry_id"],
        unique=True,
        postgresql_where=sa.text("reverses_ledger_entry_id IS NOT NULL"),
    )
    op.create_index(
        "ix_xp_ledger_entries_user_recorded",
        "xp_ledger_entries",
        ["user_id", "server_recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_xp_ledger_entries_user_recorded", table_name="xp_ledger_entries")
    op.drop_index("uq_xp_ledger_entries_reverses_award", table_name="xp_ledger_entries")
    op.drop_index("uq_xp_ledger_entries_reversal_compensation", table_name="xp_ledger_entries")
    op.drop_index("uq_xp_ledger_entries_completion_award", table_name="xp_ledger_entries")
    op.drop_table("xp_ledger_entries")
    op.drop_constraint(
        "uq_quest_completions_id_user", "quest_completions", type_="unique"
    )

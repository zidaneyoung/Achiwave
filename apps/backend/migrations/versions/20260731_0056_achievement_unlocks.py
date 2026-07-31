"""Create immutable achievement unlocks.

Revision ID: 20260731_0056
Revises: 20260731_0055
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0056"
down_revision: str | Sequence[str] | None = "20260731_0055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "achievement_unlocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("achievement_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("achievement_progress_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_progress_event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_progress_event_sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_sequence", sa.BigInteger(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("rule_version >= 1", name="ck_achievement_unlocks_rule_version_positive"),
        sa.CheckConstraint("source_progress_event_sequence >= 1", name="ck_achievement_unlocks_source_sequence_positive"),
        sa.CheckConstraint("event_sequence >= 1", name="ck_achievement_unlocks_event_sequence_positive"),
        sa.CheckConstraint("created_at >= unlocked_at", name="ck_achievement_unlocks_created_after_unlock"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_achievement_unlocks_user_id_users", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["achievement_definition_id", "rule_version"],
            ["achievement_definitions.id", "achievement_definitions.rule_version"],
            name="fk_achievement_unlocks_definition_version",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["achievement_progress_id", "user_id", "achievement_definition_id", "rule_version"],
            ["achievement_progress.id", "achievement_progress.user_id", "achievement_progress.achievement_definition_id", "achievement_progress.rule_version"],
            name="fk_achievement_unlocks_progress_user_definition_version",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_progress_event_id", "user_id", "source_progress_event_sequence"],
            ["progress_events.id", "progress_events.user_id", "progress_events.event_sequence"],
            name="fk_achievement_unlocks_source_event_user_sequence",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_achievement_unlocks"),
        sa.UniqueConstraint(
            "user_id",
            "achievement_definition_id",
            "rule_version",
            name="uq_achievement_unlocks_user_definition_version",
        ),
        sa.UniqueConstraint("user_id", "event_sequence", name="uq_achievement_unlocks_user_sequence"),
        sa.UniqueConstraint("id", "user_id", name="uq_achievement_unlocks_id_user"),
    )
    op.create_index(
        "ix_achievement_unlocks_user_unlocked",
        "achievement_unlocks",
        ["user_id", "unlocked_at"],
        unique=False,
    )
    op.create_index(
        "ix_achievement_unlocks_definition_unlocked",
        "achievement_unlocks",
        ["achievement_definition_id", "rule_version", "unlocked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_achievement_unlocks_definition_unlocked", table_name="achievement_unlocks")
    op.drop_index("ix_achievement_unlocks_user_unlocked", table_name="achievement_unlocks")
    op.drop_table("achievement_unlocks")

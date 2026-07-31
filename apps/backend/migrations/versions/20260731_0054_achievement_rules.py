"""Create private structured achievement rules.

Revision ID: 20260731_0054
Revises: 20260731_0053
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0054"
down_revision: str | Sequence[str] | None = "20260731_0053"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "achievement_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("achievement_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("rule_model", sa.Text(), nullable=False),
        sa.Column("rule_configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("authoritative_event_inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rule_schema_version", sa.Integer(), nullable=False),
        sa.Column("integrity_hash", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rule_schema_version >= 1", name="ck_achievement_rules_schema_version_positive"),
        sa.CheckConstraint("jsonb_typeof(rule_configuration) = 'object'", name="ck_achievement_rules_configuration_object"),
        sa.CheckConstraint(
            "jsonb_typeof(authoritative_event_inputs) = 'array' "
            "AND jsonb_array_length(authoritative_event_inputs) >= 1",
            name="ck_achievement_rules_event_inputs_nonempty_array",
        ),
        sa.CheckConstraint("octet_length(integrity_hash) >= 16", name="ck_achievement_rules_integrity_hash_minimum_length"),
        sa.CheckConstraint("activated_at IS NULL OR activated_at >= created_at", name="ck_achievement_rules_activation_after_creation"),
        sa.ForeignKeyConstraint(
            ["achievement_definition_id", "rule_version", "rule_model"],
            ["achievement_definitions.id", "achievement_definitions.rule_version", "achievement_definitions.progress_model"],
            name="fk_achievement_rules_definition_version_model",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_achievement_rules"),
        sa.UniqueConstraint("achievement_definition_id", "rule_version", name="uq_achievement_rules_definition_version"),
        sa.UniqueConstraint(
            "achievement_definition_id",
            "rule_version",
            "rule_model",
            name="uq_achievement_rules_definition_version_model",
        ),
    )


def downgrade() -> None:
    op.drop_table("achievement_rules")

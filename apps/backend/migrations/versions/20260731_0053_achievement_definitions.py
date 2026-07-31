"""Create public achievement definitions.

Revision ID: 20260731_0053
Revises: 20260731_0052
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260731_0053"
down_revision: str | Sequence[str] | None = "20260731_0052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "achievement_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("definition_key", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("progress_model", sa.Text(), nullable=False),
        sa.Column("threshold_value", sa.BigInteger(), nullable=True),
        sa.Column("public_name", sa.Text(), nullable=False),
        sa.Column("public_description", sa.Text(), nullable=False),
        sa.Column("icon_key", sa.Text(), nullable=False),
        sa.Column("accessible_label", sa.Text(), nullable=False),
        sa.Column("progress_exposure_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("locked_placeholder_name_key", sa.Text(), nullable=True),
        sa.Column("locked_placeholder_accessible_label_key", sa.Text(), nullable=True),
        sa.Column("retroactive_evaluation_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("definition_state", sa.Text(), server_default="draft", nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("definition_key ~ '^[a-z0-9]+(?:_[a-z0-9]+)*$'", name="ck_achievement_definitions_key_shape"),
        sa.CheckConstraint("rule_version >= 1", name="ck_achievement_definitions_rule_version_positive"),
        sa.CheckConstraint("visibility IN ('visible', 'progress_hidden', 'secret')", name="ck_achievement_definitions_visibility"),
        sa.CheckConstraint(
            "progress_model IN ('boolean_condition', 'monotonic_counter', "
            "'recalculable_counter', 'maximum_observed', "
            "'distinct_source_count', 'threshold')",
            name="ck_achievement_definitions_progress_model",
        ),
        sa.CheckConstraint(
            "(progress_model = 'boolean_condition' AND threshold_value IS NULL) OR "
            "(progress_model <> 'boolean_condition' AND threshold_value >= 1)",
            name="ck_achievement_definitions_threshold_model",
        ),
        sa.CheckConstraint("public_name = btrim(public_name) AND public_name <> ''", name="ck_achievement_definitions_public_name_nonblank"),
        sa.CheckConstraint("public_description = btrim(public_description) AND public_description <> ''", name="ck_achievement_definitions_public_description_nonblank"),
        sa.CheckConstraint("icon_key ~ '^[a-z0-9]+(?:[_-][a-z0-9]+)*$'", name="ck_achievement_definitions_icon_key_shape"),
        sa.CheckConstraint("accessible_label = btrim(accessible_label) AND accessible_label <> ''", name="ck_achievement_definitions_accessible_label_nonblank"),
        sa.CheckConstraint("visibility = 'visible' OR progress_exposure_enabled = false", name="ck_achievement_definitions_hidden_progress_not_exposed"),
        sa.CheckConstraint(
            "(visibility = 'secret' "
            "AND locked_placeholder_name_key = 'achievement.secret.name' "
            "AND locked_placeholder_accessible_label_key = "
            "'achievement.secret.accessible_label') OR "
            "(visibility <> 'secret' AND locked_placeholder_name_key IS NULL "
            "AND locked_placeholder_accessible_label_key IS NULL)",
            name="ck_achievement_definitions_secret_placeholder",
        ),
        sa.CheckConstraint("definition_state IN ('draft', 'active', 'retired')", name="ck_achievement_definitions_state"),
        sa.CheckConstraint(
            "(definition_state = 'draft' AND activated_at IS NULL AND retired_at IS NULL) OR "
            "(definition_state = 'active' AND activated_at IS NOT NULL AND retired_at IS NULL) OR "
            "(definition_state = 'retired' AND activated_at IS NOT NULL "
            "AND retired_at IS NOT NULL AND retired_at >= activated_at)",
            name="ck_achievement_definitions_state_timestamps",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_achievement_definitions"),
        sa.UniqueConstraint("definition_key", "rule_version", name="uq_achievement_definitions_key_rule_version"),
        sa.UniqueConstraint("id", "rule_version", name="uq_achievement_definitions_id_rule_version"),
        sa.UniqueConstraint("id", "rule_version", "progress_model", name="uq_achievement_definitions_id_rule_version_model"),
    )
    op.create_index(
        "ix_achievement_definitions_active_visibility",
        "achievement_definitions",
        ["visibility", "definition_key"],
        unique=False,
        postgresql_where=sa.text("definition_state = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("ix_achievement_definitions_active_visibility", table_name="achievement_definitions")
    op.drop_table("achievement_definitions")

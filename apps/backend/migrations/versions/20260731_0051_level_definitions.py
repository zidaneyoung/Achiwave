"""Create versioned level curve definitions.

Revision ID: 20260731_0051
Revises: 20260731_0050
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0051"
down_revision: str | Sequence[str] | None = "20260731_0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "level_definitions",
        sa.Column("curve_version", sa.Integer(), nullable=False),
        sa.Column("level_number", sa.Integer(), nullable=False),
        sa.Column("minimum_total_xp", sa.Integer(), nullable=False),
        sa.Column("activation_state", sa.Text(), server_default="draft", nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "curve_version >= 1", name="ck_level_definitions_curve_version_positive"
        ),
        sa.CheckConstraint(
            "level_number >= 1", name="ck_level_definitions_level_number_positive"
        ),
        sa.CheckConstraint(
            "minimum_total_xp >= 0", name="ck_level_definitions_threshold_nonnegative"
        ),
        sa.CheckConstraint(
            "level_number <> 1 OR minimum_total_xp = 0",
            name="ck_level_definitions_level_one_zero",
        ),
        sa.CheckConstraint(
            "activation_state IN ('draft', 'active', 'retired')",
            name="ck_level_definitions_activation_state",
        ),
        sa.CheckConstraint(
            "(activation_state = 'draft' AND activated_at IS NULL AND retired_at IS NULL) OR "
            "(activation_state = 'active' AND activated_at IS NOT NULL AND retired_at IS NULL) OR "
            "(activation_state = 'retired' AND activated_at IS NOT NULL "
            "AND retired_at IS NOT NULL AND retired_at >= activated_at)",
            name="ck_level_definitions_activation_timestamps",
        ),
        sa.PrimaryKeyConstraint(
            "curve_version", "level_number", name="pk_level_definitions"
        ),
        sa.UniqueConstraint(
            "curve_version",
            "minimum_total_xp",
            name="uq_level_definitions_curve_threshold",
        ),
    )
    op.create_index(
        "ix_level_definitions_state_curve",
        "level_definitions",
        ["activation_state", "curve_version", "level_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_level_definitions_state_curve", table_name="level_definitions")
    op.drop_table("level_definitions")

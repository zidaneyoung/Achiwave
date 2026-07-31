"""Add the reduced-motion presentation preference.

Revision ID: 20260731_0079
Revises: 20260731_0078
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0079"
down_revision: str | Sequence[str] | None = "20260731_0078"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column(
            "reduced_motion",
            sa.Text(),
            nullable=False,
            server_default="system",
        ),
    )
    op.create_check_constraint(
        "ck_user_preferences_reduced_motion",
        "user_preferences",
        "reduced_motion IN ('system', 'reduce', 'allow')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_preferences_reduced_motion",
        "user_preferences",
        type_="check",
    )
    op.drop_column("user_preferences", "reduced_motion")

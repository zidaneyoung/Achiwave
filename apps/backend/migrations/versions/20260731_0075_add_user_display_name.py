"""Add an optional safe profile display name.

Revision ID: 20260731_0075
Revises: 20260731_0067
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0075"
down_revision: str | Sequence[str] | None = "20260731_0067"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_users_display_name_safe_shape",
        "users",
        "display_name IS NULL OR ("
        "display_name = btrim(display_name) "
        "AND char_length(display_name) BETWEEN 1 AND 80 "
        "AND display_name !~ '[[:cntrl:]]')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_display_name_safe_shape",
        "users",
        type_="check",
    )
    op.drop_column("users", "display_name")

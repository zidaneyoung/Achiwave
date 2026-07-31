"""Add the presentation-only date-format preference.

Revision ID: 20260731_0077
Revises: 20260731_0075
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0077"
down_revision: str | Sequence[str] | None = "20260731_0075"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column(
            "date_format",
            sa.Text(),
            nullable=False,
            server_default="system",
        ),
    )
    op.create_check_constraint(
        "ck_user_preferences_date_format",
        "user_preferences",
        "date_format IN ("
        "'system', 'day_month_year', 'month_day_year', 'year_month_day')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_preferences_date_format",
        "user_preferences",
        type_="check",
    )
    op.drop_column("user_preferences", "date_format")

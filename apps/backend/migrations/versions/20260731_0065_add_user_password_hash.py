"""Add private password-hash storage for authentication.

Revision ID: 20260731_0065
Revises: 20260731_0062
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0065"
down_revision: str | Sequence[str] | None = "20260731_0062"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_users_password_hash_nonblank",
        "users",
        "password_hash IS NULL OR btrim(password_hash) <> ''",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_password_hash_nonblank",
        "users",
        type_="check",
    )
    op.drop_column("users", "password_hash")

"""Enforce unique refresh credential digests.

Revision ID: 20260731_0067
Revises: 20260731_0065
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0067"
down_revision: str | Sequence[str] | None = "20260731_0065"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_device_sessions_credential_digest",
        "device_sessions",
        ["credential_digest"],
        unique=True,
        postgresql_where=sa.text("credential_digest IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_device_sessions_credential_digest",
        table_name="device_sessions",
    )

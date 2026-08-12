"""Link client mutation bindings to authenticated devices.

Revision ID: 20260812_0084
Revises: 20260808_0083
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260812_0084"
down_revision: str | Sequence[str] | None = "20260808_0083"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "client_mutations",
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_client_mutations_device_user",
        "client_mutations",
        "registered_devices",
        ["device_id", "user_id"],
        ["id", "user_id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_client_mutations_device",
        "client_mutations",
        ["device_id", "user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_client_mutations_device", table_name="client_mutations")
    op.drop_constraint(
        "fk_client_mutations_device_user",
        "client_mutations",
        type_="foreignkey",
    )
    op.drop_column("client_mutations", "device_id")

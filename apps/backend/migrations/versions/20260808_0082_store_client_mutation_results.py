"""Store durable client mutation result snapshots.

Revision ID: 20260808_0082
Revises: 20260808_0081
Create Date: 2026-08-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260808_0082"
down_revision: str | Sequence[str] | None = "20260808_0081"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "client_mutations",
        sa.Column(
            "result_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_client_mutations_result_payload_object",
        "client_mutations",
        "result_payload IS NULL OR jsonb_typeof(result_payload) = 'object'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_client_mutations_result_payload_object",
        "client_mutations",
        type_="check",
    )
    op.drop_column("client_mutations", "result_payload")

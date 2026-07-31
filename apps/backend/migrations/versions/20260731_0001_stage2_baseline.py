"""Define the empty Stage 2 database baseline.

Revision ID: 20260731_0001
Revises:
Create Date: 2026-07-31
"""

from collections.abc import Sequence

revision: str = "20260731_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Record the baseline without creating Stage 3 domain tables."""


def downgrade() -> None:
    """Remove the baseline revision marker."""

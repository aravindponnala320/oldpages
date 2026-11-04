"""Add rental_fee_per_day_cents to listings.

Revision ID: 0019_rental_fee_per_day
Revises: 0018_approval_workflow
Create Date: 2026-08-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019_rental_fee_per_day"
down_revision: str | None = "0018_approval_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("rental_fee_per_day_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "listings",
        sa.Column("open_to_exchange", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("listings", "open_to_exchange")
    op.drop_column("listings", "rental_fee_per_day_cents")

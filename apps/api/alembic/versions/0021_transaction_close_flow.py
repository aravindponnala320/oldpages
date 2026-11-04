"""Add cancellation reason and mutual receive markers to transactions.

Revision ID: 0021_transaction_close_flow
Revises: 0020_listing_visibility
Create Date: 2026-08-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021_transaction_close_flow"
down_revision: str | None = "0020_listing_visibility"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("cancellation_reason", sa.String(500), nullable=True))
    op.add_column("transactions", sa.Column("cancelled_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    op.add_column("transactions", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("transactions", sa.Column("buyer_marked_received_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("transactions", sa.Column("seller_marked_delivered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "seller_marked_delivered_at")
    op.drop_column("transactions", "buyer_marked_received_at")
    op.drop_column("transactions", "cancelled_at")
    op.drop_column("transactions", "cancelled_by_user_id")
    op.drop_column("transactions", "cancellation_reason")

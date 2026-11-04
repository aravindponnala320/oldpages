"""Add server_default now() to created_at/updated_at on M11-M14 tables.

Revision ID: 0017_fix_timestamp_defaults
Revises: 0016_readiness_gaps
Create Date: 2026-06-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_fix_timestamp_defaults"
down_revision: str | None = "0016_readiness_gaps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = [
    "carts",
    "cart_items",
    "orders",
    "order_items",
    "payments",
    "payouts",
    "refunds",
    "shipments",
    "disputes",
    "webhook_events",
    "idempotency_keys",
    "institutions",
    "institution_domains",
    "institution_members",
    "donation_campaigns",
    "donation_needs",
    "donation_pledges",
    "donation_receipts",
    "business_profiles",
    "business_locations",
    "staff_accounts",
    "inventory_imports",
    "subscription_plans",
    "subscriptions",
    "promotions",
    "coupons",
    "promotion_orders",
    "recommendations",
    "recommendation_feedbacks",
]


def upgrade() -> None:
    for table in TABLES:
        op.alter_column(
            table,
            "created_at",
            server_default=sa.func.now(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.alter_column(
            table,
            "updated_at",
            server_default=sa.func.now(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )


def downgrade() -> None:
    for table in TABLES:
        op.alter_column(
            table,
            "created_at",
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )
        op.alter_column(
            table,
            "updated_at",
            server_default=None,
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
        )

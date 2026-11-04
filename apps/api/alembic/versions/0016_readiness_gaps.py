"""Close milestone readiness gaps.

Revision ID: 0016_readiness_gaps
Revises: 0015_recommendations
Create Date: 2026-06-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_readiness_gaps"
down_revision: str | None = "0015_recommendations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.add_column(
        "inventory_imports",
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "inventory_imports",
        sa.Column("error_rows_json", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_unique_constraint(
        "uq_inventory_imports_profile_payload_hash",
        "inventory_imports",
        ["business_profile_id", "payload_hash"],
    )

    op.create_table(
        "promotion_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=26), nullable=False),
        sa.Column("promotion_id", sa.Integer(), nullable=False),
        sa.Column("seller_user_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(length=24), nullable=False, server_default="local"),
        sa.Column("provider_order_id", sa.String(length=240), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status in ('pending', 'paid', 'cancelled', 'refunded')", name="status"),
        sa.CheckConstraint("provider in ('local', 'razorpay', 'stripe')", name="provider"),
        sa.CheckConstraint("amount_cents >= 0", name="amount_cents_non_negative"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seller_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_promotion_orders_promotion_id", "promotion_orders", ["promotion_id"])
    op.create_index("ix_promotion_orders_seller_user_id", "promotion_orders", ["seller_user_id"])
    op.create_index("ix_promotion_orders_status", "promotion_orders", ["status"])
    op.create_index(
        "ix_promotion_orders_public_id",
        "promotion_orders",
        ["public_id"],
        unique=True,
    )

    op.add_column(
        "recommendations",
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.add_column(
        "recommendations",
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="rules"),
    )
    op.add_column(
        "recommendations",
        sa.Column(
            "model",
            sa.String(length=120),
            nullable=False,
            server_default="oldpages-rule-engine",
        ),
    )
    op.add_column(
        "recommendations",
        sa.Column("model_version", sa.String(length=40), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "model_version")
    op.drop_column("recommendations", "model")
    op.drop_column("recommendations", "provider")
    op.drop_column("recommendations", "confidence")

    op.drop_index("ix_promotion_orders_public_id", table_name="promotion_orders")
    op.drop_index("ix_promotion_orders_status", table_name="promotion_orders")
    op.drop_index("ix_promotion_orders_seller_user_id", table_name="promotion_orders")
    op.drop_index("ix_promotion_orders_promotion_id", table_name="promotion_orders")
    op.drop_table("promotion_orders")

    op.drop_constraint(
        "uq_inventory_imports_profile_payload_hash",
        "inventory_imports",
        type_="unique",
    )
    op.drop_column("inventory_imports", "error_rows_json")
    op.drop_column("inventory_imports", "payload_hash")

    op.drop_column("users", "is_superuser")

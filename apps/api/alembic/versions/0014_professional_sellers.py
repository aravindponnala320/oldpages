"""Create professional sellers and monetization tables.

Revision ID: 0014_professional_sellers
Revises: 0013_institutions_donations
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_professional_sellers"
down_revision: str | None = "0013_institutions_donations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "business_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("slug", sa.String(length=260), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False, server_default="individual"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("gstin", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("listing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type in ('individual', 'shop', 'publisher', 'library', 'institution')",
            name="type",
        ),
        sa.CheckConstraint("status in ('pending', 'active', 'suspended')", name="status"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_business_profiles_owner_user_id", "business_profiles", ["owner_user_id"])
    op.create_index("ix_business_profiles_slug", "business_profiles", ["slug"])

    op.create_table(
        "business_locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("business_profile_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=4), nullable=False, server_default="IN"),
        sa.Column("pincode", sa.String(length=12), nullable=True),
        sa.Column("latitude", sa.String(length=40), nullable=True),
        sa.Column("longitude", sa.String(length=40), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["business_profile_id"], ["business_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_business_locations_business_profile_id",
        "business_locations",
        ["business_profile_id"],
    )

    op.create_table(
        "staff_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("business_profile_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=24), nullable=False, server_default="staff"),
        sa.Column("permissions_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role in ('owner', 'manager', 'staff')", name="role"),
        sa.CheckConstraint("status in ('active', 'suspended')", name="status"),
        sa.ForeignKeyConstraint(
            ["business_profile_id"], ["business_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint(
            "business_profile_id", "user_id", name="uq_staff_accounts_profile_user"
        ),
    )
    op.create_index(
        "ix_staff_accounts_business_profile_id", "staff_accounts", ["business_profile_id"]
    )
    op.create_index("ix_staff_accounts_user_id", "staff_accounts", ["user_id"])

    op.create_table(
        "inventory_imports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("business_profile_id", sa.Integer(), nullable=False),
        sa.Column("imported_by_user_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_report_url", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('pending', 'processing', 'completed', 'failed')", name="status"
        ),
        sa.ForeignKeyConstraint(
            ["business_profile_id"], ["business_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["imported_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_inventory_imports_business_profile_id",
        "inventory_imports",
        ["business_profile_id"],
    )
    op.create_index("ix_inventory_imports_status", "inventory_imports", ["status"])

    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column(
            "billing_interval", sa.String(length=24), nullable=False, server_default="monthly"
        ),
        sa.Column("features_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("listing_limit", sa.Integer(), nullable=True),
        sa.Column("saved_search_limit", sa.Integer(), nullable=True),
        sa.Column("community_limit", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("billing_interval in ('monthly', 'yearly')", name="billing_interval"),
        sa.CheckConstraint("price_cents >= 0", name="price_cents_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("provider", sa.String(length=24), nullable=False, server_default="local"),
        sa.Column("provider_subscription_id", sa.String(length=240), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status in ('trialing', 'active', 'past_due', 'cancelled', 'expired')",
            name="status",
        ),
        sa.CheckConstraint("provider in ('local', 'razorpay', 'stripe')", name="provider"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["subscription_plans.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("seller_user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type in ('featured', 'search_boost', 'homepage', 'category_spotlight',"
            " 'urgent_badge')",
            name="type",
        ),
        sa.CheckConstraint("status in ('active', 'expired', 'cancelled')", name="status"),
        sa.CheckConstraint("amount_cents >= 0", name="amount_cents_non_negative"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seller_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_promotions_listing_id", "promotions", ["listing_id"])
    op.create_index("ix_promotions_seller_user_id", "promotions", ["seller_user_id"])
    op.create_index("ix_promotions_status", "promotions", ["status"])
    op.create_index("ix_promotions_ends_at", "promotions", ["ends_at"])

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("discount_type", sa.String(length=24), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("min_order_cents", sa.Integer(), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("discount_type in ('percent', 'fixed')", name="discount_type"),
        sa.CheckConstraint("discount_value > 0", name="discount_value_positive"),
        sa.CheckConstraint(
            "min_order_cents is null or min_order_cents >= 0",
            name="min_order_cents_non_negative",
        ),
        sa.CheckConstraint("max_uses is null or max_uses > 0", name="max_uses_positive"),
        sa.CheckConstraint("used_count >= 0", name="used_count_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"])
    op.create_index("ix_coupons_is_active", "coupons", ["is_active"])


def downgrade() -> None:
    op.drop_table("coupons")
    op.drop_table("promotions")
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
    op.drop_table("inventory_imports")
    op.drop_table("staff_accounts")
    op.drop_table("business_locations")
    op.drop_table("business_profiles")

"""Create listing and media tables.

Revision ID: 0004_listings_media
Revises: 0003_catalog
Create Date: 2026-06-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_listings_media"
down_revision: str | None = "0003_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def public_id_column() -> sa.Column:
    return sa.Column("public_id", sa.String(length=26), nullable=False)


def jsonb_array() -> sa.ColumnElement:
    return sa.text("'[]'::jsonb")


def jsonb_object() -> sa.ColumnElement:
    return sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_upload"),
        sa.Column("upload_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("public_url", sa.String(length=1000), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('pending_upload', 'uploaded', 'processing', 'approved', 'rejected')",
            name="status",
        ),
        sa.CheckConstraint("byte_size > 0", name="byte_size_positive"),
        sa.UniqueConstraint("public_id", name="uq_media_assets_public_id"),
        sa.UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
    )
    op.create_index("ix_media_assets_user_id", "media_assets", ["user_id"])
    op.create_index("ix_media_assets_status", "media_assets", ["status"])

    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "seller_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title_snapshot", sa.String(length=500), nullable=False),
        sa.Column(
            "listing_modes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_array(),
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("negotiable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("return_policy", sa.String(length=500), nullable=True),
        sa.Column("exchange_preferences", sa.String(length=500), nullable=True),
        sa.Column("lending_duration_days", sa.Integer(), nullable=True),
        sa.Column("rental_deposit_amount_cents", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in "
            "('draft', 'pending_moderation', 'active', 'paused', 'reserved', 'completed', "
            "'expired', 'suspended', 'rejected', 'deleted')",
            name="status",
        ),
        sa.CheckConstraint(
            "price_amount_cents is null or price_amount_cents >= 0",
            name="price_non_negative",
        ),
        sa.CheckConstraint(
            "quality_score >= 0 and quality_score <= 100",
            name="quality_score_range",
        ),
        sa.UniqueConstraint("public_id", name="uq_listings_public_id"),
    )
    op.create_index("ix_listings_seller_user_id", "listings", ["seller_user_id"])
    op.create_index("ix_listings_book_edition_id", "listings", ["book_edition_id"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_index("ix_listings_created_at", "listings", ["created_at"])

    op.create_table(
        "listing_conditions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("condition", sa.String(length=32), nullable=False),
        sa.Column("damage_details", sa.Text(), nullable=True),
        sa.Column("highlighting_percent", sa.Integer(), nullable=True),
        sa.Column("handwritten_notes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("name_written_inside", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("torn_pages", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("missing_pages", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("loose_binding", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("water_damage", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stains", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "odor_or_smoke_exposure", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("library_markings", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stickers", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dust_jacket_present", sa.Boolean(), nullable=True),
        sa.Column("supplemental_media_present", sa.Boolean(), nullable=True),
        sa.Column("access_code_status", sa.String(length=80), nullable=True),
        sa.Column("answer_key_present", sa.Boolean(), nullable=True),
        sa.Column("workbook_completion_percent", sa.Integer(), nullable=True),
        sa.Column("signed_by_author", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("first_edition", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("collectible_notes", sa.Text(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "condition in "
            "('new_sealed', 'like_new', 'excellent', 'very_good', 'good', 'acceptable', "
            "'poor', 'reference_only')",
            name="condition",
        ),
        sa.CheckConstraint(
            "highlighting_percent is null or "
            "(highlighting_percent >= 0 and highlighting_percent <= 100)",
            name="highlighting_percent_range",
        ),
        sa.CheckConstraint(
            "workbook_completion_percent is null or "
            "(workbook_completion_percent >= 0 and workbook_completion_percent <= 100)",
            name="workbook_completion_percent_range",
        ),
        sa.UniqueConstraint("public_id", name="uq_listing_conditions_public_id"),
        sa.UniqueConstraint("listing_id", name="uq_listing_conditions_listing_id"),
    )

    op.create_table(
        "listing_locations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("neighborhood", sa.String(length=120), nullable=True),
        sa.Column("public_area", sa.String(length=180), nullable=False),
        sa.Column("campus_pickup", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("exact_latitude", sa.String(length=40), nullable=True),
        sa.Column("exact_longitude", sa.String(length=40), nullable=True),
        sa.Column("pickup_notes_private", sa.Text(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_listing_locations_public_id"),
        sa.UniqueConstraint("listing_id", name="uq_listing_locations_listing_id"),
    )

    op.create_table(
        "listing_delivery_methods",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("method", sa.String(length=24), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("price_amount_cents", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        *timestamps(),
        sa.CheckConstraint("method in ('pickup', 'shipping')", name="method"),
        sa.CheckConstraint(
            "price_amount_cents is null or price_amount_cents >= 0",
            name="price_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_listing_delivery_methods_public_id"),
        sa.UniqueConstraint("listing_id", "method", name="uq_listing_delivery_methods_method"),
    )

    op.create_table(
        "listing_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity_total", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quantity_available", sa.Integer(), nullable=False, server_default="1"),
        *timestamps(),
        sa.CheckConstraint("quantity_total > 0", name="quantity_total_positive"),
        sa.CheckConstraint("quantity_available >= 0", name="quantity_available_non_negative"),
        sa.CheckConstraint(
            "quantity_available <= quantity_total", name="quantity_available_lte_total"
        ),
        sa.UniqueConstraint("public_id", name="uq_listing_inventory_public_id"),
        sa.UniqueConstraint("listing_id", name="uq_listing_inventory_listing_id"),
    )

    op.create_table(
        "listing_price_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "changed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("old_amount_cents", sa.Integer(), nullable=True),
        sa.Column("new_amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("reason", sa.String(length=120), nullable=False, server_default="manual_update"),
        *timestamps(),
        sa.CheckConstraint(
            "old_amount_cents is null or old_amount_cents >= 0",
            name="old_price_non_negative",
        ),
        sa.CheckConstraint(
            "new_amount_cents is null or new_amount_cents >= 0",
            name="new_price_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_listing_price_history_public_id"),
    )
    op.create_index(
        "ix_listing_price_history_listing_id",
        "listing_price_history",
        ["listing_id"],
    )

    op.create_table(
        "listing_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "media_asset_id",
            sa.Integer(),
            sa.ForeignKey("media_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alt_text", sa.String(length=280), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_listing_images_public_id"),
        sa.UniqueConstraint("media_asset_id", name="uq_listing_images_media_asset_id"),
    )
    op.create_index("ix_listing_images_listing_id", "listing_images", ["listing_id"])


def downgrade() -> None:
    op.drop_index("ix_listing_images_listing_id", table_name="listing_images")
    op.drop_table("listing_images")
    op.drop_index("ix_listing_price_history_listing_id", table_name="listing_price_history")
    op.drop_table("listing_price_history")
    op.drop_table("listing_inventory")
    op.drop_table("listing_delivery_methods")
    op.drop_table("listing_locations")
    op.drop_table("listing_conditions")
    op.drop_index("ix_listings_created_at", table_name="listings")
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_book_edition_id", table_name="listings")
    op.drop_index("ix_listings_seller_user_id", table_name="listings")
    op.drop_table("listings")
    op.drop_index("ix_media_assets_status", table_name="media_assets")
    op.drop_index("ix_media_assets_user_id", table_name="media_assets")
    op.drop_table("media_assets")

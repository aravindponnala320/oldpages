"""Create search and discovery tables.

Revision ID: 0005_search_discovery
Revises: 0004_listings_media
Create Date: 2026-06-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_search_discovery"
down_revision: str | None = "0004_listings_media"
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


def jsonb_object() -> sa.ColumnElement:
    return sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.add_column("listing_locations", sa.Column("public_latitude", sa.Float(), nullable=True))
    op.add_column("listing_locations", sa.Column("public_longitude", sa.Float(), nullable=True))
    op.execute(
        """
        UPDATE listing_locations
        SET
          public_latitude = round(exact_latitude::numeric, 2)::double precision,
          public_longitude = round(exact_longitude::numeric, 2)::double precision
        WHERE exact_latitude ~ '^-?[0-9]+(\\.[0-9]+)?$'
          AND exact_longitude ~ '^-?[0-9]+(\\.[0-9]+)?$'
          AND exact_latitude::numeric BETWEEN -90 AND 90
          AND exact_longitude::numeric BETWEEN -180 AND 180
        """
    )
    op.create_check_constraint(
        "public_latitude_range",
        "listing_locations",
        "public_latitude is null or (public_latitude >= -90 and public_latitude <= 90)",
    )
    op.create_check_constraint(
        "public_longitude_range",
        "listing_locations",
        "public_longitude is null or (public_longitude >= -180 and public_longitude <= 180)",
    )
    op.create_index("ix_listing_locations_city", "listing_locations", ["city"])
    op.create_index("ix_listing_locations_state", "listing_locations", ["state"])
    op.create_index("ix_listing_locations_country", "listing_locations", ["country"])
    op.execute(
        """
        CREATE INDEX ix_listings_search_tsv
        ON listings
        USING gin (
          to_tsvector(
            'simple',
            coalesce(title_snapshot, '') || ' ' || coalesce(description, '')
          )
        )
        """
    )
    op.execute("CREATE INDEX ix_listings_modes_gin ON listings USING gin (listing_modes)")
    op.execute(
        """
        CREATE INDEX ix_listing_locations_public_geography
        ON listing_locations
        USING gist (
          geography(ST_SetSRID(ST_MakePoint(public_longitude, public_latitude), 4326))
        )
        WHERE public_latitude IS NOT NULL AND public_longitude IS NOT NULL
        """
    )
    op.execute(
        "CREATE INDEX ix_book_editions_title_trgm ON book_editions USING gin (title gin_trgm_ops)"
    )
    op.execute("CREATE INDEX ix_authors_name_trgm ON authors USING gin (name gin_trgm_ops)")
    op.execute("CREATE INDEX ix_categories_name_trgm ON categories USING gin (name gin_trgm_ops)")
    op.execute(
        "CREATE INDEX ix_listing_locations_public_area_trgm "
        "ON listing_locations USING gin (public_area gin_trgm_ops)"
    )

    op.create_table(
        "search_query_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("query", sa.String(length=500), nullable=True),
        sa.Column(
            "filters_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("sort", sa.String(length=32), nullable=False, server_default="relevance"),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("zero_results", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("result_count >= 0", name="result_count_non_negative"),
        sa.CheckConstraint(
            "latency_ms is null or latency_ms >= 0",
            name="latency_ms_non_negative",
        ),
        sa.UniqueConstraint("public_id", name="uq_search_query_logs_public_id"),
    )
    op.create_index("ix_search_query_logs_user_id", "search_query_logs", ["user_id"])
    op.create_index("ix_search_query_logs_zero_results", "search_query_logs", ["zero_results"])
    op.create_index("ix_search_query_logs_created_at", "search_query_logs", ["created_at"])

    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=True),
        sa.Column(
            "filters_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("sort", sa.String(length=32), nullable=False, server_default="relevance"),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_matched_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "sort in ('relevance', 'nearest', 'newest', 'lowest_price', 'highest_price', "
            "'best_condition', 'most_saved')",
            name="sort",
        ),
        sa.CheckConstraint("last_result_count >= 0", name="last_result_count_non_negative"),
        sa.UniqueConstraint("public_id", name="uq_saved_searches_public_id"),
        sa.UniqueConstraint("user_id", "name", name="uq_saved_searches_user_name"),
    )
    op.create_index("ix_saved_searches_user_id", "saved_searches", ["user_id"])

    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "book_edition_id",
            sa.Integer(),
            sa.ForeignKey("book_editions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_wishlist_items_public_id"),
        sa.UniqueConstraint("user_id", "book_edition_id", name="uq_wishlist_items_user_book"),
    )
    op.create_index("ix_wishlist_items_user_id", "wishlist_items", ["user_id"])
    op.create_index("ix_wishlist_items_book_edition_id", "wishlist_items", ["book_edition_id"])

    op.create_table(
        "listing_favorites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_listing_favorites_public_id"),
        sa.UniqueConstraint("user_id", "listing_id", name="uq_listing_favorites_user_listing"),
    )
    op.create_index("ix_listing_favorites_user_id", "listing_favorites", ["user_id"])
    op.create_index("ix_listing_favorites_listing_id", "listing_favorites", ["listing_id"])

    op.create_table(
        "follows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.String(length=180), nullable=False),
        sa.Column("target_label", sa.String(length=240), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "target_type in ('user', 'seller', 'author', 'genre', 'community', 'college')",
            name="target_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_follows_public_id"),
        sa.UniqueConstraint("user_id", "target_type", "target_id", name="uq_follows_target"),
    )
    op.create_index("ix_follows_user_id", "follows", ["user_id"])
    op.create_index("ix_follows_target", "follows", ["target_type", "target_id"])

    op.create_table(
        "search_match_notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "saved_search_id",
            sa.Integer(),
            sa.ForeignKey("saved_searches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("match_count", sa.Integer(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint("status in ('pending', 'delivered', 'dismissed')", name="status"),
        sa.CheckConstraint("match_count > 0", name="match_count_positive"),
        sa.UniqueConstraint("public_id", name="uq_search_match_notifications_public_id"),
    )
    op.create_index(
        "ix_search_match_notifications_user_id",
        "search_match_notifications",
        ["user_id"],
    )
    op.create_index(
        "ix_search_match_notifications_status",
        "search_match_notifications",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_search_match_notifications_status", table_name="search_match_notifications")
    op.drop_index("ix_search_match_notifications_user_id", table_name="search_match_notifications")
    op.drop_table("search_match_notifications")
    op.drop_index("ix_follows_target", table_name="follows")
    op.drop_index("ix_follows_user_id", table_name="follows")
    op.drop_table("follows")
    op.drop_index("ix_listing_favorites_listing_id", table_name="listing_favorites")
    op.drop_index("ix_listing_favorites_user_id", table_name="listing_favorites")
    op.drop_table("listing_favorites")
    op.drop_index("ix_wishlist_items_book_edition_id", table_name="wishlist_items")
    op.drop_index("ix_wishlist_items_user_id", table_name="wishlist_items")
    op.drop_table("wishlist_items")
    op.drop_index("ix_saved_searches_user_id", table_name="saved_searches")
    op.drop_table("saved_searches")
    op.drop_index("ix_search_query_logs_created_at", table_name="search_query_logs")
    op.drop_index("ix_search_query_logs_zero_results", table_name="search_query_logs")
    op.drop_index("ix_search_query_logs_user_id", table_name="search_query_logs")
    op.drop_table("search_query_logs")
    op.execute("DROP INDEX IF EXISTS ix_listing_locations_public_area_trgm")
    op.execute("DROP INDEX IF EXISTS ix_categories_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_authors_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_book_editions_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_listing_locations_public_geography")
    op.execute("DROP INDEX IF EXISTS ix_listings_modes_gin")
    op.execute("DROP INDEX IF EXISTS ix_listings_search_tsv")
    op.drop_index("ix_listing_locations_country", table_name="listing_locations")
    op.drop_index("ix_listing_locations_state", table_name="listing_locations")
    op.drop_index("ix_listing_locations_city", table_name="listing_locations")
    op.drop_constraint(
        "ck_listing_locations_public_longitude_range",
        "listing_locations",
        type_="check",
    )
    op.drop_constraint(
        "ck_listing_locations_public_latitude_range",
        "listing_locations",
        type_="check",
    )
    op.drop_column("listing_locations", "public_longitude")
    op.drop_column("listing_locations", "public_latitude")

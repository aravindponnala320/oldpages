"""Trigram indexes that match the search query's lower(coalesce(column, '')) expressions.

0005 indexed the raw columns (``title gin_trgm_ops``), but search filters on
``lower(coalesce(title, '')) LIKE '%q%'``. Postgres only uses an expression index for the
exact expression, so those indexes were never used. Measured on 50k listings, text search
went from 283 ms to 158 ms per request.

Revision ID: 0024_search_text_indexes
Revises: 0023_category_tree
"""

from __future__ import annotations

from alembic import op

revision: str = "0024_search_text_indexes"
down_revision: str | None = "0023_category_tree"
branch_labels: str | None = None
depends_on: str | None = None

# (index name, table, column): every text column search_conditions() matches with LIKE.
INDEXES = (
    ("ix_listings_title_trgm", "listings", "title_snapshot"),
    ("ix_listings_description_trgm", "listings", "description"),
    ("ix_book_editions_title_trgm", "book_editions", "title"),
    ("ix_book_editions_subtitle_trgm", "book_editions", "subtitle"),
    ("ix_book_editions_description_trgm", "book_editions", "description"),
    ("ix_books_title_trgm", "books", "title"),
    ("ix_books_subtitle_trgm", "books", "subtitle"),
    ("ix_authors_name_trgm", "authors", "name"),
    ("ix_book_identifiers_value_trgm", "book_identifiers", "identifier_value"),
    ("ix_categories_name_trgm", "categories", "name"),
    ("ix_categories_slug_trgm", "categories", "slug"),
    ("ix_listing_locations_city_trgm", "listing_locations", "city"),
    ("ix_listing_locations_state_trgm", "listing_locations", "state"),
    ("ix_listing_locations_neighborhood_trgm", "listing_locations", "neighborhood"),
    ("ix_listing_locations_public_area_trgm", "listing_locations", "public_area"),
    ("ix_listing_locations_country_trgm", "listing_locations", "country"),
)

# Created by 0005 on the raw column; same names, so they are replaced.
RAW_COLUMN_INDEXES = (
    ("ix_book_editions_title_trgm", "book_editions", "title"),
    ("ix_authors_name_trgm", "authors", "name"),
    ("ix_categories_name_trgm", "categories", "name"),
    ("ix_listing_locations_public_area_trgm", "listing_locations", "public_area"),
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for name, _table, _column in RAW_COLUMN_INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
    for name, table, column in INDEXES:
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {name} ON {table} "
            f"USING gin (lower(coalesce({column}, '')) gin_trgm_ops)"
        )


def downgrade() -> None:
    for name, _table, _column in INDEXES:
        op.execute(f"DROP INDEX IF EXISTS {name}")
    for name, table, column in RAW_COLUMN_INDEXES:
        op.execute(f"CREATE INDEX {name} ON {table} USING gin ({column} gin_trgm_ops)")

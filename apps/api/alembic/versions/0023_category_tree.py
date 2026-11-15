"""Category tree: dropdown labels, a category per listing, and the full taxonomy.

Revision ID: 0023_category_tree
Revises: 0022_listing_geog_index
Create Date: 2026-11-14
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from oldpages_api.catalog.taxonomy_sync import sync_categories

revision: str = "0023_category_tree"
down_revision: str | None = "0022_listing_geog_index"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("child_label", sa.String(60), nullable=True))
    op.add_column(
        "listings",
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_listings_category_id", "listings", ["category_id"])
    sync_categories(op.get_bind())


def downgrade() -> None:
    op.drop_index("ix_listings_category_id", table_name="listings")
    op.drop_column("listings", "category_id")
    op.drop_column("categories", "child_label")

"""Add scope and visibility to listings.

Revision ID: 0020_listing_visibility
Revises: 0019_rental_fee_per_day
Create Date: 2026-08-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020_listing_visibility"
down_revision: str | None = "0019_rental_fee_per_day"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("scope", sa.String(24), nullable=False, server_default="personal"),
    )
    op.add_column(
        "listings",
        sa.Column("visibility", sa.String(32), nullable=False, server_default="public"),
    )
    op.add_column(
        "listings",
        sa.Column(
            "business_profile_id",
            sa.Integer(),
            sa.ForeignKey("business_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "listings",
        sa.Column(
            "institution_id",
            sa.Integer(),
            sa.ForeignKey("institutions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "scope",
        "listings",
        "scope in ('personal', 'business', 'institution')",
    )
    op.create_check_constraint(
        "visibility",
        "listings",
        "visibility in ('public', 'private', 'business_only', 'institution_only')",
    )
    op.create_index("ix_listings_scope", "listings", ["scope"])
    op.create_index("ix_listings_visibility", "listings", ["visibility"])
    op.create_index("ix_listings_business_profile_id", "listings", ["business_profile_id"])
    op.create_index("ix_listings_institution_id", "listings", ["institution_id"])


def downgrade() -> None:
    op.drop_index("ix_listings_institution_id", "listings")
    op.drop_index("ix_listings_business_profile_id", "listings")
    op.drop_index("ix_listings_visibility", "listings")
    op.drop_index("ix_listings_scope", "listings")
    op.drop_constraint("visibility", "listings", type_="check")
    op.drop_constraint("scope", "listings", type_="check")
    op.drop_column("listings", "institution_id")
    op.drop_column("listings", "business_profile_id")
    op.drop_column("listings", "visibility")
    op.drop_column("listings", "scope")

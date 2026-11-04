"""Add generated geography column and GIST index on listing_locations.

Revision ID: 0022_listing_geog_index
Revises: 0021_transaction_close_flow
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0022_listing_geog_index"
down_revision: str | None = "0021_transaction_close_flow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute(
        """
        ALTER TABLE listing_locations
        ADD COLUMN IF NOT EXISTS geog geography(Point, 4326)
        GENERATED ALWAYS AS (
            CASE
                WHEN public_longitude IS NOT NULL AND public_latitude IS NOT NULL
                THEN ST_SetSRID(ST_MakePoint(public_longitude, public_latitude), 4326)::geography
                ELSE NULL
            END
        ) STORED
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_listing_locations_geog "
        "ON listing_locations USING GIST (geog)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_listing_locations_geog")
    op.execute("ALTER TABLE listing_locations DROP COLUMN IF EXISTS geog")

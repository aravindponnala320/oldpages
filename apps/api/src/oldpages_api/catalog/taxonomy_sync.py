"""Write the category tree from `taxonomy.py` into the categories table.

Plain SQLAlchemy Core on a sync connection, so both a migration and the
`sync_categories` script can run it. Safe to repeat: rows are matched by slug.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from oldpages_api.catalog.taxonomy import RETIRED_SLUGS, flatten
from oldpages_api.shared.db.ids import new_ulid

categories = sa.table(
    "categories",
    sa.column("id", sa.Integer),
    sa.column("public_id", sa.String),
    sa.column("parent_id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("slug", sa.String),
    sa.column("child_label", sa.String),
    sa.column("sort_order", sa.Integer),
    sa.column("is_active", sa.Boolean),
)


def sync_categories(conn: Connection) -> tuple[int, int]:
    """Insert or update every category; returns (inserted, updated)."""
    ids = {slug: id_ for id_, slug in conn.execute(sa.select(categories.c.id, categories.c.slug))}
    inserted = updated = 0
    # flatten() yields parents before children, so a parent's id is known when needed.
    for item in flatten():
        values = {
            "name": item.name,
            "parent_id": ids[item.parent_slug] if item.parent_slug else None,
            "child_label": item.child_label,
            "sort_order": item.sort_order,
            "is_active": True,
        }
        if item.slug in ids:
            conn.execute(
                categories.update().where(categories.c.id == ids[item.slug]).values(**values)
            )
            updated += 1
        else:
            result = conn.execute(
                categories.insert()
                .values(slug=item.slug, public_id=new_ulid(), **values)
                .returning(categories.c.id)
            )
            ids[item.slug] = result.scalar_one()
            inserted += 1
    conn.execute(
        categories.update().where(categories.c.slug.in_(RETIRED_SLUGS)).values(is_active=False)
    )
    return inserted, updated

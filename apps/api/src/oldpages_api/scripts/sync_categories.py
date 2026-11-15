"""Apply catalog/taxonomy.py to the database: python -m oldpages_api.scripts.sync_categories"""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from oldpages_api.catalog.taxonomy_sync import sync_categories
from oldpages_api.core.config import get_settings


async def main() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.begin() as conn:
        inserted, updated = await conn.run_sync(sync_categories)
    await engine.dispose()
    print(f"categories: {inserted} added, {updated} updated")


if __name__ == "__main__":
    asyncio.run(main())

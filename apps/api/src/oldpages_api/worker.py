from __future__ import annotations

import asyncio
import logging

from oldpages_api.core.config import get_settings
from oldpages_api.shared.cache.redis import check_redis, close_redis
from oldpages_api.shared.db.database import check_database, dispose_database_engine
from oldpages_api.shared.observability.logging import configure_logging

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("worker_starting", extra={"environment": settings.environment})

    try:
        while True:
            await check_database()
            await check_redis()
            logger.info("worker_heartbeat")
            await asyncio.sleep(30)
    finally:
        await close_redis()
        await dispose_database_engine()
        logger.info("worker_stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

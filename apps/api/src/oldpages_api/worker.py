from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from oldpages_api.core.config import Settings, get_settings
from oldpages_api.payments import tasks as payment_tasks
from oldpages_api.search.tasks import send_saved_search_alerts
from oldpages_api.shared.cache.redis import check_redis, close_redis
from oldpages_api.shared.db.database import (
    check_database,
    dispose_database_engine,
    get_session_factory,
)
from oldpages_api.shared.observability.logging import configure_logging

logger = logging.getLogger(__name__)


@dataclass
class Job:
    name: str
    every_seconds: int
    run: Callable[[], Awaitable[int]]
    last_run: float = 0.0


def jobs(settings: Settings) -> list[Job]:
    factory = get_session_factory()
    return [
        Job(
            "expire_unpaid_orders",
            60,
            lambda: payment_tasks.expire_unpaid_orders(factory, settings),
        ),
        Job("expire_offer_holds", 300, lambda: payment_tasks.expire_offer_holds(factory, settings)),
        Job(
            "release_buyer_protection",
            900,
            lambda: payment_tasks.release_buyer_protection(factory, settings),
        ),
        Job("saved_search_alerts", 900, lambda: send_saved_search_alerts(factory)),
    ]


async def run_due(scheduled: list[Job], now: float) -> None:
    for job in scheduled:
        if now - job.last_run < job.every_seconds:
            continue
        job.last_run = now
        try:
            await job.run()
        except Exception:
            # One failing job must not stop the others; it is retried on its next turn.
            logger.exception("worker_job_failed", extra={"job": job.name})


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("worker_starting", extra={"environment": settings.environment})
    scheduled = jobs(settings)

    try:
        while True:
            await check_database()
            await check_redis()
            await run_due(scheduled, time.monotonic())
            logger.info("worker_heartbeat")
            await asyncio.sleep(settings.worker_interval_seconds)
    finally:
        await close_redis()
        await dispose_database_engine()
        logger.info("worker_stopped")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

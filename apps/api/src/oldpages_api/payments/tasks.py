from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def expire_unpaid_orders() -> None:
    """Cancel orders that have been in 'awaiting_payment' status past their deadline."""
    logger.info("Running expire_unpaid_orders task.")


async def release_buyer_protection() -> None:
    """Auto-complete delivered orders once the buyer protection window expires."""
    logger.info("Running release_buyer_protection task.")


async def process_payout_batch() -> None:
    """Process a batch of pending payouts to sellers."""
    logger.info("Running process_payout_batch task.")

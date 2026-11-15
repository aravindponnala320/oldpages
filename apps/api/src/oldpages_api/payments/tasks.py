from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from oldpages_api.core.config import Settings
from oldpages_api.identity.security import utc_now
from oldpages_api.payments.service import PaymentsService

logger = logging.getLogger(__name__)


async def expire_unpaid_orders(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> int:
    """Cancel orders that have been in 'awaiting_payment' status past their deadline."""
    cutoff = utc_now() - timedelta(minutes=settings.unpaid_order_minutes)
    async with session_factory() as session:
        count = await PaymentsService(session).expire_unpaid_orders(cutoff)
    if count:
        logger.info("unpaid_orders_expired", extra={"count": count})
    return count


async def expire_offer_holds(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> int:
    """Put back copies held for accepted offers that never moved to a pickup or payment."""
    cutoff = utc_now() - timedelta(hours=settings.offer_hold_hours)
    async with session_factory() as session:
        count = await PaymentsService(session).expire_offer_holds(cutoff)
    if count:
        logger.info("offer_holds_expired", extra={"count": count})
    return count


async def release_buyer_protection(
    session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> int:
    """Auto-complete delivered orders once the buyer protection window expires."""
    cutoff = utc_now() - timedelta(days=settings.buyer_protection_days)
    async with session_factory() as session:
        count = await PaymentsService(session).complete_protected_orders(cutoff)
    if count:
        logger.info("orders_auto_completed", extra={"count": count})
    return count


# Payouts are recorded as paid when the seller requests them (PaymentsService.initiate_payout);
# there is no payout provider yet, so nothing waits in a batch. Add one with the provider.

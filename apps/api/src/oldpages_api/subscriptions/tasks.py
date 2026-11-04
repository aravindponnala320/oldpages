from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def expire_subscriptions() -> None:
    """Expire past-due or ended subscriptions (stub)."""
    logger.info("expire_subscriptions task called")


def expire_promotions() -> None:
    """Expire promotions whose end_at has passed (stub)."""
    logger.info("expire_promotions task called")

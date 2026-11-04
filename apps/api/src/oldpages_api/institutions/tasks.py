from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def sync_institution_member_count(institution_id: int) -> None:
    """Recalculate and sync the member_count for an institution."""
    logger.info("sync_institution_member_count called for institution_id=%d", institution_id)

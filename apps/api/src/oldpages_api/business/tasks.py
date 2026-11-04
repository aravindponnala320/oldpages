from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def process_inventory_import(import_id: int) -> None:
    """Process an inventory import job (stub)."""
    logger.info("process_inventory_import called for import_id=%s", import_id)


def notify_staff_invitation(staff_id: int) -> None:
    """Send a staff invitation notification (stub)."""
    logger.info("notify_staff_invitation called for staff_id=%s", staff_id)

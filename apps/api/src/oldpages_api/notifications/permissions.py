from __future__ import annotations

from oldpages_api.identity.models import User
from oldpages_api.notifications.models import Notification


def can_read_notification(actor: User, notification: Notification) -> bool:
    return actor.id == notification.user_id

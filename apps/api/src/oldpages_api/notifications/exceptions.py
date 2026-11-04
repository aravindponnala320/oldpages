from __future__ import annotations

from oldpages_api.core.errors import AppError


class NotificationNotFoundError(AppError):
    def __init__(self) -> None:
        super().__init__(
            detail="Notification not found.",
            status_code=404,
            title="Notification Not Found",
            type_uri="https://oldpages.in/problems/notification-not-found",
        )

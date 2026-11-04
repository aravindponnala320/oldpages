from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.notifications.models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_notifications(
        self,
        user_id: int,
        *,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Notification], str | None]:
        stmt = (
            select(Notification)
            .options(*notification_load_options())
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit + 1)
        )
        if cursor:
            cursor_notification = await self.get_notification_by_public_id(cursor)
            if cursor_notification is not None:
                stmt = stmt.where(Notification.id < cursor_notification.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_notification_by_public_id(self, public_id: str) -> Notification | None:
        result = await self.session.execute(
            select(Notification)
            .options(*notification_load_options())
            .where(Notification.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_preferences(self, user_id: int) -> NotificationPreference | None:
        result = await self.session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def notification_load_options() -> tuple[ExecutableOption, ...]:
    return (selectinload(Notification.deliveries),)


__all__ = [
    "Notification",
    "NotificationDelivery",
    "NotificationPreference",
    "NotificationRepository",
]

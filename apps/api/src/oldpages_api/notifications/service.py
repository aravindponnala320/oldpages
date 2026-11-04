from __future__ import annotations

from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.notifications.events import (
    NOTIFICATION_CREATED,
    NOTIFICATION_PREFERENCES_UPDATED,
    NOTIFICATION_READ,
)
from oldpages_api.notifications.exceptions import NotificationNotFoundError
from oldpages_api.notifications.models import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)
from oldpages_api.notifications.permissions import can_read_notification
from oldpages_api.notifications.repository import NotificationRepository
from oldpages_api.notifications.schemas import (
    NotificationChannel,
    NotificationDeliveryResponse,
    NotificationDeliveryStatus,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
    NotificationResponse,
    NotificationStatus,
    NotificationType,
)
from oldpages_api.notifications.tasks import enqueue_notification_delivery
from oldpages_api.shared.db.ids import new_ulid


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = NotificationRepository(session)

    async def list_notifications(
        self,
        actor: User,
        *,
        cursor: str | None,
        limit: int,
    ) -> NotificationListResponse:
        notifications, next_cursor = await self.repo.list_notifications(
            actor.id,
            cursor=cursor,
            limit=limit,
        )
        return NotificationListResponse(
            items=[notification_response(item) for item in notifications],
            next_cursor=next_cursor,
        )

    async def mark_notification_read(
        self,
        notification_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> NotificationResponse:
        notification = await self.repo.get_notification_by_public_id(notification_id)
        if notification is None or not can_read_notification(actor, notification):
            raise NotificationNotFoundError()
        notification.status = "read"
        notification.read_at = utc_now()
        self.repo.add(
            AuditLog(
                action=NOTIFICATION_READ,
                actor_user_id=actor.id,
                context_json={"notification_id": notification.public_id},
                ip_address=context.ip_address,
                target_user_id=actor.id,
                user_agent=context.user_agent,
            )
        )
        await self.repo.commit()
        return notification_response(notification)

    async def get_or_create_preferences(self, actor: User) -> NotificationPreferenceResponse:
        preferences = await self.ensure_preferences(actor.id)
        await self.repo.commit()
        return notification_preference_response(preferences)

    async def update_preferences(
        self,
        payload: NotificationPreferenceUpdateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> NotificationPreferenceResponse:
        preferences = await self.ensure_preferences(actor.id)
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(preferences, key, value)
        self.repo.add(
            AuditLog(
                action=NOTIFICATION_PREFERENCES_UPDATED,
                actor_user_id=actor.id,
                context_json={"fields": sorted(updates.keys())},
                ip_address=context.ip_address,
                target_user_id=actor.id,
                user_agent=context.user_agent,
            )
        )
        await self.repo.commit()
        return notification_preference_response(preferences)

    async def create_notification(
        self,
        *,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        body: str,
        related_entity_type: str | None = None,
        related_entity_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> Notification:
        preferences = await self.ensure_preferences(user_id)
        notification = Notification(
            body=body,
            data_json=data or {},
            notification_type=notification_type,
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type,
            status="unread",
            title=title,
            user_id=user_id,
        )
        self.repo.add(notification)
        await self.repo.flush()
        for channel in enabled_channels(preferences, notification_type):
            self.repo.add(
                NotificationDelivery(
                    channel=channel,
                    idempotency_key=f"{notification.public_id}:{channel}:{new_ulid()}",
                    notification_id=notification.id,
                    provider=provider_for_channel(channel),
                    status="pending",
                    user_id=user_id,
                )
            )
        self.repo.add(
            AuditLog(
                action=NOTIFICATION_CREATED,
                actor_user_id=None,
                context_json={
                    "notification_id": notification.public_id,
                    "type": notification_type,
                },
                target_user_id=user_id,
            )
        )
        await enqueue_notification_delivery(notification.id)
        return notification

    async def ensure_preferences(self, user_id: int) -> NotificationPreference:
        preferences = await self.repo.get_preferences(user_id)
        if preferences is not None:
            return preferences
        preferences = NotificationPreference(user_id=user_id)
        self.repo.add(preferences)
        await self.repo.flush()
        return preferences


def enabled_channels(
    preferences: NotificationPreference,
    notification_type: NotificationType,
) -> list[NotificationChannel]:
    channels: list[NotificationChannel] = []
    type_enabled = (
        preferences.chat_requests_enabled
        if notification_type in {"chat_request", "chat_accepted", "chat_declined"}
        else preferences.messages_enabled
        if notification_type == "message"
        else True
    )
    if not type_enabled:
        return channels
    if preferences.in_app_enabled:
        channels.append("in_app")
    if preferences.email_enabled:
        channels.append("email")
    if preferences.push_enabled:
        channels.append("push")
    return channels


def provider_for_channel(channel: NotificationChannel) -> str:
    return {
        "email": "development-email",
        "in_app": "oldpages",
        "push": "development-push",
    }[channel]


def notification_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        body=notification.body,
        created_at=notification.created_at,
        data=notification.data_json,
        deliveries=[
            NotificationDeliveryResponse(
                channel=cast("NotificationChannel", delivery.channel),
                id=delivery.public_id,
                status=cast("NotificationDeliveryStatus", delivery.status),
            )
            for delivery in sorted(notification.deliveries, key=lambda item: item.channel)
        ],
        id=notification.public_id,
        read_at=notification.read_at,
        related_entity_id=notification.related_entity_id,
        related_entity_type=notification.related_entity_type,
        status=cast("NotificationStatus", notification.status),
        title=notification.title,
        type=cast("NotificationType", notification.notification_type),
    )


def notification_preference_response(
    preferences: NotificationPreference,
) -> NotificationPreferenceResponse:
    return NotificationPreferenceResponse(
        chat_requests_enabled=preferences.chat_requests_enabled,
        email_enabled=preferences.email_enabled,
        id=preferences.public_id,
        in_app_enabled=preferences.in_app_enabled,
        marketing_enabled=preferences.marketing_enabled,
        messages_enabled=preferences.messages_enabled,
        push_enabled=preferences.push_enabled,
        quiet_hours_end=preferences.quiet_hours_end,
        quiet_hours_start=preferences.quiet_hours_start,
    )

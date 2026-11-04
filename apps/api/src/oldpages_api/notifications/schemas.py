from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

NotificationType = Literal[
    "chat_request",
    "chat_accepted",
    "chat_declined",
    "message",
    "saved_search_match",
    "system",
]
NotificationStatus = Literal["unread", "read", "archived"]
NotificationChannel = Literal["in_app", "email", "push"]
NotificationDeliveryStatus = Literal["pending", "sent", "failed", "suppressed"]


class NotificationDeliveryResponse(BaseModel):
    channel: NotificationChannel
    id: str
    status: NotificationDeliveryStatus


class NotificationResponse(BaseModel):
    body: str
    created_at: datetime
    data: dict[str, Any]
    deliveries: list[NotificationDeliveryResponse]
    id: str
    read_at: datetime | None = None
    related_entity_id: str | None = None
    related_entity_type: str | None = None
    status: NotificationStatus
    title: str
    type: NotificationType


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None = None


class NotificationPreferenceResponse(BaseModel):
    chat_requests_enabled: bool
    email_enabled: bool
    id: str
    in_app_enabled: bool
    marketing_enabled: bool
    messages_enabled: bool
    push_enabled: bool
    quiet_hours_end: str | None = None
    quiet_hours_start: str | None = None


class NotificationPreferenceUpdateRequest(BaseModel):
    chat_requests_enabled: bool | None = None
    email_enabled: bool | None = None
    in_app_enabled: bool | None = None
    marketing_enabled: bool | None = None
    messages_enabled: bool | None = None
    push_enabled: bool | None = None
    quiet_hours_end: str | None = Field(default=None, pattern=r"^[0-2][0-9]:[0-5][0-9]$")
    quiet_hours_start: str | None = Field(default=None, pattern=r"^[0-2][0-9]:[0-5][0-9]$")

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_hour(cls, value: str | None) -> str | None:
        if value is None:
            return value
        hour = int(value.split(":", maxsplit=1)[0])
        if hour > 23:
            raise ValueError("Quiet hours must use a 24-hour HH:MM value.")
        return value

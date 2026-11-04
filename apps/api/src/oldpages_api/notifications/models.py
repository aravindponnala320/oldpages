from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.identity.models import User
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Notification(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "notification_type in "
            "('chat_request', 'chat_accepted', 'chat_declined', 'message', "
            "'saved_search_match', 'system')",
            name="notification_type",
        ),
        CheckConstraint("status in ('unread', 'read', 'archived')", name="status"),
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="unread")
    related_entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    data_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deliveries: Mapped[list[NotificationDelivery]] = relationship(
        back_populates="notification",
        cascade="all, delete-orphan",
    )
    user: Mapped[User] = relationship()


class NotificationPreference(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_preferences_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chat_requests_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    messages_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    marketing_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(5), nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(5), nullable=True)

    user: Mapped[User] = relationship()


class NotificationDelivery(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        CheckConstraint("channel in ('in_app', 'email', 'push')", name="channel"),
        CheckConstraint("status in ('pending', 'sent', 'failed', 'suppressed')", name="status"),
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        UniqueConstraint("idempotency_key", name="uq_notification_deliveries_idempotency_key"),
        Index("ix_notification_deliveries_notification_id", "notification_id"),
        Index("ix_notification_deliveries_status", "status"),
        Index("ix_notification_deliveries_user_channel", "user_id", "channel"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    notification: Mapped[Notification] = relationship(back_populates="deliveries")
    user: Mapped[User] = relationship()


__all__ = [
    "Notification",
    "NotificationDelivery",
    "NotificationPreference",
]

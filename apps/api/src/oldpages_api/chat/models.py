from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
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
from oldpages_api.listings.models import Listing, MediaAsset
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class ChatRequest(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "chat_requests"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'accepted', 'declined', 'blocked')",
            name="status",
        ),
        Index("ix_chat_requests_requester_user_id", "requester_user_id"),
        Index("ix_chat_requests_recipient_status", "recipient_user_id", "status"),
        Index("ix_chat_requests_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    requester_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    conversation_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    initial_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation | None] = relationship(
        back_populates="chat_requests",
        foreign_keys=[conversation_id],
    )
    listing: Mapped[Listing] = relationship()
    recipient: Mapped[User] = relationship(foreign_keys=[recipient_user_id])
    requester: Mapped[User] = relationship(foreign_keys=[requester_user_id])


class Conversation(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint("status in ('active', 'blocked', 'closed')", name="status"),
        Index("ix_conversations_listing_id", "listing_id"),
        Index("ix_conversations_last_message_at", "last_message_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    chat_requests: Mapped[list[ChatRequest]] = relationship(
        back_populates="conversation",
        foreign_keys=[ChatRequest.conversation_id],
    )
    listing: Mapped[Listing | None] = relationship()
    members: Mapped[list[ConversationMember]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class ConversationMember(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "conversation_members"
    __table_args__ = (
        CheckConstraint("role in ('requester', 'recipient')", name="role"),
        CheckConstraint("status in ('active', 'muted', 'archived', 'blocked')", name="status"),
        UniqueConstraint("conversation_id", "user_id", name="uq_conversation_members_user"),
        Index("ix_conversation_members_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_read_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class Message(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "message_type in ('text', 'image', 'listing', 'system')", name="message_type"
        ),
        UniqueConstraint(
            "conversation_id",
            "sender_user_id",
            "client_message_id",
            name="uq_messages_client_message",
        ),
        Index("ix_messages_conversation_created", "conversation_id", "created_at", "id"),
        Index("ix_messages_sender_user_id", "sender_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    client_message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message_type: Mapped[str] = mapped_column(String(24), nullable=False, default="text")
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    attachments: Mapped[list[MessageAttachment]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    listing: Mapped[Listing | None] = relationship()
    reads: Mapped[list[MessageRead]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )
    sender: Mapped[User] = relationship()


class MessageAttachment(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "message_attachments"
    __table_args__ = (
        CheckConstraint("attachment_type in ('image')", name="attachment_type"),
        UniqueConstraint("message_id", "media_asset_id", name="uq_message_attachments_media"),
        Index("ix_message_attachments_message_id", "message_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    media_asset_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id", ondelete="RESTRICT"))
    attachment_type: Mapped[str] = mapped_column(String(24), nullable=False, default="image")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    media_asset: Mapped[MediaAsset] = relationship()
    message: Mapped[Message] = relationship(back_populates="attachments")


class MessageRead(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "message_reads"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_message_reads_user_message"),
        Index("ix_message_reads_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message: Mapped[Message] = relationship(back_populates="reads")
    user: Mapped[User] = relationship()


class MessageReport(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "message_reports"
    __table_args__ = (
        CheckConstraint("status in ('open', 'reviewed', 'dismissed')", name="status"),
        UniqueConstraint("message_id", "reporter_user_id", name="uq_message_reports_reporter"),
        Index("ix_message_reports_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")

    message: Mapped[Message] = relationship()
    reporter: Mapped[User] = relationship()


__all__ = [
    "ChatRequest",
    "Conversation",
    "ConversationMember",
    "Message",
    "MessageAttachment",
    "MessageRead",
    "MessageReport",
]

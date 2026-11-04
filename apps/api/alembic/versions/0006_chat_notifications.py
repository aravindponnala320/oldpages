"""Create chat and notification tables.

Revision ID: 0006_chat_notifications
Revises: 0005_search_discovery
Create Date: 2026-06-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_chat_notifications"
down_revision: str | None = "0005_search_discovery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def public_id_column() -> sa.Column:
    return sa.Column("public_id", sa.String(length=26), nullable=False)


def jsonb_object() -> sa.ColumnElement:
    return sa.text("'{}'::jsonb")


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("status in ('active', 'blocked', 'closed')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_conversations_public_id"),
    )
    op.create_index("ix_conversations_listing_id", "conversations", ["listing_id"])
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])

    op.create_table(
        "chat_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "requester_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recipient_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("initial_message", sa.Text(), nullable=True),
        sa.Column("response_message", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "status in ('pending', 'accepted', 'declined', 'blocked')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_chat_requests_public_id"),
    )
    op.create_index("ix_chat_requests_requester_user_id", "chat_requests", ["requester_user_id"])
    op.create_index(
        "ix_chat_requests_recipient_status",
        "chat_requests",
        ["recipient_user_id", "status"],
    )
    op.create_index("ix_chat_requests_listing_id", "chat_requests", ["listing_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("client_message_id", sa.String(length=120), nullable=True),
        sa.Column("message_type", sa.String(length=24), nullable=False, server_default="text"),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "listing_id",
            sa.Integer(),
            sa.ForeignKey("listings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint(
            "message_type in ('text', 'image', 'listing', 'system')",
            name="message_type",
        ),
        sa.UniqueConstraint("public_id", name="uq_messages_public_id"),
        sa.UniqueConstraint(
            "conversation_id",
            "sender_user_id",
            "client_message_id",
            name="uq_messages_client_message",
        ),
    )
    op.create_index(
        "ix_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at", "id"],
    )
    op.create_index("ix_messages_sender_user_id", "messages", ["sender_user_id"])

    op.create_table(
        "conversation_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("muted_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_read_message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("role in ('requester', 'recipient')", name="role"),
        sa.CheckConstraint(
            "status in ('active', 'muted', 'archived', 'blocked')",
            name="status",
        ),
        sa.UniqueConstraint("public_id", name="uq_conversation_members_public_id"),
        sa.UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_members_user",
        ),
    )
    op.create_index(
        "ix_conversation_members_user_status",
        "conversation_members",
        ["user_id", "status"],
    )

    op.create_table(
        "message_attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "media_asset_id",
            sa.Integer(),
            sa.ForeignKey("media_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("attachment_type", sa.String(length=24), nullable=False, server_default="image"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        *timestamps(),
        sa.CheckConstraint("attachment_type in ('image')", name="attachment_type"),
        sa.UniqueConstraint("public_id", name="uq_message_attachments_public_id"),
        sa.UniqueConstraint("message_id", "media_asset_id", name="uq_message_attachments_media"),
    )
    op.create_index("ix_message_attachments_message_id", "message_attachments", ["message_id"])

    op.create_table(
        "message_reads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_message_reads_public_id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_reads_user_message"),
    )
    op.create_index("ix_message_reads_user_id", "message_reads", ["user_id"])

    op.create_table(
        "message_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reporter_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=80), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        *timestamps(),
        sa.CheckConstraint("status in ('open', 'reviewed', 'dismissed')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_message_reports_public_id"),
        sa.UniqueConstraint("message_id", "reporter_user_id", name="uq_message_reports_reporter"),
    )
    op.create_index("ix_message_reports_status", "message_reports", ["status"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="unread"),
        sa.Column("related_entity_type", sa.String(length=80), nullable=True),
        sa.Column("related_entity_id", sa.String(length=80), nullable=True),
        sa.Column(
            "data_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=jsonb_object(),
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "notification_type in ('chat_request', 'chat_accepted', 'chat_declined', "
            "'message', 'saved_search_match', 'system')",
            name="notification_type",
        ),
        sa.CheckConstraint("status in ('unread', 'read', 'archived')", name="status"),
        sa.UniqueConstraint("public_id", name="uq_notifications_public_id"),
    )
    op.create_index("ix_notifications_user_status", "notifications", ["user_id", "status"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("chat_requests_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("messages_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("marketing_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiet_hours_start", sa.String(length=5), nullable=True),
        sa.Column("quiet_hours_end", sa.String(length=5), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("public_id", name="uq_notification_preferences_public_id"),
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user_id"),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        public_id_column(),
        sa.Column(
            "notification_id",
            sa.Integer(),
            sa.ForeignKey("notifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.CheckConstraint("channel in ('in_app', 'email', 'push')", name="channel"),
        sa.CheckConstraint(
            "status in ('pending', 'sent', 'failed', 'suppressed')",
            name="status",
        ),
        sa.CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        sa.UniqueConstraint("public_id", name="uq_notification_deliveries_public_id"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_notification_deliveries_idempotency_key",
        ),
    )
    op.create_index(
        "ix_notification_deliveries_notification_id",
        "notification_deliveries",
        ["notification_id"],
    )
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"])
    op.create_index(
        "ix_notification_deliveries_user_channel",
        "notification_deliveries",
        ["user_id", "channel"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_user_channel", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index(
        "ix_notification_deliveries_notification_id",
        table_name="notification_deliveries",
    )
    op.drop_table("notification_deliveries")
    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_user_status", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_message_reports_status", table_name="message_reports")
    op.drop_table("message_reports")
    op.drop_index("ix_message_reads_user_id", table_name="message_reads")
    op.drop_table("message_reads")
    op.drop_index("ix_message_attachments_message_id", table_name="message_attachments")
    op.drop_table("message_attachments")
    op.drop_index("ix_conversation_members_user_status", table_name="conversation_members")
    op.drop_table("conversation_members")
    op.drop_index("ix_messages_sender_user_id", table_name="messages")
    op.drop_index("ix_messages_conversation_created", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_chat_requests_listing_id", table_name="chat_requests")
    op.drop_index("ix_chat_requests_recipient_status", table_name="chat_requests")
    op.drop_index("ix_chat_requests_requester_user_id", table_name="chat_requests")
    op.drop_table("chat_requests")
    op.drop_index("ix_conversations_last_message_at", table_name="conversations")
    op.drop_index("ix_conversations_listing_id", table_name="conversations")
    op.drop_table("conversations")

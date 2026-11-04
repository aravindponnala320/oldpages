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

from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class User(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'pending_deletion', 'deleted', 'suspended')",
            name="status",
        ),
        UniqueConstraint("email", name="uq_users_email"),
        Index("ix_users_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mobile_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped[UserProfile] = relationship(back_populates="user", uselist=False)
    preferences: Mapped[UserPreference] = relationship(back_populates="user", uselist=False)


class UserProfile(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint(
            "privacy_level in ('public', 'members_only', 'private')",
            name="privacy_level",
        ),
        CheckConstraint(
            "allow_messages_from in ('everyone', 'members', 'none')",
            name="allow_messages_from",
        ),
        UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
        UniqueConstraint("username", name="uq_user_profiles_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str | None] = mapped_column(String(40), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    approximate_location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(160), nullable=True)
    course_department: Mapped[str | None] = mapped_column(String(160), nullable=True)
    privacy_level: Mapped[str] = mapped_column(String(24), nullable=False, default="public")
    hide_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hide_institution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hide_followers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hide_shelves: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allow_messages_from: Mapped[str] = mapped_column(String(24), nullable=False, default="everyone")
    show_online_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_read_receipts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    favorite_genres: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    favorite_authors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    favorite_books: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    reading_interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    user: Mapped[User] = relationship(back_populates="profile")


class UserDevice(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "user_devices"
    __table_args__ = (
        UniqueConstraint("user_id", "device_fingerprint", name="uq_user_devices_fingerprint"),
        Index("ix_user_devices_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_from_user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)


class UserSession(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("refresh_token_hash", name="uq_user_sessions_refresh_token_hash"),
        Index("ix_user_sessions_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    refresh_token_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reuse_detected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)


class SocialAccount(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "social_accounts"
    __table_args__ = (
        CheckConstraint("provider in ('google', 'apple')", name="provider"),
        UniqueConstraint(
            "provider", "provider_account_id", name="uq_social_accounts_provider_account"
        ),
        UniqueConstraint("user_id", "provider", name="uq_social_accounts_user_provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserVerification(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "user_verifications"
    __table_args__ = (
        CheckConstraint(
            "verification_type in "
            "('email', 'mobile', 'password_reset', 'data_export', 'account_deletion')",
            name="verification_type",
        ),
        UniqueConstraint("token_hash", name="uq_user_verifications_token_hash"),
        Index("ix_user_verifications_user_type", "user_id", "verification_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    verification_type: Mapped[str] = mapped_column(String(40), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    destination: Mapped[str] = mapped_column(String(320), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class UserPreference(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_preferences_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    user: Mapped[User] = relationship(back_populates="preferences")


class UserBlock(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "user_blocks"
    __table_args__ = (
        CheckConstraint("blocker_user_id <> blocked_user_id", name="not_self"),
        UniqueConstraint("blocker_user_id", "blocked_user_id", name="uq_user_blocks_pair"),
        Index("ix_user_blocks_blocked_user_id", "blocked_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blocker_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    blocked_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(280), nullable=True)


class ConsentRecord(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (Index("ix_consent_records_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    terms_version: Mapped[str] = mapped_column(String(40), nullable=False)
    privacy_version: Mapped[str] = mapped_column(String(40), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)


class AuditLog(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_actor_user_id", "actor_user_id"),
        Index("ix_audit_logs_target_user_id", "target_user_id"),
        Index("ix_audit_logs_action", "action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    context_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

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

from oldpages_api.catalog.models import BookEdition
from oldpages_api.identity.models import User
from oldpages_api.listings.models import Listing
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Community(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "communities"
    __table_args__ = (
        CheckConstraint(
            "visibility in ('public', 'private', 'secret', 'institution_verified')",
            name="visibility",
        ),
        CheckConstraint(
            "membership_policy in ('open', 'request', 'approval', 'institution_verified')",
            name="membership_policy",
        ),
        CheckConstraint(
            "community_type in ("
            "'college', 'university', 'school', 'area', 'city', 'apartment', 'workplace', "
            "'language', 'genre', 'author', 'series', 'book', 'exam', 'course', 'profession', "
            "'age_group', 'reading_goal', 'library', 'bookstore', 'publisher', 'social_cause', "
            "'local', 'general')",
            name="community_type",
        ),
        CheckConstraint("status in ('active', 'archived', 'suspended')", name="status"),
        UniqueConstraint("slug", name="uq_communities_slug"),
        Index("ix_communities_visibility_status", "visibility", "status"),
        Index("ix_communities_city_country", "city", "country"),
        Index("ix_communities_institution", "institution"),
        Index("ix_communities_genre", "genre"),
        Index("ix_communities_book_edition_id", "book_edition_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    community_type: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="public")
    membership_policy: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(180), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    language: Mapped[str | None] = mapped_column(String(40), nullable=True)
    book_edition_id: Mapped[int | None] = mapped_column(
        ForeignKey("book_editions.id", ondelete="SET NULL"),
        nullable=True,
    )
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    book_edition: Mapped[BookEdition | None] = relationship()
    channels: Mapped[list[CommunityChannel]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
    )
    members: Mapped[list[CommunityMember]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
    )
    owner: Mapped[User] = relationship()
    posts: Mapped[list[CommunityPost]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
    )
    roles: Mapped[list[CommunityRole]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
    )
    rules: Mapped[list[CommunityRule]] = relationship(
        back_populates="community",
        cascade="all, delete-orphan",
    )


class CommunityRole(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "community_roles"
    __table_args__ = (
        UniqueConstraint("community_id", "name", name="uq_community_roles_name"),
        Index("ix_community_roles_community_id", "community_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    permissions_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    community: Mapped[Community] = relationship(back_populates="roles")
    members: Mapped[list[CommunityMember]] = relationship(back_populates="role")


class CommunityMember(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "community_members"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'active', 'rejected', 'banned', 'muted')",
            name="status",
        ),
        UniqueConstraint("community_id", "user_id", name="uq_community_members_user"),
        Index("ix_community_members_user_status", "user_id", "status"),
        Index("ix_community_members_community_status", "community_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey("community_roles.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    answers_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    community: Mapped[Community] = relationship(back_populates="members")
    role: Mapped[CommunityRole] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class CommunityRule(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "community_rules"
    __table_args__ = (Index("ix_community_rules_community_id", "community_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    community: Mapped[Community] = relationship(back_populates="rules")


class CommunityChannel(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "community_channels"
    __table_args__ = (
        CheckConstraint(
            "channel_type in ('general', 'announcements', 'marketplace', 'questions', 'resources')",
            name="channel_type",
        ),
        CheckConstraint("visibility in ('public', 'members', 'moderators')", name="visibility"),
        UniqueConstraint("community_id", "slug", name="uq_community_channels_slug"),
        Index("ix_community_channels_community_id", "community_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False, default="general")
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="members")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    community: Mapped[Community] = relationship(back_populates="channels")
    posts: Mapped[list[CommunityPost]] = relationship(back_populates="channel")


class CommunityPost(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "community_posts"
    __table_args__ = (
        CheckConstraint(
            "post_type in ("
            "'text', 'review', 'photo', 'video', 'poll', 'question', 'recommendation', 'quote', "
            "'reading_update', 'listing', 'exchange_request', 'donation_request', 'event', "
            "'challenge', 'resource', 'announcement')",
            name="post_type",
        ),
        CheckConstraint(
            "status in ('published', 'pending_review', 'hidden', 'deleted')",
            name="status",
        ),
        Index("ix_community_posts_feed", "community_id", "status", "is_pinned", "created_at"),
        Index("ix_community_posts_author_user_id", "author_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("community_channels.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    post_type: Mapped[str] = mapped_column(String(40), nullable=False, default="text")
    title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    poll_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="published")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_announcement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    author: Mapped[User] = relationship()
    channel: Mapped[CommunityChannel | None] = relationship(back_populates="posts")
    comments: Mapped[list[PostComment]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )
    community: Mapped[Community] = relationship(back_populates="posts")
    listing: Mapped[Listing | None] = relationship()
    reactions: Mapped[list[PostReaction]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
    )


class PostComment(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "post_comments"
    __table_args__ = (
        CheckConstraint("status in ('published', 'hidden', 'deleted')", name="status"),
        Index("ix_post_comments_post_created", "post_id", "created_at"),
        Index("ix_post_comments_author_user_id", "author_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"))
    author_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    parent_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("post_comments.id", ondelete="SET NULL"),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="published")

    author: Mapped[User] = relationship()
    parent: Mapped[PostComment | None] = relationship(remote_side=[id])
    post: Mapped[CommunityPost] = relationship(back_populates="comments")


class PostReaction(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "post_reactions"
    __table_args__ = (
        CheckConstraint(
            "reaction_type in ('like', 'love', 'insightful', 'upvote', 'celebrate')",
            name="reaction_type",
        ),
        UniqueConstraint("post_id", "user_id", name="uq_post_reactions_user"),
        Index("ix_post_reactions_post_id", "post_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reaction_type: Mapped[str] = mapped_column(String(24), nullable=False, default="like")

    post: Mapped[CommunityPost] = relationship(back_populates="reactions")
    user: Mapped[User] = relationship()


class CommunityReport(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "community_reports"
    __table_args__ = (
        CheckConstraint(
            "target_type in ('community', 'post', 'comment', 'member')",
            name="target_type",
        ),
        CheckConstraint("status in ('open', 'resolved', 'dismissed')", name="status"),
        Index("ix_community_reports_community_status", "community_id", "status"),
        Index("ix_community_reports_reporter_user_id", "reporter_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    community_id: Mapped[int] = mapped_column(ForeignKey("communities.id", ondelete="CASCADE"))
    reporter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_type: Mapped[str] = mapped_column(String(24), nullable=False)
    target_community_post_id: Mapped[int | None] = mapped_column(
        ForeignKey("community_posts.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_post_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("post_comments.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_member_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="open")

    community: Mapped[Community] = relationship()
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_user_id])


__all__ = [
    "Community",
    "CommunityChannel",
    "CommunityMember",
    "CommunityPost",
    "CommunityReport",
    "CommunityRole",
    "CommunityRule",
    "PostComment",
    "PostReaction",
]

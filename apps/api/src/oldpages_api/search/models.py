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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.catalog.models import BookEdition
from oldpages_api.identity.models import User
from oldpages_api.listings.models import Listing
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin

SEARCH_SORT_VALUES = (
    "'relevance', 'nearest', 'newest', 'lowest_price', 'highest_price', "
    "'best_condition', 'most_saved'"
)


class SearchQueryLog(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "search_query_logs"
    __table_args__ = (
        CheckConstraint("result_count >= 0", name="result_count_non_negative"),
        CheckConstraint("latency_ms is null or latency_ms >= 0", name="latency_ms_non_negative"),
        Index("ix_search_query_logs_user_id", "user_id"),
        Index("ix_search_query_logs_zero_results", "zero_results"),
        Index("ix_search_query_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    query: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    sort: Mapped[str] = mapped_column(String(32), nullable=False, default="relevance")
    result_count: Mapped[int] = mapped_column(Integer, nullable=False)
    zero_results: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped[User | None] = relationship()


class SavedSearch(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "saved_searches"
    __table_args__ = (
        CheckConstraint(f"sort in ({SEARCH_SORT_VALUES})", name="sort"),
        CheckConstraint("last_result_count >= 0", name="last_result_count_non_negative"),
        UniqueConstraint("user_id", "name", name="uq_saved_searches_user_name"),
        Index("ix_saved_searches_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    query: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    sort: Mapped[str] = mapped_column(String(32), nullable=False, default="relevance")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship()


class WishlistItem(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint("user_id", "book_edition_id", name="uq_wishlist_items_user_book"),
        Index("ix_wishlist_items_user_id", "user_id"),
        Index("ix_wishlist_items_book_edition_id", "book_edition_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(ForeignKey("book_editions.id", ondelete="CASCADE"))

    book_edition: Mapped[BookEdition] = relationship()
    user: Mapped[User] = relationship()


class ListingFavorite(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uq_listing_favorites_user_listing"),
        Index("ix_listing_favorites_user_id", "user_id"),
        Index("ix_listing_favorites_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))

    listing: Mapped[Listing] = relationship()
    user: Mapped[User] = relationship()


class Follow(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "follows"
    __table_args__ = (
        CheckConstraint(
            "target_type in ('user', 'seller', 'author', 'genre', 'community', 'college')",
            name="target_type",
        ),
        UniqueConstraint("user_id", "target_type", "target_id", name="uq_follows_target"),
        Index("ix_follows_user_id", "user_id"),
        Index("ix_follows_target", "target_type", "target_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[str] = mapped_column(String(180), nullable=False)
    target_label: Mapped[str | None] = mapped_column(String(240), nullable=True)

    user: Mapped[User] = relationship()


class SearchMatchNotification(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "search_match_notifications"
    __table_args__ = (
        CheckConstraint("status in ('pending', 'delivered', 'dismissed')", name="status"),
        CheckConstraint("match_count > 0", name="match_count_positive"),
        Index("ix_search_match_notifications_user_id", "user_id"),
        Index("ix_search_match_notifications_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    saved_search_id: Mapped[int] = mapped_column(
        ForeignKey("saved_searches.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    match_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    saved_search: Mapped[SavedSearch] = relationship()
    user: Mapped[User] = relationship()


__all__ = [
    "Follow",
    "ListingFavorite",
    "SavedSearch",
    "SearchMatchNotification",
    "SearchQueryLog",
    "WishlistItem",
]

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
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
from oldpages_api.communities.models import Community
from oldpages_api.identity.models import User
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Shelf(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "shelves"
    __table_args__ = (
        CheckConstraint(
            "shelf_type in ("
            "'want_to_read', 'currently_reading', 'finished', 'did_not_finish', 'owned', "
            "'previously_owned', 'available_for_exchange', 'available_for_lending', "
            "'favorites', 'academic_books', 'rare_collection', 'custom')",
            name="shelf_type",
        ),
        CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        UniqueConstraint("user_id", "slug", name="uq_shelves_user_slug"),
        Index("ix_shelves_user_id", "user_id"),
        Index("ix_shelves_visibility", "visibility"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    shelf_type: Mapped[str] = mapped_column(String(40), nullable=False, default="custom")
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    items: Mapped[list[ShelfItem]] = relationship(
        back_populates="shelf",
        cascade="all, delete-orphan",
    )
    user: Mapped[User] = relationship()


class ShelfItem(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "shelf_items"
    __table_args__ = (
        UniqueConstraint("shelf_id", "book_edition_id", name="uq_shelf_items_book"),
        Index("ix_shelf_items_user_id", "user_id"),
        Index("ix_shelf_items_book_edition_id", "book_edition_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shelf_id: Mapped[int] = mapped_column(ForeignKey("shelves.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(ForeignKey("book_editions.id", ondelete="CASCADE"))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    book_edition: Mapped[BookEdition] = relationship()
    shelf: Mapped[Shelf] = relationship(back_populates="items")
    user: Mapped[User] = relationship()


class ReadingProgress(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reading_progress"
    __table_args__ = (
        CheckConstraint(
            "status in ('want_to_read', 'currently_reading', 'finished', 'did_not_finish')",
            name="status",
        ),
        CheckConstraint("current_page is null or current_page >= 0", name="current_page"),
        CheckConstraint(
            "percent_complete is null or (percent_complete >= 0 and percent_complete <= 100)",
            name="percent_complete",
        ),
        CheckConstraint("rating is null or (rating >= 1 and rating <= 5)", name="rating"),
        CheckConstraint("reread_count >= 0", name="reread_count_non_negative"),
        CheckConstraint("total_reading_minutes >= 0", name="total_reading_minutes_non_negative"),
        UniqueConstraint("user_id", "book_edition_id", name="uq_reading_progress_user_book"),
        Index("ix_reading_progress_user_status", "user_id", "status"),
        Index("ix_reading_progress_book_edition_id", "book_edition_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(ForeignKey("book_editions.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="want_to_read")
    current_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percent_complete: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    finished_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_progress_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_reading_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_minutes_json: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    book_edition: Mapped[BookEdition] = relationship()
    notes: Mapped[list[ReadingNote]] = relationship(back_populates="progress")
    user: Mapped[User] = relationship()


class ReadingNote(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reading_notes"
    __table_args__ = (
        CheckConstraint("note_type in ('note', 'highlight', 'quote')", name="note_type"),
        CheckConstraint("visibility in ('private', 'public')", name="visibility"),
        CheckConstraint("page_number is null or page_number >= 0", name="page_number"),
        CheckConstraint(
            "percent_complete is null or (percent_complete >= 0 and percent_complete <= 100)",
            name="percent_complete",
        ),
        UniqueConstraint("user_id", "client_note_id", name="uq_reading_notes_client_note"),
        Index("ix_reading_notes_user_book", "user_id", "book_edition_id"),
        Index("ix_reading_notes_visibility", "visibility"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(ForeignKey("book_editions.id", ondelete="CASCADE"))
    progress_id: Mapped[int | None] = mapped_column(
        ForeignKey("reading_progress.id", ondelete="SET NULL"),
        nullable=True,
    )
    note_type: Mapped[str] = mapped_column(String(24), nullable=False, default="note")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    percent_complete: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    client_note_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    book_edition: Mapped[BookEdition] = relationship()
    progress: Mapped[ReadingProgress | None] = relationship(back_populates="notes")
    user: Mapped[User] = relationship()


class ReadingGoal(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reading_goals"
    __table_args__ = (
        CheckConstraint(
            "goal_type in ("
            "'books_per_year', 'pages_per_month', 'minutes_per_day', 'genre', 'author', "
            "'language', 'community_challenge', 'institution_challenge')",
            name="goal_type",
        ),
        CheckConstraint("scope in ('personal', 'community', 'institution')", name="scope"),
        CheckConstraint("status in ('active', 'completed', 'cancelled')", name="status"),
        CheckConstraint("target_value > 0", name="target_value_positive"),
        CheckConstraint("current_value >= 0", name="current_value_non_negative"),
        Index("ix_reading_goals_user_status", "user_id", "status"),
        Index("ix_reading_goals_community_id", "community_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    community_id: Mapped[int | None] = mapped_column(
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=True,
    )
    goal_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scope: Mapped[str] = mapped_column(String(24), nullable=False, default="personal")
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    target_metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    community: Mapped[Community | None] = relationship()
    user: Mapped[User] = relationship()


class ReadingStatistic(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reading_statistics"
    __table_args__ = (
        CheckConstraint("period_type in ('month', 'year', 'all_time')", name="period_type"),
        CheckConstraint("books_completed >= 0", name="books_completed_non_negative"),
        CheckConstraint("pages_read >= 0", name="pages_read_non_negative"),
        CheckConstraint("minutes_read >= 0", name="minutes_read_non_negative"),
        CheckConstraint("reading_streak_days >= 0", name="reading_streak_days_non_negative"),
        UniqueConstraint(
            "user_id",
            "period_type",
            "period_start",
            "timezone",
            name="uq_reading_statistics_period",
        ),
        Index("ix_reading_statistics_user_period", "user_id", "period_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    period_type: Mapped[str] = mapped_column(String(24), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False)
    books_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pages_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minutes_read: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reading_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    genres_json: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    authors_json: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    monthly_progress_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    year_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[User] = relationship()


__all__ = [
    "ReadingGoal",
    "ReadingNote",
    "ReadingProgress",
    "ReadingStatistic",
    "Shelf",
    "ShelfItem",
]

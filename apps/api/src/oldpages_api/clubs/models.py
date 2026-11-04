from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
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


class BookClub(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_clubs"
    __table_args__ = (
        CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        CheckConstraint("status in ('active', 'archived', 'suspended')", name="status"),
        UniqueConstraint("slug", name="uq_book_clubs_slug"),
        Index("ix_book_clubs_owner_user_id", "owner_user_id"),
        Index("ix_book_clubs_community_id", "community_id"),
        Index("ix_book_clubs_visibility_status", "visibility", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    community_id: Mapped[int | None] = mapped_column(
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="public")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    books: Mapped[list[ClubBook]] = relationship(
        back_populates="club",
        cascade="all, delete-orphan",
    )
    community: Mapped[Community | None] = relationship()
    nominations: Mapped[list[BookNomination]] = relationship(
        back_populates="club",
        cascade="all, delete-orphan",
    )
    owner: Mapped[User] = relationship()


class ClubBook(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "club_books"
    __table_args__ = (
        CheckConstraint("status in ('current', 'next', 'past')", name="status"),
        Index("ix_club_books_club_status", "club_id", "status"),
        Index("ix_club_books_book_edition_id", "book_edition_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("book_clubs.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(
        ForeignKey("book_editions.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="next")
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discussion_guide: Mapped[str | None] = mapped_column(Text, nullable=True)

    book_edition: Mapped[BookEdition] = relationship()
    club: Mapped[BookClub] = relationship(back_populates="books")
    milestones: Mapped[list[ReadingMilestone]] = relationship(
        back_populates="club_book",
        cascade="all, delete-orphan",
    )


class BookNomination(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_nominations"
    __table_args__ = (
        CheckConstraint("status in ('active', 'selected', 'withdrawn')", name="status"),
        UniqueConstraint(
            "club_id",
            "cycle_key",
            "book_edition_id",
            name="uq_book_nominations_cycle_book",
        ),
        Index("ix_book_nominations_club_cycle", "club_id", "cycle_key", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("book_clubs.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(
        ForeignKey("book_editions.id", ondelete="RESTRICT")
    )
    nominator_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    cycle_key: Mapped[str] = mapped_column(String(80), nullable=False, default="default")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")

    book_edition: Mapped[BookEdition] = relationship()
    club: Mapped[BookClub] = relationship(back_populates="nominations")
    nominator: Mapped[User] = relationship()
    votes: Mapped[list[BookVote]] = relationship(
        back_populates="nomination",
        cascade="all, delete-orphan",
    )


class BookVote(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "book_votes"
    __table_args__ = (
        CheckConstraint("rank > 0", name="rank_positive"),
        UniqueConstraint("nomination_id", "voter_user_id", name="uq_book_votes_nomination_voter"),
        UniqueConstraint(
            "club_id",
            "cycle_key",
            "voter_user_id",
            "rank",
            name="uq_book_votes_voter_rank",
        ),
        Index("ix_book_votes_club_cycle", "club_id", "cycle_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("book_clubs.id", ondelete="CASCADE"))
    nomination_id: Mapped[int] = mapped_column(
        ForeignKey("book_nominations.id", ondelete="CASCADE")
    )
    voter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    cycle_key: Mapped[str] = mapped_column(String(80), nullable=False, default="default")
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    club: Mapped[BookClub] = relationship()
    nomination: Mapped[BookNomination] = relationship(back_populates="votes")
    voter: Mapped[User] = relationship()


class ReadingMilestone(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reading_milestones"
    __table_args__ = (
        CheckConstraint(
            "position_type in ('chapter', 'page', 'percent', 'whole_book')",
            name="position_type",
        ),
        CheckConstraint("position_value >= 0", name="position_value_non_negative"),
        Index("ix_reading_milestones_club_book_id", "club_book_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_book_id: Mapped[int] = mapped_column(ForeignKey("club_books.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    position_type: Mapped[str] = mapped_column(String(24), nullable=False)
    position_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discussion_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    club_book: Mapped[ClubBook] = relationship(back_populates="milestones")


class BuddyRead(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "buddy_reads"
    __table_args__ = (
        CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        CheckConstraint("status in ('active', 'completed', 'cancelled')", name="status"),
        CheckConstraint("max_participants > 0", name="max_participants_positive"),
        Index("ix_buddy_reads_book_edition_id", "book_edition_id"),
        Index("ix_buddy_reads_creator_user_id", "creator_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creator_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(
        ForeignKey("book_editions.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="private")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    participant_user_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    progress_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    book_edition: Mapped[BookEdition] = relationship()
    creator: Mapped[User] = relationship()


class Readalong(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "readalongs"
    __table_args__ = (
        CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        CheckConstraint(
            "status in ('scheduled', 'active', 'completed', 'cancelled')",
            name="status",
        ),
        Index("ix_readalongs_book_edition_id", "book_edition_id"),
        Index("ix_readalongs_community_id", "community_id"),
        Index("ix_readalongs_host_user_id", "host_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    community_id: Mapped[int | None] = mapped_column(
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    book_edition_id: Mapped[int] = mapped_column(
        ForeignKey("book_editions.id", ondelete="RESTRICT")
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="public")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False, default="UTC")
    chapter_schedule_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    moderator_user_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    book_edition: Mapped[BookEdition] = relationship()
    community: Mapped[Community | None] = relationship()
    host: Mapped[User] = relationship()


class Event(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "event_type in ("
            "'book_club_meeting', 'book_exchange', 'used_book_fair', 'donation_drive', "
            "'author_meetup', 'signing', 'reading_session', 'silent_reading', "
            "'childrens_story_session', 'library_event', 'college_textbook_sale', "
            "'writing_workshop', 'poetry_reading', 'online_discussion', 'author_interview')",
            name="event_type",
        ),
        CheckConstraint("visibility in ('public', 'private')", name="visibility"),
        CheckConstraint("status in ('scheduled', 'cancelled', 'completed')", name="status"),
        CheckConstraint("capacity is null or capacity > 0", name="capacity_positive"),
        Index("ix_events_starts_at", "starts_at"),
        Index("ix_events_community_id", "community_id"),
        Index("ix_events_club_id", "club_id"),
        Index("ix_events_organizer_user_id", "organizer_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organizer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    community_id: Mapped[int | None] = mapped_column(
        ForeignKey("communities.id", ondelete="SET NULL"),
        nullable=True,
    )
    club_id: Mapped[int | None] = mapped_column(
        ForeignKey("book_clubs.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    visibility: Mapped[str] = mapped_column(String(24), nullable=False, default="public")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="scheduled")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False)
    location_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    online_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checkin_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    checkins: Mapped[list[EventCheckin]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    club: Mapped[BookClub | None] = relationship()
    community: Mapped[Community | None] = relationship()
    organizer: Mapped[User] = relationship()
    rsvps: Mapped[list[EventRSVP]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )
    waitlist_entries: Mapped[list[EventWaitlist]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class EventRSVP(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "event_rsvps"
    __table_args__ = (
        CheckConstraint("status in ('going', 'cancelled', 'waitlisted')", name="status"),
        CheckConstraint("guest_count >= 0", name="guest_count_non_negative"),
        UniqueConstraint("event_id", "user_id", name="uq_event_rsvps_user"),
        Index("ix_event_rsvps_event_status", "event_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="going")
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    event: Mapped[Event] = relationship(back_populates="rsvps")
    user: Mapped[User] = relationship()


class EventWaitlist(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "event_waitlists"
    __table_args__ = (
        CheckConstraint("status in ('waiting', 'promoted', 'cancelled')", name="status"),
        CheckConstraint("position > 0", name="position_positive"),
        CheckConstraint("guest_count >= 0", name="guest_count_non_negative"),
        UniqueConstraint("event_id", "user_id", name="uq_event_waitlists_user"),
        Index("ix_event_waitlists_event_status_position", "event_id", "status", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="waiting")
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    event: Mapped[Event] = relationship(back_populates="waitlist_entries")
    user: Mapped[User] = relationship()


class EventCheckin(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "event_checkins"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_checkins_user"),
        Index("ix_event_checkins_event_id", "event_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    checked_in_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checkin_code: Mapped[str] = mapped_column(String(32), nullable=False)

    checked_in_by: Mapped[User] = relationship(foreign_keys=[checked_in_by_user_id])
    event: Mapped[Event] = relationship(back_populates="checkins")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


__all__ = [
    "BookClub",
    "BookNomination",
    "BookVote",
    "BuddyRead",
    "ClubBook",
    "Event",
    "EventCheckin",
    "EventRSVP",
    "EventWaitlist",
    "Readalong",
    "ReadingMilestone",
]

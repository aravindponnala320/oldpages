from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.catalog.models import BookEdition
from oldpages_api.clubs.models import (
    BookClub,
    BookNomination,
    BookVote,
    BuddyRead,
    ClubBook,
    Event,
    EventCheckin,
    EventRSVP,
    EventWaitlist,
    Readalong,
    ReadingMilestone,
)
from oldpages_api.communities.models import Community, CommunityMember
from oldpages_api.identity.models import User
from oldpages_api.listings.models import Listing
from oldpages_api.listings.repository import listing_load_options


class ClubRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_book_edition_by_public_id(self, public_id: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition).where(BookEdition.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_community_by_public_id(self, public_id: str) -> Community | None:
        result = await self.session.execute(
            select(Community)
            .options(
                selectinload(Community.members).selectinload(CommunityMember.role),
                selectinload(Community.owner),
            )
            .where(Community.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_club_by_public_id(self, public_id: str) -> BookClub | None:
        result = await self.session.execute(
            select(BookClub)
            .execution_options(populate_existing=True)
            .options(*club_load_options())
            .where(BookClub.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_club_by_slug(self, slug: str) -> BookClub | None:
        result = await self.session.execute(
            select(BookClub).options(*club_load_options()).where(BookClub.slug == slug)
        )
        return result.unique().scalar_one_or_none()

    async def list_clubs(
        self,
        *,
        community_id: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[BookClub], str | None]:
        stmt = (
            select(BookClub)
            .options(*club_load_options())
            .where(BookClub.status == "active")
            .order_by(BookClub.created_at.desc(), BookClub.id.desc())
            .limit(limit + 1)
        )
        if community_id:
            community = await self.get_community_by_public_id(community_id)
            if community is None:
                return [], None
            stmt = stmt.where(BookClub.community_id == community.id)
        if cursor:
            cursor_club = await self.get_club_by_public_id(cursor)
            if cursor_club is not None:
                stmt = stmt.where(BookClub.id < cursor_club.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def next_club_book_sequence(self, club_id: int) -> int:
        result = await self.session.execute(
            select(func.max(ClubBook.sequence)).where(ClubBook.club_id == club_id)
        )
        current = result.scalar_one_or_none()
        return int(current or 0) + 1

    async def get_club_book_by_public_id(self, public_id: str) -> ClubBook | None:
        result = await self.session.execute(
            select(ClubBook)
            .execution_options(populate_existing=True)
            .options(*club_book_load_options())
            .where(ClubBook.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_club_books(self, club_id: int) -> list[ClubBook]:
        result = await self.session.execute(
            select(ClubBook)
            .options(*club_book_load_options())
            .where(ClubBook.club_id == club_id)
            .order_by(ClubBook.sequence.asc(), ClubBook.id.asc())
        )
        return list(result.unique().scalars().all())

    async def get_nomination_by_public_id(self, public_id: str) -> BookNomination | None:
        result = await self.session.execute(
            select(BookNomination)
            .options(*nomination_load_options())
            .where(BookNomination.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_nominations(self, club_id: int, cycle_key: str) -> list[BookNomination]:
        result = await self.session.execute(
            select(BookNomination)
            .options(*nomination_load_options())
            .where(
                BookNomination.club_id == club_id,
                BookNomination.cycle_key == cycle_key,
                BookNomination.status == "active",
            )
            .order_by(BookNomination.created_at.asc(), BookNomination.id.asc())
        )
        return list(result.unique().scalars().all())

    async def get_vote(self, nomination_id: int, voter_user_id: int) -> BookVote | None:
        result = await self.session.execute(
            select(BookVote)
            .options(selectinload(BookVote.nomination), selectinload(BookVote.voter))
            .where(
                BookVote.nomination_id == nomination_id,
                BookVote.voter_user_id == voter_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_vote_by_rank(
        self,
        *,
        club_id: int,
        cycle_key: str,
        rank: int,
        voter_user_id: int,
    ) -> BookVote | None:
        result = await self.session.execute(
            select(BookVote).where(
                BookVote.club_id == club_id,
                BookVote.cycle_key == cycle_key,
                BookVote.rank == rank,
                BookVote.voter_user_id == voter_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_active_listings_for_book(
        self,
        book_edition_id: int,
        *,
        limit: int = 6,
    ) -> list[Listing]:
        result = await self.session.execute(
            select(Listing)
            .options(*listing_load_options())
            .where(Listing.book_edition_id == book_edition_id, Listing.status == "active")
            .order_by(Listing.created_at.desc(), Listing.id.desc())
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def list_milestones(self, club_book_id: int) -> list[ReadingMilestone]:
        result = await self.session.execute(
            select(ReadingMilestone)
            .where(ReadingMilestone.club_book_id == club_book_id)
            .order_by(ReadingMilestone.position_value.asc(), ReadingMilestone.id.asc())
        )
        return list(result.scalars().all())

    async def get_buddy_read_by_public_id(self, public_id: str) -> BuddyRead | None:
        result = await self.session.execute(
            select(BuddyRead)
            .execution_options(populate_existing=True)
            .options(selectinload(BuddyRead.book_edition), selectinload(BuddyRead.creator))
            .where(BuddyRead.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_readalong_by_public_id(self, public_id: str) -> Readalong | None:
        result = await self.session.execute(
            select(Readalong)
            .options(
                selectinload(Readalong.book_edition),
                selectinload(Readalong.community),
                selectinload(Readalong.host),
            )
            .where(Readalong.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_event_by_public_id(self, public_id: str) -> Event | None:
        result = await self.session.execute(
            select(Event)
            .execution_options(populate_existing=True)
            .options(*event_load_options())
            .where(Event.public_id == public_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_event_by_public_id_for_update(self, public_id: str) -> Event | None:
        result = await self.session.execute(
            select(Event)
            .execution_options(populate_existing=True)
            .options(*event_load_options())
            .where(Event.public_id == public_id)
            .with_for_update()
        )
        return result.unique().scalar_one_or_none()

    async def list_events(
        self,
        *,
        club_id: str | None,
        community_id: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Event], str | None]:
        stmt = (
            select(Event)
            .options(*event_load_options())
            .where(Event.status == "scheduled")
            .order_by(Event.starts_at.asc(), Event.id.asc())
            .limit(limit + 1)
        )
        if club_id:
            club = await self.get_club_by_public_id(club_id)
            if club is None:
                return [], None
            stmt = stmt.where(Event.club_id == club.id)
        if community_id:
            community = await self.get_community_by_public_id(community_id)
            if community is None:
                return [], None
            stmt = stmt.where(Event.community_id == community.id)
        if cursor:
            cursor_event = await self.get_event_by_public_id(cursor)
            if cursor_event is not None:
                stmt = stmt.where(Event.id > cursor_event.id)
        result = await self.session.execute(stmt)
        rows = list(result.unique().scalars().all())
        next_cursor = rows[-1].public_id if len(rows) > limit else None
        return rows[:limit], next_cursor

    async def get_rsvp(self, event_id: int, user_id: int) -> EventRSVP | None:
        result = await self.session.execute(
            select(EventRSVP)
            .options(selectinload(EventRSVP.user), selectinload(EventRSVP.event))
            .where(EventRSVP.event_id == event_id, EventRSVP.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_waitlist_entry(self, event_id: int, user_id: int) -> EventWaitlist | None:
        result = await self.session.execute(
            select(EventWaitlist)
            .options(selectinload(EventWaitlist.user), selectinload(EventWaitlist.event))
            .where(EventWaitlist.event_id == event_id, EventWaitlist.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_waiting_entries(self, event_id: int) -> list[EventWaitlist]:
        result = await self.session.execute(
            select(EventWaitlist)
            .options(selectinload(EventWaitlist.user), selectinload(EventWaitlist.event))
            .where(EventWaitlist.event_id == event_id, EventWaitlist.status == "waiting")
            .order_by(EventWaitlist.position.asc(), EventWaitlist.id.asc())
        )
        return list(result.scalars().all())

    async def attendee_seat_count(self, event_id: int) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(EventRSVP.guest_count + 1), 0)).where(
                EventRSVP.event_id == event_id,
                EventRSVP.status == "going",
            )
        )
        return int(result.scalar_one())

    async def waitlist_count(self, event_id: int) -> int:
        result = await self.session.execute(
            select(func.count(EventWaitlist.id)).where(
                EventWaitlist.event_id == event_id,
                EventWaitlist.status == "waiting",
            )
        )
        return int(result.scalar_one())

    async def max_waitlist_position(self, event_id: int) -> int:
        result = await self.session.execute(
            select(func.max(EventWaitlist.position)).where(EventWaitlist.event_id == event_id)
        )
        return int(result.scalar_one_or_none() or 0)

    async def get_checkin(self, event_id: int, user_id: int) -> EventCheckin | None:
        result = await self.session.execute(
            select(EventCheckin)
            .options(selectinload(EventCheckin.user), selectinload(EventCheckin.checked_in_by))
            .where(EventCheckin.event_id == event_id, EventCheckin.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()


def club_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(BookClub.books).selectinload(ClubBook.book_edition),
        selectinload(BookClub.community),
        selectinload(BookClub.owner),
    )


def club_book_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(ClubBook.book_edition),
        selectinload(ClubBook.club).selectinload(BookClub.owner),
        selectinload(ClubBook.club).selectinload(BookClub.community),
        selectinload(ClubBook.milestones),
    )


def nomination_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(BookNomination.book_edition),
        selectinload(BookNomination.club).selectinload(BookClub.owner),
        selectinload(BookNomination.nominator),
        selectinload(BookNomination.votes).selectinload(BookVote.voter),
    )


def event_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Event.checkins),
        selectinload(Event.club).selectinload(BookClub.owner),
        selectinload(Event.community),
        selectinload(Event.organizer),
        selectinload(Event.rsvps).selectinload(EventRSVP.user),
        selectinload(Event.waitlist_entries).selectinload(EventWaitlist.user),
    )


__all__ = ["ClubRepository"]

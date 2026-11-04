from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.clubs.events import (
    BOOK_CLUB_BOOK_SELECTED,
    BOOK_CLUB_CREATED,
    BOOK_NOMINATION_CREATED,
    BOOK_VOTE_CAST,
    BUDDY_READ_CREATED,
    BUDDY_READ_JOINED,
    EVENT_CHECKIN_CREATED,
    EVENT_CREATED,
    EVENT_RSVP_CREATED,
    EVENT_WAITLIST_PROMOTED,
    READALONG_CREATED,
    READING_MILESTONE_CREATED,
)
from oldpages_api.clubs.exceptions import (
    BuddyReadNotFoundError,
    ClubBookNotFoundError,
    ClubNotFoundError,
    ClubValidationError,
    EventNotFoundError,
    ForbiddenClubActionError,
    InvalidClubStateTransitionError,
)
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
from oldpages_api.clubs.repository import ClubRepository
from oldpages_api.clubs.schemas import (
    BookClubCreateRequest,
    BookClubListResponse,
    BookClubResponse,
    BookClubStatus,
    BookNominationCreateRequest,
    BookNominationResponse,
    BookNominationStatus,
    BookVoteRequest,
    BookVoteResponse,
    BuddyReadCreateRequest,
    BuddyReadProgressRequest,
    BuddyReadResponse,
    BuddyReadStatus,
    ClubBookCreateRequest,
    ClubBookListResponse,
    ClubBookResponse,
    ClubBookStatus,
    ClubBookSummary,
    ClubUserSummary,
    ClubVisibility,
    EventCheckinRequest,
    EventCheckinResponse,
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventRSVPRequest,
    EventRSVPResponse,
    EventRSVPStatus,
    EventStatus,
    EventType,
    EventUpdateRequest,
    MilestonePositionType,
    ReadalongCreateRequest,
    ReadalongResponse,
    ReadalongStatus,
    ReadingMilestoneCreateRequest,
    ReadingMilestoneListResponse,
    ReadingMilestoneResponse,
    SelectClubBookRequest,
)
from oldpages_api.communities.permissions import require_active_member
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.service import listing_response
from oldpages_api.shared.db.ids import new_ulid

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


class ClubService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ClubRepository(session)

    async def create_club(
        self,
        payload: BookClubCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BookClubResponse:
        community_id = None
        if payload.community_id:
            community = await self.repo.get_community_by_public_id(payload.community_id)
            if community is None:
                raise ClubValidationError("Community was not found.")
            require_active_member(actor, community)
            community_id = community.id
        slug = slugify(payload.slug or payload.name)
        existing = await self.repo.get_club_by_slug(slug)
        if existing is not None:
            raise ClubValidationError("Book club slug is already in use.")
        club = BookClub(
            community_id=community_id,
            description=payload.description,
            name=payload.name,
            owner_user_id=actor.id,
            settings_json=payload.settings,
            slug=slug,
            timezone=payload.timezone,
            visibility=payload.visibility,
        )
        self.repo.add(club)
        await self.repo.flush()
        await self.audit(
            action=BOOK_CLUB_CREATED,
            actor=actor,
            context=context,
            payload={"club_id": club.public_id, "visibility": club.visibility},
        )
        await self.repo.commit()
        reloaded = await self.get_club_model(club.public_id)
        return book_club_response(reloaded, actor)

    async def list_clubs(
        self,
        *,
        community_id: str | None,
        cursor: str | None,
        limit: int,
        viewer: User | None,
    ) -> BookClubListResponse:
        clubs, next_cursor = await self.repo.list_clubs(
            community_id=community_id,
            cursor=cursor,
            limit=limit,
        )
        visible = [club for club in clubs if can_view_club(club, viewer)]
        return BookClubListResponse(
            items=[book_club_response(club, viewer) for club in visible],
            next_cursor=next_cursor,
        )

    async def get_club(self, club_id: str, viewer: User | None) -> BookClubResponse:
        club = await self.get_club_model(club_id)
        require_can_view_club(club, viewer)
        return book_club_response(club, viewer)

    async def add_club_book(
        self,
        club_id: str,
        payload: ClubBookCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ClubBookResponse:
        club = await self.get_club_model(club_id)
        require_club_owner(club, actor)
        book = await self.repo.get_book_edition_by_public_id(payload.book_id)
        if book is None:
            raise ClubValidationError("Book was not found.")
        club_book = ClubBook(
            book_edition_id=book.id,
            club_id=club.id,
            discussion_guide=payload.discussion_guide,
            end_date=payload.end_date,
            sequence=await self.repo.next_club_book_sequence(club.id),
            start_date=payload.start_date,
            status=payload.status,
            selected_at=utc_now(),
        )
        self.repo.add(club_book)
        await self.repo.flush()
        await self.audit(
            action=BOOK_CLUB_BOOK_SELECTED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "club_id": club.public_id},
        )
        await self.repo.commit()
        reloaded = await self.get_club_book_model(club_book.public_id)
        return await self.club_book_response(reloaded)

    async def list_club_books(
        self,
        club_id: str,
        viewer: User | None,
    ) -> ClubBookListResponse:
        club = await self.get_club_model(club_id)
        require_can_view_club(club, viewer)
        books = await self.repo.list_club_books(club.id)
        return ClubBookListResponse(
            items=[await self.club_book_response(club_book) for club_book in books]
        )

    async def create_nomination(
        self,
        club_id: str,
        payload: BookNominationCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BookNominationResponse:
        club = await self.get_club_model(club_id)
        require_can_participate(club, actor)
        book = await self.repo.get_book_edition_by_public_id(payload.book_id)
        if book is None:
            raise ClubValidationError("Book was not found.")
        nomination = BookNomination(
            book_edition_id=book.id,
            club_id=club.id,
            cycle_key=payload.cycle_key,
            nominator_user_id=actor.id,
            note=payload.note,
        )
        self.repo.add(nomination)
        await self.repo.flush()
        await self.audit(
            action=BOOK_NOMINATION_CREATED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "club_id": club.public_id},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_nomination_by_public_id(nomination.public_id)
        if reloaded is None:
            raise ClubValidationError("Nomination could not be created.")
        return nomination_response(reloaded)

    async def cast_vote(
        self,
        club_id: str,
        payload: BookVoteRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BookVoteResponse:
        club = await self.get_club_model(club_id)
        require_can_participate(club, actor)
        nomination = await self.repo.get_nomination_by_public_id(payload.nomination_id)
        if (
            nomination is None
            or nomination.club_id != club.id
            or nomination.cycle_key != payload.cycle_key
        ):
            raise ClubValidationError("Nomination was not found for this club cycle.")
        existing_rank = await self.repo.get_vote_by_rank(
            club_id=club.id,
            cycle_key=payload.cycle_key,
            rank=payload.rank,
            voter_user_id=actor.id,
        )
        existing_vote = await self.repo.get_vote(nomination.id, actor.id)
        if existing_rank is not None and existing_rank.nomination_id != nomination.id:
            raise ClubValidationError("A voter can assign each rank only once per cycle.")
        if existing_vote is None:
            vote = BookVote(
                club_id=club.id,
                cycle_key=payload.cycle_key,
                nomination_id=nomination.id,
                rank=payload.rank,
                voter_user_id=actor.id,
            )
            self.repo.add(vote)
        else:
            vote = existing_vote
            vote.rank = payload.rank
        await self.repo.flush()
        await self.audit(
            action=BOOK_VOTE_CAST,
            actor=actor,
            context=context,
            payload={"club_id": club.public_id, "nomination_id": nomination.public_id},
        )
        await self.repo.commit()
        return BookVoteResponse(
            cycle_key=vote.cycle_key,
            id=vote.public_id,
            nomination_id=nomination.public_id,
            rank=vote.rank,
            voter=ClubUserSummary(id=actor.public_id),
        )

    async def select_book(
        self,
        club_id: str,
        payload: SelectClubBookRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ClubBookResponse:
        club = await self.get_club_model(club_id)
        require_club_owner(club, actor)
        nominations = await self.repo.list_nominations(club.id, payload.cycle_key)
        if not nominations:
            raise ClubValidationError("No active nominations exist for this cycle.")
        winner = select_deterministic_winner(nominations)
        winner.status = "selected"
        club_book = ClubBook(
            book_edition_id=winner.book_edition_id,
            club_id=club.id,
            end_date=payload.end_date,
            sequence=await self.repo.next_club_book_sequence(club.id),
            start_date=payload.start_date,
            status=payload.status,
            selected_at=utc_now(),
        )
        self.repo.add(club_book)
        await self.repo.flush()
        await self.audit(
            action=BOOK_CLUB_BOOK_SELECTED,
            actor=actor,
            context=context,
            payload={
                "book_id": winner.book_edition.public_id,
                "club_id": club.public_id,
                "cycle_key": payload.cycle_key,
                "nomination_id": winner.public_id,
            },
        )
        await self.repo.commit()
        reloaded = await self.get_club_book_model(club_book.public_id)
        return await self.club_book_response(reloaded)

    async def create_milestone(
        self,
        club_book_id: str,
        payload: ReadingMilestoneCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReadingMilestoneResponse:
        club_book = await self.get_club_book_model(club_book_id)
        require_club_owner(club_book.club, actor)
        milestone = ReadingMilestone(
            club_book_id=club_book.id,
            discussion_prompt=payload.discussion_prompt,
            ends_at=payload.ends_at,
            position_type=payload.position_type,
            position_value=payload.position_value,
            starts_at=payload.starts_at,
            title=payload.title,
        )
        self.repo.add(milestone)
        await self.repo.flush()
        await self.audit(
            action=READING_MILESTONE_CREATED,
            actor=actor,
            context=context,
            payload={"club_book_id": club_book.public_id},
        )
        await self.repo.commit()
        return milestone_response(
            milestone, progress_type=None, progress_value=None, finished=False
        )

    async def list_milestones(
        self,
        club_book_id: str,
        *,
        finished: bool,
        progress_type: str | None,
        progress_value: int | None,
        viewer: User | None,
    ) -> ReadingMilestoneListResponse:
        club_book = await self.get_club_book_model(club_book_id)
        require_can_view_club(club_book.club, viewer)
        milestones = await self.repo.list_milestones(club_book.id)
        return ReadingMilestoneListResponse(
            items=[
                milestone_response(
                    milestone,
                    progress_type=progress_type,
                    progress_value=progress_value,
                    finished=finished,
                )
                for milestone in milestones
            ]
        )

    async def create_buddy_read(
        self,
        payload: BuddyReadCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BuddyReadResponse:
        book = await self.repo.get_book_edition_by_public_id(payload.book_id)
        if book is None:
            raise ClubValidationError("Book was not found.")
        buddy_read = BuddyRead(
            book_edition_id=book.id,
            creator_user_id=actor.id,
            deadline_at=payload.deadline_at,
            max_participants=payload.max_participants,
            participant_user_ids_json=[actor.public_id],
            progress_json={},
            title=payload.title,
            visibility=payload.visibility,
        )
        self.repo.add(buddy_read)
        await self.repo.flush()
        await self.audit(
            action=BUDDY_READ_CREATED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "buddy_read_id": buddy_read.public_id},
        )
        await self.repo.commit()
        reloaded = await self.get_buddy_read_model(buddy_read.public_id)
        return buddy_read_response(reloaded)

    async def join_buddy_read(
        self,
        buddy_read_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> BuddyReadResponse:
        buddy_read = await self.get_buddy_read_model(buddy_read_id)
        participants = list(buddy_read.participant_user_ids_json)
        if actor.public_id not in participants:
            if len(participants) >= buddy_read.max_participants:
                raise InvalidClubStateTransitionError("Buddy read is already full.")
            participants.append(actor.public_id)
            buddy_read.participant_user_ids_json = participants
        await self.audit(
            action=BUDDY_READ_JOINED,
            actor=actor,
            context=context,
            payload={"buddy_read_id": buddy_read.public_id},
        )
        await self.repo.commit()
        reloaded = await self.get_buddy_read_model(buddy_read.public_id)
        return buddy_read_response(reloaded)

    async def update_buddy_read_progress(
        self,
        buddy_read_id: str,
        payload: BuddyReadProgressRequest,
        actor: User,
    ) -> BuddyReadResponse:
        buddy_read = await self.get_buddy_read_model(buddy_read_id)
        if actor.public_id not in buddy_read.participant_user_ids_json:
            raise ForbiddenClubActionError("Only participants can update buddy-read progress.")
        progress = dict(buddy_read.progress_json)
        progress[actor.public_id] = {
            "position_type": payload.position_type,
            "position_value": payload.position_value,
            "updated_at": utc_now().isoformat(),
        }
        buddy_read.progress_json = progress
        await self.repo.commit()
        reloaded = await self.get_buddy_read_model(buddy_read.public_id)
        return buddy_read_response(reloaded)

    async def create_readalong(
        self,
        payload: ReadalongCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ReadalongResponse:
        book = await self.repo.get_book_edition_by_public_id(payload.book_id)
        if book is None:
            raise ClubValidationError("Book was not found.")
        community_id = None
        if payload.community_id:
            community = await self.repo.get_community_by_public_id(payload.community_id)
            if community is None:
                raise ClubValidationError("Community was not found.")
            require_active_member(actor, community)
            community_id = community.id
        readalong = Readalong(
            book_edition_id=book.id,
            chapter_schedule_json=payload.chapter_schedule,
            community_id=community_id,
            description=payload.description,
            ends_at=payload.ends_at,
            host_user_id=actor.id,
            moderator_user_ids_json=[actor.public_id],
            starts_at=payload.starts_at,
            timezone=payload.timezone,
            title=payload.title,
            visibility=payload.visibility,
        )
        self.repo.add(readalong)
        await self.repo.flush()
        await self.audit(
            action=READALONG_CREATED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id, "readalong_id": readalong.public_id},
        )
        await self.repo.commit()
        reloaded = await self.repo.get_readalong_by_public_id(readalong.public_id)
        if reloaded is None:
            raise ClubValidationError("Readalong could not be created.")
        return readalong_response(reloaded)

    async def create_event(
        self,
        payload: EventCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> EventResponse:
        community_id = None
        club_id = None
        if payload.community_id:
            community = await self.repo.get_community_by_public_id(payload.community_id)
            if community is None:
                raise ClubValidationError("Community was not found.")
            require_active_member(actor, community)
            community_id = community.id
        if payload.club_id:
            club = await self.get_club_model(payload.club_id)
            require_club_owner(club, actor)
            club_id = club.id
        event = Event(
            address=payload.address,
            capacity=payload.capacity,
            checkin_code=new_ulid()[:12],
            club_id=club_id,
            community_id=community_id,
            description=payload.description,
            ends_at=payload.ends_at,
            event_type=payload.event_type,
            location_name=payload.location_name,
            metadata_json=payload.metadata,
            online_url=payload.online_url,
            organizer_user_id=actor.id,
            starts_at=payload.starts_at,
            timezone=payload.timezone,
            title=payload.title,
            visibility=payload.visibility,
        )
        self.repo.add(event)
        await self.repo.flush()
        await self.audit(
            action=EVENT_CREATED,
            actor=actor,
            context=context,
            payload={"event_id": event.public_id, "event_type": event.event_type},
        )
        await self.repo.commit()
        reloaded = await self.get_event_model(event.public_id)
        return await self.event_response(reloaded, actor)

    async def list_events(
        self,
        *,
        club_id: str | None,
        community_id: str | None,
        cursor: str | None,
        limit: int,
        viewer: User | None,
    ) -> EventListResponse:
        events, next_cursor = await self.repo.list_events(
            club_id=club_id,
            community_id=community_id,
            cursor=cursor,
            limit=limit,
        )
        visible = [event for event in events if can_view_event(event, viewer)]
        return EventListResponse(
            items=[await self.event_response(event, viewer) for event in visible],
            next_cursor=next_cursor,
        )

    async def get_event(self, event_id: str, viewer: User | None) -> EventResponse:
        event = await self.get_event_model(event_id)
        require_can_view_event(event, viewer)
        return await self.event_response(event, viewer)

    async def update_event(
        self,
        event_id: str,
        payload: EventUpdateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> EventResponse:
        event = await self.get_event_model(event_id, for_update=True)
        require_event_organizer(event, actor)
        if payload.title is not None:
            event.title = payload.title
        if payload.description is not None:
            event.description = payload.description
        if payload.location_name is not None:
            event.location_name = payload.location_name
        if payload.online_url is not None:
            event.online_url = payload.online_url
        if payload.status is not None:
            event.status = payload.status
        if payload.starts_at is not None:
            event.starts_at = payload.starts_at
        if payload.ends_at is not None:
            event.ends_at = payload.ends_at
        if event.ends_at <= event.starts_at:
            raise ClubValidationError("Event ends_at must be after starts_at.")
        if payload.timezone is not None:
            event.timezone = payload.timezone
        if "capacity" in payload.model_fields_set:
            event.capacity = payload.capacity
            await self.promote_waitlist(event, actor, context)
        await self.repo.commit()
        reloaded = await self.get_event_model(event.public_id)
        return await self.event_response(reloaded, actor)

    async def create_rsvp(
        self,
        event_id: str,
        payload: EventRSVPRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> EventRSVPResponse:
        event = await self.get_event_model(event_id, for_update=True)
        require_can_view_event(event, actor)
        existing = await self.repo.get_rsvp(event.id, actor.id)
        if existing is not None and existing.status == "going":
            return await self.rsvp_response(existing)
        if await self.has_capacity_for(event, payload.guest_count):
            if existing is None:
                rsvp = EventRSVP(
                    event_id=event.id,
                    guest_count=payload.guest_count,
                    note=payload.note,
                    status="going",
                    user_id=actor.id,
                )
                self.repo.add(rsvp)
            else:
                rsvp = existing
                rsvp.guest_count = payload.guest_count
                rsvp.note = payload.note
                rsvp.status = "going"
            waitlist = await self.repo.get_waitlist_entry(event.id, actor.id)
            if waitlist is not None and waitlist.status == "waiting":
                waitlist.status = "promoted"
            await self.audit(
                action=EVENT_RSVP_CREATED,
                actor=actor,
                context=context,
                payload={"event_id": event.public_id, "status": "going"},
            )
            await self.repo.commit()
            return await self.get_rsvp_response(event.id, actor.id)

        rsvp = existing or EventRSVP(
            event_id=event.id,
            guest_count=payload.guest_count,
            note=payload.note,
            status="waitlisted",
            user_id=actor.id,
        )
        rsvp.guest_count = payload.guest_count
        rsvp.note = payload.note
        rsvp.status = "waitlisted"
        if existing is None:
            self.repo.add(rsvp)
        waitlist = await self.repo.get_waitlist_entry(event.id, actor.id)
        if waitlist is None:
            waitlist = EventWaitlist(
                event_id=event.id,
                guest_count=payload.guest_count,
                position=await self.repo.max_waitlist_position(event.id) + 1,
                status="waiting",
                user_id=actor.id,
            )
            self.repo.add(waitlist)
        else:
            waitlist.guest_count = payload.guest_count
            if waitlist.status != "waiting":
                waitlist.position = await self.repo.max_waitlist_position(event.id) + 1
            waitlist.status = "waiting"
        await self.audit(
            action=EVENT_RSVP_CREATED,
            actor=actor,
            context=context,
            payload={"event_id": event.public_id, "status": "waitlisted"},
        )
        await self.repo.commit()
        return await self.get_rsvp_response(event.id, actor.id)

    async def cancel_rsvp(
        self,
        event_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> EventRSVPResponse:
        event = await self.get_event_model(event_id, for_update=True)
        rsvp = await self.repo.get_rsvp(event.id, actor.id)
        if rsvp is None:
            raise ClubValidationError("RSVP was not found.")
        rsvp.status = "cancelled"
        waitlist = await self.repo.get_waitlist_entry(event.id, actor.id)
        if waitlist is not None and waitlist.status == "waiting":
            waitlist.status = "cancelled"
        await self.promote_waitlist(event, actor, context)
        await self.repo.commit()
        return await self.get_rsvp_response(event.id, actor.id)

    async def create_checkin(
        self,
        event_id: str,
        payload: EventCheckinRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> EventCheckinResponse:
        event = await self.get_event_model(event_id)
        require_event_organizer(event, actor)
        if payload.checkin_code != event.checkin_code:
            raise ForbiddenClubActionError("Event check-in code is invalid.")
        attendee = await self.repo.get_user_by_public_id(payload.user_id)
        if attendee is None:
            raise ClubValidationError("Check-in user was not found.")
        rsvp = await self.repo.get_rsvp(event.id, attendee.id)
        if rsvp is None or rsvp.status != "going":
            raise ClubValidationError("Only confirmed RSVPs can be checked in.")
        checkin = await self.repo.get_checkin(event.id, attendee.id)
        if checkin is None:
            checkin = EventCheckin(
                checked_in_at=utc_now(),
                checked_in_by_user_id=actor.id,
                checkin_code=payload.checkin_code,
                event_id=event.id,
                user_id=attendee.id,
            )
            self.repo.add(checkin)
            await self.repo.flush()
        await self.audit(
            action=EVENT_CHECKIN_CREATED,
            actor=actor,
            context=context,
            payload={"event_id": event.public_id, "user_id": attendee.public_id},
        )
        await self.repo.commit()
        return EventCheckinResponse(
            checked_in_at=checkin.checked_in_at,
            checked_in_by_user_id=actor.public_id,
            event_id=event.public_id,
            id=checkin.public_id,
            user_id=attendee.public_id,
        )

    async def calendar_export(self, event_id: str, viewer: User | None) -> str:
        event = await self.get_event_model(event_id)
        require_can_view_event(event, viewer)
        return event_ics(event)

    async def has_capacity_for(self, event: Event, guest_count: int) -> bool:
        if event.capacity is None:
            return True
        used = await self.repo.attendee_seat_count(event.id)
        return used + guest_count + 1 <= event.capacity

    async def promote_waitlist(
        self,
        event: Event,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        if event.capacity is None:
            capacity_remaining = 1_000_000_000
        else:
            capacity_remaining = event.capacity - await self.repo.attendee_seat_count(event.id)
        if capacity_remaining <= 0:
            return
        waiting_entries = await self.repo.list_waiting_entries(event.id)
        for entry in waiting_entries:
            seats = entry.guest_count + 1
            if seats > capacity_remaining:
                continue
            rsvp = await self.repo.get_rsvp(event.id, entry.user_id)
            if rsvp is None:
                rsvp = EventRSVP(
                    event_id=event.id,
                    guest_count=entry.guest_count,
                    status="going",
                    user_id=entry.user_id,
                )
                self.repo.add(rsvp)
            else:
                rsvp.guest_count = entry.guest_count
                rsvp.status = "going"
            entry.status = "promoted"
            capacity_remaining -= seats
            await self.audit(
                action=EVENT_WAITLIST_PROMOTED,
                actor=actor,
                context=context,
                payload={"event_id": event.public_id, "user_id": entry.user.public_id},
            )
        await self.reorder_waitlist(event.id)

    async def reorder_waitlist(self, event_id: int) -> None:
        waiting = await self.repo.list_waiting_entries(event_id)
        for index, entry in enumerate(waiting, start=1):
            entry.position = index

    async def club_book_response(self, club_book: ClubBook) -> ClubBookResponse:
        listings = await self.repo.list_active_listings_for_book(club_book.book_edition_id)
        return ClubBookResponse(
            available_listings=[listing_response(listing) for listing in listings],
            book=ClubBookSummary(
                id=club_book.book_edition.public_id,
                title=club_book.book_edition.title,
            ),
            discussion_guide=club_book.discussion_guide,
            end_date=club_book.end_date,
            id=club_book.public_id,
            selected_at=club_book.selected_at,
            sequence=club_book.sequence,
            start_date=club_book.start_date,
            status=cast("ClubBookStatus", club_book.status),
        )

    async def event_response(self, event: Event, viewer: User | None) -> EventResponse:
        is_organizer = viewer is not None and viewer.id == event.organizer_user_id
        return EventResponse(
            capacity=event.capacity,
            checkin_code=event.checkin_code if is_organizer else None,
            club_id=event.club.public_id if event.club else None,
            community_id=event.community.public_id if event.community else None,
            description=event.description,
            ends_at=event.ends_at,
            event_type=cast("EventType", event.event_type),
            id=event.public_id,
            location_name=event.location_name,
            online_url=event.online_url,
            organizer=ClubUserSummary(id=event.organizer.public_id),
            rsvp_count=len([rsvp for rsvp in event.rsvps if rsvp.status == "going"]),
            starts_at=event.starts_at,
            status=cast("EventStatus", event.status),
            timezone=event.timezone,
            title=event.title,
            visibility=cast("ClubVisibility", event.visibility),
            waitlist_count=len(
                [entry for entry in event.waitlist_entries if entry.status == "waiting"]
            ),
        )

    async def rsvp_response(self, rsvp: EventRSVP) -> EventRSVPResponse:
        waitlist = await self.repo.get_waitlist_entry(rsvp.event_id, rsvp.user_id)
        return EventRSVPResponse(
            event_id=rsvp.event.public_id,
            guest_count=rsvp.guest_count,
            id=rsvp.public_id,
            status=cast("EventRSVPStatus", rsvp.status),
            user=ClubUserSummary(id=rsvp.user.public_id),
            waitlist_position=waitlist.position
            if waitlist is not None and waitlist.status == "waiting"
            else None,
        )

    async def get_rsvp_response(self, event_id: int, user_id: int) -> EventRSVPResponse:
        rsvp = await self.repo.get_rsvp(event_id, user_id)
        if rsvp is None:
            raise ClubValidationError("RSVP was not found.")
        return await self.rsvp_response(rsvp)

    async def get_club_model(self, club_id: str) -> BookClub:
        club = await self.repo.get_club_by_public_id(club_id)
        if club is None:
            raise ClubNotFoundError()
        return club

    async def get_club_book_model(self, club_book_id: str) -> ClubBook:
        club_book = await self.repo.get_club_book_by_public_id(club_book_id)
        if club_book is None:
            raise ClubBookNotFoundError()
        return club_book

    async def get_buddy_read_model(self, buddy_read_id: str) -> BuddyRead:
        buddy_read = await self.repo.get_buddy_read_by_public_id(buddy_read_id)
        if buddy_read is None:
            raise BuddyReadNotFoundError()
        return buddy_read

    async def get_event_model(self, event_id: str, *, for_update: bool = False) -> Event:
        event = (
            await self.repo.get_event_by_public_id_for_update(event_id)
            if for_update
            else await self.repo.get_event_by_public_id(event_id)
        )
        if event is None:
            raise EventNotFoundError()
        return event

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, Any],
    ) -> None:
        self.repo.add(
            AuditLog(
                action=action,
                actor_user_id=actor.id,
                context_json=payload,
                ip_address=context.ip_address,
                target_user_id=None,
                user_agent=context.user_agent,
            )
        )


def can_view_club(club: BookClub, viewer: User | None) -> bool:
    if club.visibility == "public":
        return True
    return viewer is not None and club.owner_user_id == viewer.id


def require_can_view_club(club: BookClub, viewer: User | None) -> None:
    if not can_view_club(club, viewer):
        raise ForbiddenClubActionError("This book club is private.")


def require_can_participate(club: BookClub, actor: User) -> None:
    if club.visibility == "private" and club.owner_user_id != actor.id:
        raise ForbiddenClubActionError("This book club is private.")


def require_club_owner(club: BookClub, actor: User) -> None:
    if club.owner_user_id != actor.id:
        raise ForbiddenClubActionError("Only the club owner can perform this action.")


def can_view_event(event: Event, viewer: User | None) -> bool:
    if event.visibility == "public":
        return True
    return viewer is not None and event.organizer_user_id == viewer.id


def require_can_view_event(event: Event, viewer: User | None) -> None:
    if not can_view_event(event, viewer):
        raise ForbiddenClubActionError("This event is private.")


def require_event_organizer(event: Event, actor: User) -> None:
    if event.organizer_user_id != actor.id:
        raise ForbiddenClubActionError("Only the event organizer can perform this action.")


def select_deterministic_winner(nominations: list[BookNomination]) -> BookNomination:
    totals: dict[int, int] = defaultdict(int)
    counts: dict[int, int] = defaultdict(int)
    for nomination in nominations:
        for vote in nomination.votes:
            totals[nomination.id] += vote.rank
            counts[nomination.id] += 1
    return sorted(
        nominations,
        key=lambda nomination: (
            counts[nomination.id] == 0,
            totals[nomination.id] if counts[nomination.id] else 1_000_000,
            -counts[nomination.id],
            nomination.created_at,
            nomination.id,
        ),
    )[0]


def book_club_response(club: BookClub, viewer: User | None) -> BookClubResponse:
    current = next((item for item in club.books if item.status == "current"), None)
    next_book = next((item for item in club.books if item.status == "next"), None)
    return BookClubResponse(
        community_id=club.community.public_id if club.community else None,
        current_book=club_book_summary(current),
        description=club.description,
        id=club.public_id,
        member_context="owner" if viewer is not None and viewer.id == club.owner_user_id else None,
        name=club.name,
        next_book=club_book_summary(next_book),
        owner=ClubUserSummary(id=club.owner.public_id),
        slug=club.slug,
        status=cast("BookClubStatus", club.status),
        timezone=club.timezone,
        visibility=cast("ClubVisibility", club.visibility),
    )


def club_book_summary(club_book: ClubBook | None) -> ClubBookSummary | None:
    if club_book is None:
        return None
    return ClubBookSummary(
        id=club_book.book_edition.public_id,
        title=club_book.book_edition.title,
    )


def nomination_response(nomination: BookNomination) -> BookNominationResponse:
    return BookNominationResponse(
        book=ClubBookSummary(
            id=nomination.book_edition.public_id,
            title=nomination.book_edition.title,
        ),
        cycle_key=nomination.cycle_key,
        id=nomination.public_id,
        note=nomination.note,
        nominator=ClubUserSummary(id=nomination.nominator.public_id),
        status=cast("BookNominationStatus", nomination.status),
        vote_count=len(nomination.votes),
    )


def milestone_response(
    milestone: ReadingMilestone,
    *,
    finished: bool,
    progress_type: str | None,
    progress_value: int | None,
) -> ReadingMilestoneResponse:
    locked = spoiler_locked(
        milestone,
        finished=finished,
        progress_type=progress_type,
        progress_value=progress_value,
    )
    return ReadingMilestoneResponse(
        discussion_prompt=None if locked else milestone.discussion_prompt,
        ends_at=milestone.ends_at,
        id=milestone.public_id,
        position_type=cast("MilestonePositionType", milestone.position_type),
        position_value=milestone.position_value,
        spoiler_locked=locked,
        starts_at=milestone.starts_at,
        title=milestone.title,
    )


def spoiler_locked(
    milestone: ReadingMilestone,
    *,
    finished: bool,
    progress_type: str | None,
    progress_value: int | None,
) -> bool:
    if milestone.position_type == "whole_book":
        return not finished
    if progress_type != milestone.position_type or progress_value is None:
        return True
    return progress_value < milestone.position_value


def buddy_read_response(buddy_read: BuddyRead) -> BuddyReadResponse:
    return BuddyReadResponse(
        book=ClubBookSummary(
            id=buddy_read.book_edition.public_id,
            title=buddy_read.book_edition.title,
        ),
        deadline_at=buddy_read.deadline_at,
        id=buddy_read.public_id,
        max_participants=buddy_read.max_participants,
        participant_user_ids=buddy_read.participant_user_ids_json,
        progress=buddy_read.progress_json,
        status=cast("BuddyReadStatus", buddy_read.status),
        title=buddy_read.title,
        visibility=cast("ClubVisibility", buddy_read.visibility),
    )


def readalong_response(readalong: Readalong) -> ReadalongResponse:
    return ReadalongResponse(
        book=ClubBookSummary(
            id=readalong.book_edition.public_id,
            title=readalong.book_edition.title,
        ),
        chapter_schedule=readalong.chapter_schedule_json,
        community_id=readalong.community.public_id if readalong.community else None,
        description=readalong.description,
        ends_at=readalong.ends_at,
        host=ClubUserSummary(id=readalong.host.public_id),
        id=readalong.public_id,
        starts_at=readalong.starts_at,
        status=cast("ReadalongStatus", readalong.status),
        timezone=readalong.timezone,
        title=readalong.title,
        visibility=cast("ClubVisibility", readalong.visibility),
    )


def event_ics(event: Event) -> str:
    timezone = ZoneInfo(event.timezone)
    starts_at = event_datetime_in_zone(event.starts_at, timezone)
    ends_at = event_datetime_in_zone(event.ends_at, timezone)
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    dtstart = starts_at.strftime("%Y%m%dT%H%M%S")
    dtend = ends_at.strftime("%Y%m%dT%H%M%S")
    escaped_title = escape_ics_text(event.title)
    escaped_description = escape_ics_text(event.description or "")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//OldPages//Clubs Events//EN",
        "BEGIN:VEVENT",
        f"UID:{event.public_id}@oldpages.in",
        f"DTSTAMP:{stamp}",
        f"DTSTART;TZID={event.timezone}:{dtstart}",
        f"DTEND;TZID={event.timezone}:{dtend}",
        f"SUMMARY:{escaped_title}",
        f"DESCRIPTION:{escaped_description}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def event_datetime_in_zone(value: Any, timezone: ZoneInfo) -> Any:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone)
    return value.astimezone(timezone)


def escape_ics_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def slugify(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not slug:
        raise ClubValidationError("Slug cannot be empty.")
    return slug[:180]

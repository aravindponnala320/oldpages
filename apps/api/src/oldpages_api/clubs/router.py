from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.clubs.schemas import (
    BookClubCreateRequest,
    BookClubListResponse,
    BookClubResponse,
    BookNominationCreateRequest,
    BookNominationResponse,
    BookVoteRequest,
    BookVoteResponse,
    BuddyReadCreateRequest,
    BuddyReadProgressRequest,
    BuddyReadResponse,
    ClubBookCreateRequest,
    ClubBookListResponse,
    ClubBookResponse,
    EventCheckinRequest,
    EventCheckinResponse,
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventRSVPRequest,
    EventRSVPResponse,
    EventUpdateRequest,
    ReadalongCreateRequest,
    ReadalongResponse,
    ReadingMilestoneCreateRequest,
    ReadingMilestoneListResponse,
    ReadingMilestoneResponse,
    SelectClubBookRequest,
)
from oldpages_api.clubs.service import ClubService
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    get_optional_principal,
    request_context,
)
from oldpages_api.shared.db.database import get_session

clubs_router = APIRouter(prefix="/clubs", tags=["clubs"])
club_books_router = APIRouter(prefix="/club-books", tags=["club books"])
buddy_reads_router = APIRouter(prefix="/buddy-reads", tags=["buddy reads"])
readalongs_router = APIRouter(prefix="/readalongs", tags=["readalongs"])
events_router = APIRouter(prefix="/events", tags=["events"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
OptionalPrincipalDep = Annotated[CurrentPrincipal | None, Depends(get_optional_principal)]


def club_service(session: AsyncSession) -> ClubService:
    return ClubService(session)


@clubs_router.post("", response_model=BookClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club(
    payload: BookClubCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BookClubResponse:
    return await club_service(session).create_club(
        payload,
        principal.user,
        request_context(request),
    )


@clubs_router.get("", response_model=BookClubListResponse)
async def list_clubs(
    session: SessionDep,
    principal: OptionalPrincipalDep,
    community_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> BookClubListResponse:
    return await club_service(session).list_clubs(
        community_id=community_id,
        cursor=cursor,
        limit=limit,
        viewer=principal.user if principal else None,
    )


@clubs_router.get("/{club_id}", response_model=BookClubResponse)
async def get_club(
    club_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
) -> BookClubResponse:
    return await club_service(session).get_club(club_id, principal.user if principal else None)


@clubs_router.post("/{club_id}/books", response_model=ClubBookResponse)
async def add_club_book(
    club_id: str,
    payload: ClubBookCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ClubBookResponse:
    return await club_service(session).add_club_book(
        club_id,
        payload,
        principal.user,
        request_context(request),
    )


@clubs_router.get("/{club_id}/books", response_model=ClubBookListResponse)
async def list_club_books(
    club_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
) -> ClubBookListResponse:
    return await club_service(session).list_club_books(
        club_id,
        principal.user if principal else None,
    )


@clubs_router.post("/{club_id}/nominations", response_model=BookNominationResponse)
async def create_nomination(
    club_id: str,
    payload: BookNominationCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BookNominationResponse:
    return await club_service(session).create_nomination(
        club_id,
        payload,
        principal.user,
        request_context(request),
    )


@clubs_router.post("/{club_id}/votes", response_model=BookVoteResponse)
async def cast_vote(
    club_id: str,
    payload: BookVoteRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BookVoteResponse:
    return await club_service(session).cast_vote(
        club_id,
        payload,
        principal.user,
        request_context(request),
    )


@clubs_router.post("/{club_id}/select-book", response_model=ClubBookResponse)
async def select_book(
    club_id: str,
    payload: SelectClubBookRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ClubBookResponse:
    return await club_service(session).select_book(
        club_id,
        payload,
        principal.user,
        request_context(request),
    )


@club_books_router.post("/{club_book_id}/milestones", response_model=ReadingMilestoneResponse)
async def create_milestone(
    club_book_id: str,
    payload: ReadingMilestoneCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingMilestoneResponse:
    return await club_service(session).create_milestone(
        club_book_id,
        payload,
        principal.user,
        request_context(request),
    )


@club_books_router.get("/{club_book_id}/milestones", response_model=ReadingMilestoneListResponse)
async def list_milestones(
    club_book_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
    finished: bool = Query(default=False),
    progress_type: str | None = Query(default=None),
    progress_value: int | None = Query(default=None, ge=0),
) -> ReadingMilestoneListResponse:
    return await club_service(session).list_milestones(
        club_book_id,
        finished=finished,
        progress_type=progress_type,
        progress_value=progress_value,
        viewer=principal.user if principal else None,
    )


@buddy_reads_router.post(
    "",
    response_model=BuddyReadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_buddy_read(
    payload: BuddyReadCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BuddyReadResponse:
    return await club_service(session).create_buddy_read(
        payload,
        principal.user,
        request_context(request),
    )


@buddy_reads_router.post("/{buddy_read_id}/join", response_model=BuddyReadResponse)
async def join_buddy_read(
    buddy_read_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> BuddyReadResponse:
    return await club_service(session).join_buddy_read(
        buddy_read_id,
        principal.user,
        request_context(request),
    )


@buddy_reads_router.post("/{buddy_read_id}/progress", response_model=BuddyReadResponse)
async def update_buddy_read_progress(
    buddy_read_id: str,
    payload: BuddyReadProgressRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> BuddyReadResponse:
    return await club_service(session).update_buddy_read_progress(
        buddy_read_id,
        payload,
        principal.user,
    )


@readalongs_router.post(
    "",
    response_model=ReadalongResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_readalong(
    payload: ReadalongCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadalongResponse:
    return await club_service(session).create_readalong(
        payload,
        principal.user,
        request_context(request),
    )


@events_router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> EventResponse:
    return await club_service(session).create_event(
        payload,
        principal.user,
        request_context(request),
    )


@events_router.get("", response_model=EventListResponse)
async def list_events(
    session: SessionDep,
    principal: OptionalPrincipalDep,
    club_id: str | None = Query(default=None),
    community_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> EventListResponse:
    return await club_service(session).list_events(
        club_id=club_id,
        community_id=community_id,
        cursor=cursor,
        limit=limit,
        viewer=principal.user if principal else None,
    )


@events_router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
) -> EventResponse:
    return await club_service(session).get_event(event_id, principal.user if principal else None)


@events_router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    payload: EventUpdateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> EventResponse:
    return await club_service(session).update_event(
        event_id,
        payload,
        principal.user,
        request_context(request),
    )


@events_router.post("/{event_id}/rsvps", response_model=EventRSVPResponse)
async def create_rsvp(
    event_id: str,
    payload: EventRSVPRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> EventRSVPResponse:
    return await club_service(session).create_rsvp(
        event_id,
        payload,
        principal.user,
        request_context(request),
    )


@events_router.post("/{event_id}/rsvps/cancel", response_model=EventRSVPResponse)
async def cancel_rsvp(
    event_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> EventRSVPResponse:
    return await club_service(session).cancel_rsvp(
        event_id,
        principal.user,
        request_context(request),
    )


@events_router.post("/{event_id}/checkins", response_model=EventCheckinResponse)
async def create_checkin(
    event_id: str,
    payload: EventCheckinRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> EventCheckinResponse:
    return await club_service(session).create_checkin(
        event_id,
        payload,
        principal.user,
        request_context(request),
    )


@events_router.get("/{event_id}/calendar.ics", response_class=Response)
async def calendar_export(
    event_id: str,
    session: SessionDep,
    principal: OptionalPrincipalDep,
) -> Response:
    body = await club_service(session).calendar_export(
        event_id, principal.user if principal else None
    )
    return Response(content=body, media_type="text/calendar")

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    get_optional_principal,
    request_context,
)
from oldpages_api.reading.schemas import (
    ReadingGoalCreateRequest,
    ReadingGoalListResponse,
    ReadingGoalResponse,
    ReadingNoteCreateRequest,
    ReadingNoteListResponse,
    ReadingNoteResponse,
    ReadingProgressListResponse,
    ReadingProgressResponse,
    ReadingProgressUpdateRequest,
    ReadingStatisticListResponse,
    ReadingStatisticRecomputeRequest,
    ReadingStatisticResponse,
    ShelfCreateRequest,
    ShelfItemCreateRequest,
    ShelfItemResponse,
    ShelfListResponse,
    ShelfResponse,
)
from oldpages_api.reading.service import ReadingService
from oldpages_api.shared.db.database import get_session

reading_router = APIRouter(prefix="/reading", tags=["reading"])
public_reading_router = APIRouter(prefix="/users", tags=["reading"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
OptionalPrincipalDep = Annotated[CurrentPrincipal | None, Depends(get_optional_principal)]


def reading_service(session: AsyncSession) -> ReadingService:
    return ReadingService(session)


@reading_router.post(
    "/shelves",
    response_model=ShelfResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shelf(
    payload: ShelfCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ShelfResponse:
    return await reading_service(session).create_shelf(
        payload,
        principal.user,
        request_context(request),
    )


@reading_router.get("/shelves", response_model=ShelfListResponse)
async def list_my_shelves(
    principal: PrincipalDep,
    session: SessionDep,
) -> ShelfListResponse:
    return await reading_service(session).list_my_shelves(principal.user)


@public_reading_router.get("/{user_id}/shelves", response_model=ShelfListResponse)
async def list_public_shelves(
    user_id: str,
    principal: OptionalPrincipalDep,
    session: SessionDep,
) -> ShelfListResponse:
    return await reading_service(session).list_public_shelves(
        user_id,
        principal.user if principal else None,
    )


@reading_router.post("/shelves/{shelf_id}/items", response_model=ShelfItemResponse)
async def add_shelf_item(
    shelf_id: str,
    payload: ShelfItemCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ShelfItemResponse:
    return await reading_service(session).add_shelf_item(
        shelf_id,
        payload,
        principal.user,
        request_context(request),
    )


@reading_router.delete(
    "/shelves/{shelf_id}/items/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_shelf_item(
    shelf_id: str,
    book_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await reading_service(session).remove_shelf_item(
        shelf_id,
        book_id,
        principal.user,
        request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@reading_router.put("/progress/{book_id}", response_model=ReadingProgressResponse)
async def update_progress(
    book_id: str,
    payload: ReadingProgressUpdateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingProgressResponse:
    return await reading_service(session).update_progress(
        book_id,
        payload,
        principal.user,
        request_context(request),
    )


@reading_router.get("/progress", response_model=ReadingProgressListResponse)
async def list_progress(
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingProgressListResponse:
    return await reading_service(session).list_progress(principal.user)


@reading_router.post(
    "/notes",
    response_model=ReadingNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    payload: ReadingNoteCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingNoteResponse:
    return await reading_service(session).create_note(
        payload,
        principal.user,
        request_context(request),
    )


@reading_router.get("/notes", response_model=ReadingNoteListResponse)
async def list_notes(
    principal: PrincipalDep,
    session: SessionDep,
    book_id: str | None = Query(default=None),
) -> ReadingNoteListResponse:
    return await reading_service(session).list_notes(principal.user, book_id=book_id)


@public_reading_router.get("/{user_id}/reading-notes", response_model=ReadingNoteListResponse)
async def list_public_notes(
    user_id: str,
    session: SessionDep,
    book_id: str | None = Query(default=None),
) -> ReadingNoteListResponse:
    return await reading_service(session).list_public_notes(user_id, book_id)


@reading_router.post(
    "/goals",
    response_model=ReadingGoalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_goal(
    payload: ReadingGoalCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingGoalResponse:
    return await reading_service(session).create_goal(
        payload,
        principal.user,
        request_context(request),
    )


@reading_router.get("/goals", response_model=ReadingGoalListResponse)
async def list_goals(
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingGoalListResponse:
    return await reading_service(session).list_goals(principal.user)


@reading_router.post("/statistics/recompute", response_model=ReadingStatisticResponse)
async def recompute_statistics(
    payload: ReadingStatisticRecomputeRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingStatisticResponse:
    return await reading_service(session).recompute_statistics(
        payload,
        principal.user,
        request_context(request),
    )


@reading_router.get("/statistics", response_model=ReadingStatisticListResponse)
async def list_statistics(
    principal: PrincipalDep,
    session: SessionDep,
) -> ReadingStatisticListResponse:
    return await reading_service(session).list_statistics(principal.user)

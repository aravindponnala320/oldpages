from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    request_context,
)
from fastapi import Query
from oldpages_api.listings.schemas import (
    CompleteMediaUploadRequest,
    ListingCreateRequest,
    ListingResponse,
    ListingUpdateRequest,
    MediaAssetResponse,
    MediaUploadUrlRequest,
    MediaUploadUrlResponse,
)
from oldpages_api.listings.service import ListingService
from oldpages_api.shared.db.database import get_session

listings_router = APIRouter(prefix="/listings", tags=["listings"])
media_router = APIRouter(prefix="/media", tags=["media"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]


def listing_service(request: Request, session: AsyncSession) -> ListingService:
    return ListingService(session, request.app.state.settings)


@listings_router.get("/mine", response_model=list[ListingResponse])
async def my_listings(
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
    listing_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[ListingResponse]:
    return await listing_service(request, session).get_my_listings(
        principal.user, status=listing_status, limit=limit
    )


@listings_router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ListingResponse:
    return await listing_service(request, session).create_listing(
        payload,
        principal.user,
        request_context(request),
    )


@listings_router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: str,
    request: Request,
    session: SessionDep,
) -> ListingResponse:
    return await listing_service(request, session).get_listing(listing_id)


@listings_router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    payload: ListingUpdateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ListingResponse:
    return await listing_service(request, session).update_listing(
        listing_id,
        payload,
        principal.user,
        request_context(request),
    )


@listings_router.post("/{listing_id}/publish", response_model=ListingResponse)
async def publish_listing(
    listing_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ListingResponse:
    return await listing_service(request, session).publish_listing(
        listing_id,
        principal.user,
        request_context(request),
    )


@listings_router.post("/{listing_id}/pause", response_model=ListingResponse)
async def pause_listing(
    listing_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ListingResponse:
    return await listing_service(request, session).pause_listing(
        listing_id,
        principal.user,
        request_context(request),
    )


@listings_router.post("/{listing_id}/relist", response_model=ListingResponse)
async def relist_listing(
    listing_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ListingResponse:
    return await listing_service(request, session).relist_listing(
        listing_id,
        principal.user,
        request_context(request),
    )


@listings_router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await listing_service(request, session).delete_listing(
        listing_id,
        principal.user,
        request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@media_router.post("/upload-url", response_model=MediaUploadUrlResponse)
async def create_media_upload_url(
    payload: MediaUploadUrlRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> MediaUploadUrlResponse:
    return await listing_service(request, session).create_upload_url(
        payload,
        principal.user,
        request_context(request),
    )


@media_router.post("/{media_id}/complete", response_model=MediaAssetResponse)
async def complete_media_upload(
    media_id: str,
    payload: CompleteMediaUploadRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> MediaAssetResponse:
    return await listing_service(request, session).complete_upload(
        media_id,
        payload,
        principal.user,
        request_context(request),
    )

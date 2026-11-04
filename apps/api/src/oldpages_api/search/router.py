from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.core.config import Settings, get_settings
from oldpages_api.geo.dependencies import ActiveLocationDep
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    get_optional_principal,
    request_context,
)
from oldpages_api.listings.schemas import ConditionGrade, DeliveryMethod, ListingMode
from oldpages_api.search.schemas import (
    FollowCreateRequest,
    FollowResponse,
    ListingFavoriteResponse,
    ListingSearchFilters,
    ListingSearchResponse,
    SavedSearchCreateRequest,
    SavedSearchListResponse,
    SavedSearchResponse,
    SearchSort,
    SearchSuggestionResponse,
    WishlistItemResponse,
)
from oldpages_api.search.service import SearchService
from oldpages_api.shared.db.database import get_session

search_router = APIRouter(prefix="/search", tags=["search"])
saved_searches_router = APIRouter(prefix="/saved-searches", tags=["saved searches"])
wishlists_router = APIRouter(prefix="/wishlists", tags=["wishlists"])
listing_favorites_router = APIRouter(prefix="/listings", tags=["favorites"])
follows_router = APIRouter(prefix="/follows", tags=["follows"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
OptionalPrincipalDep = Annotated[CurrentPrincipal | None, Depends(get_optional_principal)]


def search_service(session: AsyncSession) -> SearchService:
    return SearchService(session)


@search_router.get("/listings", response_model=ListingSearchResponse)
async def search_listings(
    session: SessionDep,
    principal: OptionalPrincipalDep,
    active_location: ActiveLocationDep,
    settings: Annotated[Settings, Depends(get_settings)],
    actual_photos: bool | None = None,
    author: str | None = Query(default=None, max_length=240),
    campus_pickup: bool | None = None,
    category: str | None = Query(default=None, max_length=180),
    city: str | None = Query(default=None, max_length=120),
    condition: ConditionGrade | None = None,
    country: str | None = Query(default=None, max_length=80),
    cursor: str | None = Query(default=None, max_length=256),
    delivery_method: DeliveryMethod | None = None,
    distance_km: float | None = Query(default=None, gt=0, le=500),
    first_edition: bool | None = None,
    format: str | None = Query(default=None, max_length=32),
    free_only: bool = False,
    isbn: str | None = Query(default=None, max_length=32),
    language: str | None = Query(default=None, max_length=24),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    limit: int = Query(default=20, ge=1, le=50),
    listing_mode: ListingMode | None = None,
    longitude: float | None = Query(default=None, ge=-180, le=180),
    max_price_amount_cents: int | None = Query(default=None, ge=0),
    min_price_amount_cents: int | None = Query(default=None, ge=0),
    negotiable: bool | None = None,
    publication_year: int | None = Query(default=None, ge=1450, le=2200),
    publisher: str | None = Query(default=None, max_length=240),
    q: str | None = Query(default=None, max_length=500),
    signed_copy: bool | None = None,
    sort: SearchSort = "relevance",
    state: str | None = Query(default=None, max_length=120),
    use_active_location: bool = Query(default=True),
) -> ListingSearchResponse:
    if (
        use_active_location
        and active_location is not None
        and latitude is None
        and longitude is None
    ):
        latitude = active_location.latitude
        longitude = active_location.longitude
        if distance_km is None:
            distance_km = min(
                active_location.radius_km or settings.geo_default_radius_km,
                settings.geo_max_radius_km,
            )
    filters = ListingSearchFilters(
        actual_photos=actual_photos,
        author=author,
        campus_pickup=campus_pickup,
        category=category,
        city=city,
        condition=condition,
        country=country,
        cursor=cursor,
        delivery_method=delivery_method,
        distance_km=distance_km,
        first_edition=first_edition,
        format=format,
        free_only=free_only,
        isbn=isbn,
        language=language,
        latitude=latitude,
        limit=limit,
        listing_mode=listing_mode,
        longitude=longitude,
        max_price_amount_cents=max_price_amount_cents,
        min_price_amount_cents=min_price_amount_cents,
        negotiable=negotiable,
        publication_year=publication_year,
        publisher=publisher,
        q=q,
        signed_copy=signed_copy,
        sort=sort,
        state=state,
    )
    return await search_service(session).search_listings(
        filters,
        principal.user if principal else None,
    )


@search_router.get("/suggestions", response_model=SearchSuggestionResponse)
async def search_suggestions(
    session: SessionDep,
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=20),
) -> SearchSuggestionResponse:
    return await search_service(session).suggestions(q, limit)


@saved_searches_router.post(
    "",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_saved_search(
    payload: SavedSearchCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> SavedSearchResponse:
    return await search_service(session).create_saved_search(
        payload,
        principal.user,
        request_context(request),
    )


@saved_searches_router.get("", response_model=SavedSearchListResponse)
async def list_saved_searches(
    principal: PrincipalDep,
    session: SessionDep,
) -> SavedSearchListResponse:
    return await search_service(session).list_saved_searches(principal.user)


@wishlists_router.post(
    "/{book_id}",
    response_model=WishlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_wishlist_item(
    book_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> WishlistItemResponse:
    return await search_service(session).add_wishlist_item(
        book_id,
        principal.user,
        request_context(request),
    )


@wishlists_router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    book_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await search_service(session).delete_wishlist_item(
        book_id,
        principal.user,
        request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@listing_favorites_router.post(
    "/{listing_id}/favorite",
    response_model=ListingFavoriteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_listing_favorite(
    listing_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> ListingFavoriteResponse:
    return await search_service(session).add_listing_favorite(
        listing_id,
        principal.user,
        request_context(request),
    )


@listing_favorites_router.delete("/{listing_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing_favorite(
    listing_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await search_service(session).delete_listing_favorite(
        listing_id,
        principal.user,
        request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@follows_router.post("", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
async def create_follow(
    payload: FollowCreateRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> FollowResponse:
    return await search_service(session).create_follow(
        payload,
        principal.user,
        request_context(request),
    )


@follows_router.delete("/{follow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_follow(
    follow_id: str,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    await search_service(session).delete_follow(
        follow_id,
        principal.user,
        request_context(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

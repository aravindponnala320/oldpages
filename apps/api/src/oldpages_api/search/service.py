from __future__ import annotations

import math
import time
from typing import cast

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.models import BookEdition
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import utc_now
from oldpages_api.listings.models import (
    Listing,
    ListingCondition,
    ListingImage,
    ListingLocation,
    MediaAsset,
)
from oldpages_api.listings.service import location_public_response
from oldpages_api.search.events import (
    FOLLOW_CREATED,
    FOLLOW_DELETED,
    LISTING_FAVORITED,
    LISTING_UNFAVORITED,
    MATCH_NOTIFICATION_QUEUED,
    SAVED_SEARCH_CREATED,
    SEARCH_ZERO_RESULTS_RECORDED,
    WISHLIST_ITEM_ADDED,
    WISHLIST_ITEM_DELETED,
)
from oldpages_api.search.exceptions import (
    DuplicateSearchResourceError,
    SearchResourceNotFoundError,
    SearchValidationError,
)
from oldpages_api.search.models import (
    Follow,
    ListingFavorite,
    SavedSearch,
    SearchMatchNotification,
    SearchQueryLog,
    WishlistItem,
)
from oldpages_api.search.permissions import require_owner
from oldpages_api.search.repository import SearchRepository
from oldpages_api.search.schemas import (
    ConditionGrade,
    DeliveryMethod,
    FollowCreateRequest,
    FollowResponse,
    FollowTargetType,
    ListingFavoriteResponse,
    ListingMode,
    ListingSearchFilters,
    ListingSearchResponse,
    ListingSearchResult,
    SavedSearchCreateRequest,
    SavedSearchListResponse,
    SavedSearchResponse,
    SearchListingBookSummary,
    SearchSort,
    SearchSuggestion,
    SearchSuggestionResponse,
    SuggestionType,
    WishlistItemResponse,
)
from oldpages_api.search.tasks import enqueue_saved_search_match_notification


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SearchRepository(session)

    async def search_listings(
        self,
        filters: ListingSearchFilters,
        actor: User | None,
    ) -> ListingSearchResponse:
        started = time.perf_counter()
        page = await self.repo.search_listing_page(filters)
        latency_ms = int((time.perf_counter() - started) * 1000)
        await self.log_search(filters, actor, page.total, latency_ms)
        await self.repo.commit()
        return ListingSearchResponse(
            items=[
                listing_search_result(
                    listing,
                    page.favorite_counts.get(listing.id, 0),
                    listing_distance_km(listing.location, filters),
                )
                for listing in page.listings
            ],
            next_cursor=page.next_cursor,
            result_count=page.total,
        )

    async def suggestions(self, query: str, limit: int) -> SearchSuggestionResponse:
        cleaned = query.strip()
        if not cleaned:
            return SearchSuggestionResponse(items=[])
        suggestions = await self.repo.suggestions(cleaned, limit)
        return SearchSuggestionResponse(
            items=[
                SearchSuggestion(text=text, type=cast("SuggestionType", suggestion_type))
                for suggestion_type, text in suggestions
            ]
        )

    async def create_saved_search(
        self,
        payload: SavedSearchCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> SavedSearchResponse:
        existing = await self.repo.get_saved_search_by_name(actor.id, payload.name)
        if existing is not None:
            raise DuplicateSearchResourceError("A saved search with this name already exists.")
        filters = saved_search_filters(payload)
        match_count = await self.repo.count_matching(filters)
        saved_search = SavedSearch(
            filters_json=payload.filters,
            last_matched_at=utc_now() if match_count else None,
            last_result_count=match_count,
            name=payload.name,
            notifications_enabled=payload.notifications_enabled,
            query=payload.query,
            sort=payload.sort,
            user_id=actor.id,
        )
        self.repo.add(saved_search)
        await self.repo.flush()
        if match_count and payload.notifications_enabled:
            self.repo.add(
                SearchMatchNotification(
                    match_count=match_count,
                    metadata_json={"query": payload.query, "filters": payload.filters},
                    saved_search_id=saved_search.id,
                    status="pending",
                    user_id=actor.id,
                )
            )
            await enqueue_saved_search_match_notification(saved_search.id)
            await self.audit(
                action=MATCH_NOTIFICATION_QUEUED,
                actor=actor,
                context=context,
                payload={"saved_search_id": saved_search.public_id},
            )
        await self.audit(
            action=SAVED_SEARCH_CREATED,
            actor=actor,
            context=context,
            payload={"saved_search_id": saved_search.public_id},
        )
        await self.repo.commit()
        return saved_search_response(saved_search)

    async def list_saved_searches(self, actor: User) -> SavedSearchListResponse:
        searches = await self.repo.list_saved_searches(actor.id)
        return SavedSearchListResponse(items=[saved_search_response(item) for item in searches])

    async def add_wishlist_item(
        self,
        book_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> WishlistItemResponse:
        book = await self.repo.get_book_edition_by_public_id(book_id)
        if book is None:
            raise SearchResourceNotFoundError("Book not found.")
        existing = await self.repo.get_wishlist_item(actor.id, book.id)
        if existing is not None:
            return wishlist_item_response(existing)
        item = WishlistItem(book_edition_id=book.id, user_id=actor.id)
        self.repo.add(item)
        await self.audit(
            action=WISHLIST_ITEM_ADDED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id},
        )
        await self.repo.commit()
        item.book_edition = book
        return wishlist_item_response(item)

    async def delete_wishlist_item(
        self,
        book_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        book = await self.repo.get_book_edition_by_public_id(book_id)
        if book is None:
            return
        item = await self.repo.get_wishlist_item(actor.id, book.id)
        if item is None:
            return
        await self.repo.delete(item)
        await self.audit(
            action=WISHLIST_ITEM_DELETED,
            actor=actor,
            context=context,
            payload={"book_id": book.public_id},
        )
        await self.repo.commit()

    async def add_listing_favorite(
        self,
        listing_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> ListingFavoriteResponse:
        listing = await self.repo.get_listing_by_public_id(listing_id)
        if listing is None:
            raise SearchResourceNotFoundError("Listing not found.")
        existing = await self.repo.get_listing_favorite(actor.id, listing.id)
        if existing is not None:
            return listing_favorite_response(existing, listing.public_id)
        favorite = ListingFavorite(listing_id=listing.id, user_id=actor.id)
        self.repo.add(favorite)
        await self.audit(
            action=LISTING_FAVORITED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()
        return listing_favorite_response(favorite, listing.public_id)

    async def delete_listing_favorite(
        self,
        listing_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        listing = await self.repo.get_listing_by_public_id(listing_id)
        if listing is None:
            return
        favorite = await self.repo.get_listing_favorite(actor.id, listing.id)
        if favorite is None:
            return
        await self.repo.delete(favorite)
        await self.audit(
            action=LISTING_UNFAVORITED,
            actor=actor,
            context=context,
            payload={"listing_id": listing.public_id},
        )
        await self.repo.commit()

    async def create_follow(
        self,
        payload: FollowCreateRequest,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> FollowResponse:
        await self.validate_follow_target(payload)
        existing = await self.repo.get_follow(actor.id, payload.target_type, payload.target_id)
        if existing is not None:
            return follow_response(existing)
        follow = Follow(
            target_id=payload.target_id,
            target_label=payload.target_label,
            target_type=payload.target_type,
            user_id=actor.id,
        )
        self.repo.add(follow)
        await self.audit(
            action=FOLLOW_CREATED,
            actor=actor,
            context=context,
            payload={"target_id": payload.target_id, "target_type": payload.target_type},
        )
        await self.repo.commit()
        return follow_response(follow)

    async def delete_follow(
        self,
        follow_id: str,
        actor: User,
        context: AuthenticatedRequestContext,
    ) -> None:
        follow = await self.repo.get_follow_by_public_id(follow_id)
        if follow is None:
            raise SearchResourceNotFoundError("Follow not found.")
        require_owner(actor, follow.user_id)
        await self.repo.delete(follow)
        await self.audit(
            action=FOLLOW_DELETED,
            actor=actor,
            context=context,
            payload={"follow_id": follow.public_id},
        )
        await self.repo.commit()

    async def validate_follow_target(self, payload: FollowCreateRequest) -> None:
        if payload.target_type in {"user", "seller"}:
            if await self.repo.get_user_by_public_id(payload.target_id) is None:
                raise SearchResourceNotFoundError("Follow target user not found.")
        if payload.target_type == "author":
            if await self.repo.get_author_by_public_id(payload.target_id) is None:
                raise SearchResourceNotFoundError("Follow target author not found.")

    async def log_search(
        self,
        filters: ListingSearchFilters,
        actor: User | None,
        result_count: int,
        latency_ms: int,
    ) -> None:
        self.repo.add(
            SearchQueryLog(
                filters_json=filters.log_filters(),
                latency_ms=latency_ms,
                query=filters.q,
                result_count=result_count,
                sort=filters.sort,
                user_id=actor.id if actor else None,
                zero_results=result_count == 0,
            )
        )
        if result_count == 0:
            self.repo.add(
                AuditLog(
                    action=SEARCH_ZERO_RESULTS_RECORDED,
                    actor_user_id=actor.id if actor else None,
                    context_json=filters.log_filters(),
                    target_user_id=None,
                )
            )

    async def audit(
        self,
        *,
        action: str,
        actor: User,
        context: AuthenticatedRequestContext,
        payload: dict[str, str],
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


def saved_search_filters(payload: SavedSearchCreateRequest) -> ListingSearchFilters:
    values = dict(payload.filters)
    values["q"] = payload.query
    values["sort"] = payload.sort
    try:
        return ListingSearchFilters(**values)
    except ValidationError as exc:
        raise SearchValidationError("Saved search filters are invalid.") from exc


def listing_distance_km(
    location: ListingLocation | None,
    filters: ListingSearchFilters,
) -> float | None:
    if (
        location is None
        or location.public_latitude is None
        or location.public_longitude is None
        or filters.latitude is None
        or filters.longitude is None
    ):
        return None
    return haversine_km(
        filters.latitude,
        filters.longitude,
        location.public_latitude,
        location.public_longitude,
    )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return earth_radius_km * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def listing_search_result(
    listing: Listing,
    favorite_count: int,
    distance_km: float | None,
) -> ListingSearchResult:
    return ListingSearchResult(
        book=book_summary(listing.book_edition),
        condition=condition_value(listing.condition),
        created_at=listing.created_at,
        currency=listing.currency,
        delivery_methods=[
            cast("DeliveryMethod", method.method)
            for method in sorted(listing.delivery_methods, key=lambda item: item.method)
            if method.enabled
        ],
        distance_km=round(distance_km, 2) if distance_km is not None else None,
        favorite_count=favorite_count,
        id=listing.public_id,
        image_url=primary_image_url(listing.images),
        listing_modes=cast("list[ListingMode]", listing.listing_modes),
        location=location_public_response(listing.location),
        negotiable=listing.negotiable,
        price_amount_cents=listing.price_amount_cents,
        quality_score=listing.quality_score,
        seller={"id": listing.seller.public_id},
        title=listing.title_snapshot,
    )


def book_summary(book: BookEdition) -> SearchListingBookSummary:
    identifiers = {item.identifier_type: item.identifier_value for item in book.identifiers}
    return SearchListingBookSummary(
        authors=[
            item.author.name for item in sorted(book.book.authors, key=lambda item: item.position)
        ],
        categories=[item.category.name for item in book.book.categories],
        id=book.public_id,
        isbn_10=identifiers.get("isbn10"),
        isbn_13=identifiers.get("isbn13"),
        title=book.title,
    )


def condition_value(condition: ListingCondition | None) -> ConditionGrade | None:
    return cast("ConditionGrade | None", condition.condition if condition else None)


def primary_image_url(images: list[ListingImage]) -> str | None:
    sorted_images = sorted(images, key=lambda image: (not image.is_primary, image.sort_order))
    for image in sorted_images:
        media: MediaAsset = image.media_asset
        if media.status == "approved":
            return media.public_url
    return None


def saved_search_response(saved_search: SavedSearch) -> SavedSearchResponse:
    return SavedSearchResponse(
        created_at=saved_search.created_at,
        filters=saved_search.filters_json,
        id=saved_search.public_id,
        last_matched_at=saved_search.last_matched_at,
        last_result_count=saved_search.last_result_count,
        name=saved_search.name,
        notifications_enabled=saved_search.notifications_enabled,
        query=saved_search.query,
        sort=cast("SearchSort", saved_search.sort),
    )


def wishlist_item_response(item: WishlistItem) -> WishlistItemResponse:
    return WishlistItemResponse(
        book=book_summary(item.book_edition),
        created_at=item.created_at,
        id=item.public_id,
    )


def listing_favorite_response(
    favorite: ListingFavorite,
    listing_public_id: str,
) -> ListingFavoriteResponse:
    return ListingFavoriteResponse(
        created_at=favorite.created_at,
        id=favorite.public_id,
        listing_id=listing_public_id,
    )


def follow_response(follow: Follow) -> FollowResponse:
    return FollowResponse(
        created_at=follow.created_at,
        id=follow.public_id,
        target_id=follow.target_id,
        target_label=follow.target_label,
        target_type=cast("FollowTargetType", follow.target_type),
    )

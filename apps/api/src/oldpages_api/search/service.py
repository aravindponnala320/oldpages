from __future__ import annotations

import base64
import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
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

CONDITION_RANK = {
    "new_sealed": 8,
    "like_new": 7,
    "excellent": 6,
    "very_good": 5,
    "good": 4,
    "acceptable": 3,
    "poor": 2,
    "reference_only": 1,
}


@dataclass(frozen=True, slots=True)
class RankedListing:
    distance_km: float | None
    favorite_count: int
    listing: Listing
    relevance_score: float


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SearchRepository(session)

    async def search_listings(
        self,
        filters: ListingSearchFilters,
        actor: User | None,
    ) -> ListingSearchResponse:
        started = time.perf_counter()
        candidates = await self.repo.search_listing_candidates(filters)
        favorite_counts = await self.repo.favorite_counts([listing.id for listing in candidates])
        ranked = rank_and_filter(candidates, filters, favorite_counts)
        result_count = len(ranked)
        page, next_cursor = paginate(ranked, filters.cursor, filters.limit)
        latency_ms = int((time.perf_counter() - started) * 1000)
        await self.log_search(filters, actor, result_count, latency_ms)
        await self.repo.commit()
        return ListingSearchResponse(
            items=[
                listing_search_result(item.listing, item.favorite_count, item.distance_km)
                for item in page
            ],
            next_cursor=next_cursor,
            result_count=result_count,
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
        candidates = await self.repo.search_listing_candidates(filters)
        ranked = rank_and_filter(
            candidates,
            filters,
            await self.repo.favorite_counts([listing.id for listing in candidates]),
        )
        saved_search = SavedSearch(
            filters_json=payload.filters,
            last_matched_at=utc_now() if ranked else None,
            last_result_count=len(ranked),
            name=payload.name,
            notifications_enabled=payload.notifications_enabled,
            query=payload.query,
            sort=payload.sort,
            user_id=actor.id,
        )
        self.repo.add(saved_search)
        await self.repo.flush()
        if ranked and payload.notifications_enabled:
            self.repo.add(
                SearchMatchNotification(
                    match_count=len(ranked),
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


def rank_and_filter(
    listings: list[Listing],
    filters: ListingSearchFilters,
    favorite_counts: dict[int, int],
) -> list[RankedListing]:
    ranked: list[RankedListing] = []
    for listing in listings:
        if not passes_python_filters(listing, filters):
            continue
        distance_km = listing_distance_km(listing.location, filters)
        if filters.distance_km is not None:
            if distance_km is None or distance_km > filters.distance_km:
                continue
        favorite_count = favorite_counts.get(listing.id, 0)
        ranked.append(
            RankedListing(
                distance_km=distance_km,
                favorite_count=favorite_count,
                listing=listing,
                relevance_score=relevance_score(listing, filters, favorite_count, distance_km),
            )
        )
    return sorted(ranked, key=sort_key(filters.sort), reverse=sort_reverse(filters.sort))


def passes_python_filters(listing: Listing, filters: ListingSearchFilters) -> bool:
    if filters.listing_mode and filters.listing_mode not in listing.listing_modes:
        return False
    if filters.delivery_method and not any(
        method.enabled and method.method == filters.delivery_method
        for method in listing.delivery_methods
    ):
        return False
    if filters.actual_photos and not listing.images:
        return False
    return True


def sort_key(sort: SearchSort) -> Callable[[RankedListing], tuple[float, float, float]]:
    def key(item: RankedListing) -> tuple[float, float, float]:
        listing = item.listing
        if sort == "nearest":
            return (
                item.distance_km if item.distance_km is not None else 1_000_000,
                timestamp(listing.created_at),
                float(listing.id),
            )
        if sort == "newest":
            return (timestamp(listing.created_at), item.relevance_score, float(listing.id))
        if sort == "lowest_price":
            price = listing.price_amount_cents if listing.price_amount_cents is not None else 0
            return (float(price), item.relevance_score, float(listing.id))
        if sort == "highest_price":
            price = listing.price_amount_cents if listing.price_amount_cents is not None else -1
            return (float(price), item.relevance_score, float(listing.id))
        if sort == "best_condition":
            condition = listing.condition.condition if listing.condition else ""
            return (
                float(CONDITION_RANK.get(condition, 0)),
                item.relevance_score,
                float(listing.id),
            )
        if sort == "most_saved":
            return (float(item.favorite_count), item.relevance_score, float(listing.id))
        return (item.relevance_score, timestamp(listing.created_at), float(listing.id))

    return key


def sort_reverse(sort: SearchSort) -> bool:
    return sort not in {"lowest_price", "nearest"}


def timestamp(value: datetime) -> float:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return float(value.timestamp())


def relevance_score(
    listing: Listing,
    filters: ListingSearchFilters,
    favorite_count: int,
    distance_km: float | None,
) -> float:
    score = listing.quality_score / 100
    score += min(favorite_count, 20) * 0.03
    if distance_km is not None:
        score += max(0, 1 - min(distance_km, 100) / 100) * 0.2
    if not filters.q:
        return score
    query = filters.q.lower()
    haystacks = search_haystacks(listing)
    for value in haystacks:
        lowered = value.lower()
        if query == lowered:
            score += 3
        elif query in lowered:
            score += 1.5
        else:
            similarity = SequenceMatcher(None, query, lowered).ratio()
            if similarity >= 0.72:
                score += similarity
    return score


def search_haystacks(listing: Listing) -> list[str]:
    values = [
        listing.title_snapshot,
        listing.description or "",
        listing.book_edition.title,
        listing.book_edition.subtitle or "",
        listing.book_edition.description or "",
    ]
    values.extend(identifier.identifier_value for identifier in listing.book_edition.identifiers)
    values.extend(author.author.name for author in listing.book_edition.book.authors)
    values.extend(category.category.name for category in listing.book_edition.book.categories)
    values.extend(listing.book_edition.genres)
    values.extend(listing.book_edition.subjects)
    if listing.location is not None:
        values.extend(
            [
                listing.location.city,
                listing.location.neighborhood or "",
                listing.location.public_area,
                listing.location.state or "",
                listing.location.country,
            ]
        )
    return values


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


def paginate(
    ranked: list[RankedListing],
    cursor: str | None,
    limit: int,
) -> tuple[list[RankedListing], str | None]:
    offset = decode_cursor(cursor)
    page = ranked[offset : offset + limit]
    next_offset = offset + limit
    next_cursor = encode_cursor(next_offset) if next_offset < len(ranked) else None
    return page, next_cursor


def encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": offset}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode()


def decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except (ValueError, json.JSONDecodeError) as exc:
        raise SearchValidationError("Invalid search cursor.") from exc
    offset = payload.get("offset")
    if not isinstance(offset, int) or offset < 0:
        raise SearchValidationError("Invalid search cursor.")
    return offset


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

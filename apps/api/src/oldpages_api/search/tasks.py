from __future__ import annotations

import logging

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from oldpages_api.identity.security import utc_now
from oldpages_api.listings.service import as_utc
from oldpages_api.notifications.service import NotificationService
from oldpages_api.search.models import SavedSearch, SearchMatchNotification
from oldpages_api.search.repository import SearchRepository
from oldpages_api.search.schemas import ListingSearchFilters

logger = logging.getLogger(__name__)

ALERT_BATCH = 500


async def enqueue_saved_search_match_notification(saved_search_id: int) -> None:
    """Delivered by send_saved_search_alerts on the worker's next run."""
    _ = saved_search_id


async def send_saved_search_alerts(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Tells readers about books published since their saved search last matched."""
    sent = 0
    async with session_factory() as session:
        notifications = NotificationService(session)
        pending = await session.scalars(
            select(SearchMatchNotification)
            .options(selectinload(SearchMatchNotification.saved_search))
            .where(SearchMatchNotification.status == "pending")
            .limit(ALERT_BATCH)
        )
        for match in pending.all():
            # Queued when the search was saved: the books that already matched.
            await notify(notifications, match.saved_search, match.match_count)
            match.status = "delivered"
            sent += 1
        await session.commit()

        repo = SearchRepository(session)
        searches = await session.scalars(
            select(SavedSearch)
            .options(selectinload(SavedSearch.user))
            .where(SavedSearch.notifications_enabled.is_(True))
            .order_by(SavedSearch.id)
            .limit(ALERT_BATCH)
        )
        for saved in searches.all():
            filters = alert_filters(saved)
            if filters is None:
                continue
            since = as_utc(saved.last_matched_at or saved.created_at)
            fresh = await repo.count_matching(filters, published_after=since)
            if not fresh:
                continue
            await notify(notifications, saved, fresh)
            saved.last_matched_at = utc_now()
            saved.last_result_count = await repo.count_matching(filters)
            await session.commit()
            sent += 1
    if sent:
        logger.info("saved_search_alerts_sent", extra={"count": sent})
    return sent


def alert_filters(saved: SavedSearch) -> ListingSearchFilters | None:
    values = {
        **saved.filters_json,
        "q": saved.query,
        "sort": saved.sort,
        "exclude_seller_id": saved.user.public_id,  # their own new listings aren't news
    }
    try:
        return ListingSearchFilters(**values)
    except ValidationError:
        logger.warning("saved_search_filters_invalid", extra={"saved_search_id": saved.public_id})
        return None


async def notify(notifications: NotificationService, saved: SavedSearch, count: int) -> None:
    books = "book matches" if count == 1 else "books match"
    await notifications.create_notification(
        user_id=saved.user_id,
        notification_type="saved_search_match",
        title=f"New for “{saved.name}”",
        body=f"{count} {books} your saved search.",
        related_entity_type="saved_search",
        related_entity_id=saved.public_id,
        data={"saved_search_id": saved.public_id, "query": saved.query, "count": count},
    )

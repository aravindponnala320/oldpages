from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.models import Book, BookEdition
from oldpages_api.listings.models import Listing, ListingInventory
from oldpages_api.reading.models import ShelfItem
from oldpages_api.search.models import ListingFavorite, WishlistItem

logger = logging.getLogger(__name__)

RecommendationCandidate = dict[str, Any]

CONDITION_MULTIPLIER: dict[str, float] = {
    "new_sealed": 1.0,
    "like_new": 0.85,
    "excellent": 0.70,
    "very_good": 0.60,
    "good": 0.50,
    "acceptable": 0.35,
    "poor": 0.20,
    "reference_only": 0.15,
}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "fiction": ["fiction", "novel", "story", "stories", "narrative"],
    "non-fiction": ["non-fiction", "nonfiction", "biography", "memoir", "history", "true"],
    "science": ["science", "physics", "chemistry", "biology", "scientific", "nature"],
    "technology": ["technology", "tech", "programming", "software", "computer", "coding"],
    "mathematics": ["mathematics", "math", "algebra", "calculus", "geometry", "statistics"],
    "philosophy": ["philosophy", "logic", "ethics", "metaphysics", "epistemology"],
    "self-help": ["self-help", "self help", "motivation", "productivity", "mindset", "habit"],
    "business": ["business", "management", "entrepreneurship", "startup", "finance", "economics"],
    "children": ["children", "kids", "picture book", "juvenile", "young adult", "ya"],
    "education": ["education", "textbook", "academic", "study", "learning", "exam"],
    "literature": ["literature", "classic", "poetry", "poem", "drama", "play"],
    "health": ["health", "medicine", "medical", "nutrition", "wellness", "fitness"],
    "history": ["history", "historical", "ancient", "war", "civilization", "empire"],
    "art": ["art", "design", "drawing", "painting", "photography", "creative"],
    "religion": ["religion", "spirituality", "yoga", "meditation", "faith", "theology"],
    "law": ["law", "legal", "constitution", "rights", "justice", "court"],
    "cooking": ["cooking", "recipe", "food", "cuisine", "chef", "baking"],
    "travel": ["travel", "geography", "atlas", "explore", "adventure", "culture"],
}


class RecommendationEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_for_user(
        self, user_id: int, limit: int = 20
    ) -> list[RecommendationCandidate]:
        """
        Generate recommendations using rule-based signals:
        1. Wishlist-based: find listings for books in user's wishlist
        2. Genre-based: find listings in user's favorite genres (from reading history)
        3. Trending: find most-saved listings in last 7 days
        """
        results: list[RecommendationCandidate] = []

        wishlist_recs = await self._wishlist_based(user_id, limit)
        results.extend(wishlist_recs)

        genre_recs = await self._genre_based(user_id, limit)
        results.extend(genre_recs)

        trending_recs = await self._trending_based(limit)
        results.extend(trending_recs)

        deduplicated = _deduplicate(results)
        deduplicated.sort(key=lambda r: r["score"], reverse=True)
        return deduplicated[:limit]

    async def generate_book_recommendations(
        self, user_id: int, limit: int = 10
    ) -> list[RecommendationCandidate]:
        """Books similar to what user has read or wishlisted, by genre overlap."""
        read_book_edition_ids = await self._user_read_book_edition_ids(user_id)
        wishlist_book_edition_ids = await self._user_wishlist_book_edition_ids(user_id)
        known_ids = set(read_book_edition_ids) | set(wishlist_book_edition_ids)

        if not known_ids:
            return []

        genres = await self._genres_for_book_editions(list(known_ids))
        if not genres:
            return []

        result = await self.session.execute(
            select(BookEdition)
            .join(Book, Book.id == BookEdition.book_id)
            .where(BookEdition.id.not_in(known_ids))
            .limit(limit * 3)
        )
        candidates = list(result.scalars().all())

        recs: list[RecommendationCandidate] = []
        for edition in candidates:
            overlap = [g for g in edition.genres if g in genres]
            if overlap:
                score = min(len(overlap) / max(len(genres), 1), 1.0) * 0.7
                recs.append(
                    {
                        "entity_type": "book",
                        "entity_id": edition.id,
                        "score": round(score, 4),
                        "reason": f"Similar genres: {', '.join(overlap[:3])}",
                        "source": "genre",
                    }
                )

        recs.sort(key=lambda r: r["score"], reverse=True)
        return recs[:limit]

    async def generate_price_suggestion(self, book_id: int, condition: str) -> dict[str, Any]:
        """
        Suggest price based on average price of similar active listings for same book,
        adjusted by condition multiplier.
        """
        result = await self.session.execute(
            select(Listing.price_amount_cents)
            .join(BookEdition, BookEdition.id == Listing.book_edition_id)
            .join(ListingInventory, ListingInventory.listing_id == Listing.id)
            .where(
                BookEdition.book_id == book_id,
                Listing.status == "active",
                Listing.price_amount_cents.is_not(None),
                ListingInventory.quantity_available > 0,
            )
            .limit(50)
        )
        prices = [row[0] for row in result.all() if row[0] is not None]

        multiplier = CONDITION_MULTIPLIER.get(condition, 0.5)

        if not prices:
            return {
                "suggested_cents": None,
                "min_cents": None,
                "max_cents": None,
                "basis": "no_data",
            }

        avg_price = sum(prices) / len(prices)
        suggested = int(avg_price * multiplier)
        min_price = int(min(prices) * multiplier)
        max_price = int(max(prices) * multiplier)

        return {
            "suggested_cents": suggested,
            "min_cents": min_price,
            "max_cents": max_price,
            "basis": f"average_of_{len(prices)}_listings",
        }

    async def suggest_categories(self, title: str, description: str) -> list[str]:
        """Rule-based category suggestion from title and description keywords."""
        combined = f"{title} {description}".lower()
        matched: list[str] = []
        for slug, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in combined for kw in keywords):
                matched.append(slug)
        return matched[:5]

    async def get_similar_listings(self, listing_id: int, limit: int = 10) -> list[Listing]:
        """Find listings for same book or same genres."""
        result = await self.session.execute(select(Listing).where(Listing.id == listing_id))
        source = result.scalar_one_or_none()
        if source is None:
            return []

        result2 = await self.session.execute(
            select(Listing)
            .join(ListingInventory, ListingInventory.listing_id == Listing.id)
            .where(
                Listing.book_edition_id == source.book_edition_id,
                Listing.id != listing_id,
                Listing.status == "active",
                Listing.deleted_at.is_(None),
                ListingInventory.quantity_available > 0,
            )
            .order_by(Listing.created_at.desc())
            .limit(limit)
        )
        return list(result2.scalars().all())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _wishlist_based(self, user_id: int, limit: int) -> list[RecommendationCandidate]:
        result = await self.session.execute(
            select(WishlistItem.book_edition_id).where(WishlistItem.user_id == user_id).limit(20)
        )
        book_edition_ids = [row[0] for row in result.all()]
        if not book_edition_ids:
            return []

        result2 = await self.session.execute(
            select(Listing)
            .join(ListingInventory, ListingInventory.listing_id == Listing.id)
            .where(
                Listing.book_edition_id.in_(book_edition_ids),
                Listing.status == "active",
                Listing.deleted_at.is_(None),
                ListingInventory.quantity_available > 0,
                Listing.seller_user_id != user_id,
            )
            .order_by(Listing.created_at.desc())
            .limit(limit)
        )
        listings = list(result2.scalars().all())
        return [
            {
                "entity_type": "listing",
                "entity_id": listing.id,
                "score": 0.90,
                "reason": "This book is on your wishlist",
                "source": "wishlist",
            }
            for listing in listings
        ]

    async def _genre_based(self, user_id: int, limit: int) -> list[RecommendationCandidate]:
        read_ids = await self._user_read_book_edition_ids(user_id)
        if not read_ids:
            return []
        genres = await self._genres_for_book_editions(read_ids)
        if not genres:
            return []

        result = await self.session.execute(
            select(BookEdition.id)
            .where(BookEdition.genres.contains(list(genres)[:1]))
            .where(BookEdition.id.not_in(read_ids))
            .limit(20)
        )
        target_ids = [row[0] for row in result.all()]
        if not target_ids:
            return []

        result2 = await self.session.execute(
            select(Listing)
            .join(ListingInventory, ListingInventory.listing_id == Listing.id)
            .where(
                Listing.book_edition_id.in_(target_ids),
                Listing.status == "active",
                Listing.deleted_at.is_(None),
                ListingInventory.quantity_available > 0,
                Listing.seller_user_id != user_id,
            )
            .order_by(Listing.created_at.desc())
            .limit(limit)
        )
        listings = list(result2.scalars().all())
        genre_label = list(genres)[0] if genres else "your favorite genres"
        return [
            {
                "entity_type": "listing",
                "entity_id": listing.id,
                "score": 0.70,
                "reason": f"Based on your reading history in {genre_label}",
                "source": "genre",
            }
            for listing in listings
        ]

    async def _trending_based(self, limit: int) -> list[RecommendationCandidate]:
        cutoff = datetime.now(UTC) - timedelta(days=7)
        result = await self.session.execute(
            select(ListingFavorite.listing_id, func.count(ListingFavorite.id).label("cnt"))
            .where(ListingFavorite.created_at >= cutoff)
            .group_by(ListingFavorite.listing_id)
            .order_by(func.count(ListingFavorite.id).desc())
            .limit(limit)
        )
        rows = result.all()
        if not rows:
            return []

        listing_ids = [row[0] for row in rows]
        counts = {row[0]: row[1] for row in rows}
        max_count = max(counts.values()) if counts else 1

        result2 = await self.session.execute(
            select(Listing)
            .join(ListingInventory, ListingInventory.listing_id == Listing.id)
            .where(
                Listing.id.in_(listing_ids),
                Listing.status == "active",
                Listing.deleted_at.is_(None),
                ListingInventory.quantity_available > 0,
            )
        )
        listings = list(result2.scalars().all())
        return [
            {
                "entity_type": "listing",
                "entity_id": listing.id,
                "score": round(0.5 + 0.4 * (counts.get(listing.id, 0) / max_count), 4),
                "reason": f"Trending — saved {counts.get(listing.id, 0)} times this week",
                "source": "trending",
            }
            for listing in listings
        ]

    async def _user_read_book_edition_ids(self, user_id: int) -> list[int]:
        result = await self.session.execute(
            select(ShelfItem.book_edition_id).where(ShelfItem.user_id == user_id).limit(50)
        )
        return [row[0] for row in result.all()]

    async def _user_wishlist_book_edition_ids(self, user_id: int) -> list[int]:
        result = await self.session.execute(
            select(WishlistItem.book_edition_id).where(WishlistItem.user_id == user_id).limit(50)
        )
        return [row[0] for row in result.all()]

    async def _genres_for_book_editions(self, book_edition_ids: list[int]) -> set[str]:
        result = await self.session.execute(
            select(BookEdition.genres).where(BookEdition.id.in_(book_edition_ids))
        )
        genres: set[str] = set()
        for (genre_list,) in result.all():
            if isinstance(genre_list, list):
                genres.update(genre_list)
        return genres


def _deduplicate(recs: list[RecommendationCandidate]) -> list[RecommendationCandidate]:
    seen: set[tuple[str, int]] = set()
    out: list[RecommendationCandidate] = []
    for rec in recs:
        key = (rec["entity_type"], rec["entity_id"])
        if key not in seen:
            seen.add(key)
            out.append(rec)
    return out

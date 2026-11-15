from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from oldpages_api.catalog.models import (
    AcademicMetadata,
    Author,
    Book,
    BookAuthor,
    BookCategory,
    BookEdition,
    BookIdentifier,
    Category,
    Publisher,
)
from oldpages_api.identity.models import AuditLog, User
from oldpages_api.listings.models import (
    Listing,
    ListingCondition,
    ListingDeliveryMethod,
    ListingImage,
    ListingInventory,
    ListingLocation,
    MediaAsset,
)
from oldpages_api.search.models import (
    Follow,
    ListingFavorite,
    SavedSearch,
    SearchMatchNotification,
    SearchQueryLog,
    WishlistItem,
)
from oldpages_api.search.query import (
    after_cursor,
    decode_cursor,
    encode_cursor,
    favorite_totals,
    search_base,
    search_conditions,
    sort_order,
)
from oldpages_api.search.schemas import ListingSearchFilters


@dataclass(frozen=True, slots=True)
class SearchPage:
    listings: list[Listing]
    favorite_counts: dict[int, int]
    next_cursor: str | None
    total: int


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_listing_page(self, filters: ListingSearchFilters) -> SearchPage:
        dialect = self.dialect_name
        conditions = search_conditions(filters, dialect)
        favorites_table = favorite_totals()
        favorites = func.coalesce(favorites_table.c.total, 0)
        sort_value, descending = sort_order(filters, favorites, dialect)

        stmt = (
            search_base(Listing.id, sort_value.label("sort_value"))
            .outerjoin(favorites_table, favorites_table.c.listing_id == Listing.id)
            .where(*conditions)
        )
        total: int | None = None  # counted once, on the first page
        if filters.cursor:
            value, listing_id, total = decode_cursor(filters.cursor, filters.sort)
            stmt = stmt.where(after_cursor(sort_value, descending, value, listing_id))
        if descending:
            stmt = stmt.order_by(sort_value.desc(), Listing.id.desc())
        else:
            stmt = stmt.order_by(sort_value.asc(), Listing.id.asc())
        rows = (await self.session.execute(stmt.limit(filters.limit + 1))).all()

        if total is None:
            total = await self.count_matching(filters)
        next_cursor = None
        if len(rows) > filters.limit:
            rows = rows[: filters.limit]
            last_id, last_value = rows[-1]
            next_cursor = encode_cursor(filters.sort, last_value, last_id, total)
        ids = [row[0] for row in rows]
        return SearchPage(
            listings=await self.listings_in_order(ids),
            favorite_counts=await self.favorite_counts(ids),
            next_cursor=next_cursor,
            total=total,
        )

    async def count_matching(
        self, filters: ListingSearchFilters, published_after: datetime | None = None
    ) -> int:
        matching = search_base(Listing.id).where(*search_conditions(filters, self.dialect_name))
        if published_after is not None:
            matching = matching.where(Listing.published_at > published_after)
        total = await self.session.scalar(select(func.count()).select_from(matching.subquery()))
        return int(total or 0)

    async def listings_in_order(self, ids: Sequence[int]) -> list[Listing]:
        if not ids:
            return []
        result = await self.session.execute(
            select(Listing).options(*search_listing_load_options()).where(Listing.id.in_(ids))
        )
        by_id = {listing.id: listing for listing in result.scalars().all()}
        return [by_id[listing_id] for listing_id in ids if listing_id in by_id]

    async def favorite_counts(self, listing_ids: Sequence[int]) -> dict[int, int]:
        if not listing_ids:
            return {}
        result = await self.session.execute(
            select(ListingFavorite.listing_id, func.count(ListingFavorite.id))
            .where(ListingFavorite.listing_id.in_(listing_ids))
            .group_by(ListingFavorite.listing_id)
        )
        return {listing_id: count for listing_id, count in result.all()}

    async def suggestions(self, query: str, limit: int) -> list[tuple[str, str]]:
        active_listing_ids = select(Listing.id).where(Listing.status == "active")
        pattern = f"{query.lower()}%"
        suggestions: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()

        async def collect(stmt: Select[str], suggestion_type: str) -> None:
            if len(suggestions) >= limit:
                return
            result = await self.session.execute(stmt.limit(limit))
            for (text,) in result.all():
                if not text:
                    continue
                key = (suggestion_type, text.lower())
                if key in seen:
                    continue
                seen.add(key)
                suggestions.append((suggestion_type, text))
                if len(suggestions) >= limit:
                    break

        await collect(
            select(BookEdition.title)
            .join(Listing, Listing.book_edition_id == BookEdition.id)
            .where(Listing.id.in_(active_listing_ids), func.lower(BookEdition.title).like(pattern))
            .order_by(BookEdition.title),
            "title",
        )
        await collect(
            select(Author.name)
            .join(BookAuthor, BookAuthor.author_id == Author.id)
            .join(Book, Book.id == BookAuthor.book_id)
            .join(BookEdition, BookEdition.book_id == Book.id)
            .join(Listing, Listing.book_edition_id == BookEdition.id)
            .where(Listing.id.in_(active_listing_ids), func.lower(Author.name).like(pattern))
            .order_by(Author.name),
            "author",
        )
        await collect(
            select(BookIdentifier.identifier_value)
            .join(BookEdition, BookEdition.id == BookIdentifier.book_edition_id)
            .join(Listing, Listing.book_edition_id == BookEdition.id)
            .where(
                Listing.id.in_(active_listing_ids),
                func.lower(BookIdentifier.identifier_value).like(pattern),
            )
            .order_by(BookIdentifier.identifier_value),
            "isbn",
        )
        await collect(
            select(Category.name)
            .join(BookCategory, BookCategory.category_id == Category.id)
            .join(Book, Book.id == BookCategory.book_id)
            .join(BookEdition, BookEdition.book_id == Book.id)
            .join(Listing, Listing.book_edition_id == BookEdition.id)
            .where(Listing.id.in_(active_listing_ids), func.lower(Category.name).like(pattern))
            .order_by(Category.name),
            "category",
        )
        await collect(
            select(ListingLocation.public_area)
            .join(Listing, Listing.id == ListingLocation.listing_id)
            .where(
                Listing.id.in_(active_listing_ids),
                func.lower(ListingLocation.public_area).like(pattern),
            )
            .order_by(ListingLocation.public_area),
            "location",
        )
        return suggestions

    async def get_book_edition_by_public_id(self, public_id: str) -> BookEdition | None:
        result = await self.session.execute(
            select(BookEdition)
            .options(*book_summary_load_options())
            .where(BookEdition.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_listing_by_public_id(self, public_id: str) -> Listing | None:
        result = await self.session.execute(
            select(Listing)
            .options(*search_listing_load_options())
            .where(Listing.public_id == public_id, Listing.status != "deleted")
        )
        return result.unique().scalar_one_or_none()

    async def get_user_by_public_id(self, public_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_author_by_public_id(self, public_id: str) -> Author | None:
        result = await self.session.execute(select(Author).where(Author.public_id == public_id))
        return result.scalar_one_or_none()

    async def get_saved_search_by_name(self, user_id: int, name: str) -> SavedSearch | None:
        result = await self.session.execute(
            select(SavedSearch).where(SavedSearch.user_id == user_id, SavedSearch.name == name)
        )
        return result.scalar_one_or_none()

    async def list_saved_searches(self, user_id: int) -> list[SavedSearch]:
        result = await self.session.execute(
            select(SavedSearch)
            .where(SavedSearch.user_id == user_id)
            .order_by(SavedSearch.created_at.desc(), SavedSearch.id.desc())
        )
        return list(result.scalars().all())

    async def get_wishlist_item(self, user_id: int, book_edition_id: int) -> WishlistItem | None:
        result = await self.session.execute(
            select(WishlistItem)
            .options(selectinload(WishlistItem.book_edition).selectinload(BookEdition.book))
            .where(
                WishlistItem.user_id == user_id,
                WishlistItem.book_edition_id == book_edition_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_listing_favorite(self, user_id: int, listing_id: int) -> ListingFavorite | None:
        result = await self.session.execute(
            select(ListingFavorite).where(
                ListingFavorite.user_id == user_id,
                ListingFavorite.listing_id == listing_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_follow(self, user_id: int, target_type: str, target_id: str) -> Follow | None:
        result = await self.session.execute(
            select(Follow).where(
                Follow.user_id == user_id,
                Follow.target_type == target_type,
                Follow.target_id == target_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_follow_by_public_id(self, public_id: str) -> Follow | None:
        result = await self.session.execute(select(Follow).where(Follow.public_id == public_id))
        return result.scalar_one_or_none()

    def add(self, instance: object) -> None:
        self.session.add(instance)

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    @property
    def dialect_name(self) -> str:
        return self.session.get_bind().dialect.name


def search_listing_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(Listing.book_edition).selectinload(BookEdition.identifiers),
        selectinload(Listing.book_edition).selectinload(BookEdition.publisher),
        selectinload(Listing.book_edition).selectinload(BookEdition.academic_metadata),
        selectinload(Listing.book_edition)
        .selectinload(BookEdition.book)
        .selectinload(Book.authors)
        .selectinload(BookAuthor.author),
        selectinload(Listing.book_edition)
        .selectinload(BookEdition.book)
        .selectinload(Book.categories)
        .selectinload(BookCategory.category),
        selectinload(Listing.condition),
        selectinload(Listing.delivery_methods),
        selectinload(Listing.images).selectinload(ListingImage.media_asset),
        selectinload(Listing.inventory),
        selectinload(Listing.location),
        selectinload(Listing.seller),
    )


def book_summary_load_options() -> tuple[ExecutableOption, ...]:
    return (
        selectinload(BookEdition.identifiers),
        selectinload(BookEdition.book).selectinload(Book.authors).selectinload(BookAuthor.author),
        selectinload(BookEdition.book)
        .selectinload(Book.categories)
        .selectinload(BookCategory.category),
    )


__all__ = [
    "AcademicMetadata",
    "AuditLog",
    "Author",
    "Book",
    "BookAuthor",
    "BookCategory",
    "BookEdition",
    "BookIdentifier",
    "Category",
    "Follow",
    "Listing",
    "ListingCondition",
    "ListingDeliveryMethod",
    "ListingFavorite",
    "ListingImage",
    "ListingInventory",
    "ListingLocation",
    "MediaAsset",
    "Publisher",
    "SavedSearch",
    "SearchMatchNotification",
    "SearchQueryLog",
    "SearchRepository",
    "WishlistItem",
]

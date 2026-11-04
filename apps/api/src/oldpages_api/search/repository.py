from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, and_, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.types import UserDefinedType

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
from oldpages_api.search.schemas import ListingSearchFilters


class Geography(UserDefinedType[Any]):
    cache_ok = True

    def get_col_spec(self, **kw: Any) -> str:  # noqa: ANN401
        return "geography"


# Common Indian city name aliases (English ↔ local). Lookups in either direction
# should also match the other; searching "Bangalore" should return "Bengaluru"
# listings, and vice-versa. Extend this list as more cities appear.
_CITY_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("bangalore", "bengaluru"),
    ("bombay", "mumbai"),
    ("madras", "chennai"),
    ("calcutta", "kolkata"),
    ("cochin", "kochi"),
    ("trivandrum", "thiruvananthapuram"),
    ("pondicherry", "puducherry"),
    ("gurgaon", "gurugram"),
    ("mysore", "mysuru"),
    ("mangalore", "mangaluru"),
    ("baroda", "vadodara"),
    ("poona", "pune"),
    ("simla", "shimla"),
    ("benares", "banaras", "varanasi"),
    ("cawnpore", "kanpur"),
)

CITY_ALIASES: dict[str, tuple[str, ...]] = {
    alias: group for group in _CITY_ALIAS_GROUPS for alias in group
}


def expand_city_aliases(value: str) -> tuple[str, ...]:
    """Return the input plus any alternate spellings from CITY_ALIASES."""
    key = value.strip().lower()
    return CITY_ALIASES.get(key, (key,))


class SearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_listing_candidates(self, filters: ListingSearchFilters) -> list[Listing]:
        stmt = base_listing_query().where(
            Listing.status == "active",
            Listing.deleted_at.is_(None),
            ListingInventory.quantity_available > 0,
            Listing.visibility == "public",
        )
        stmt = apply_text_filters(stmt, filters)
        stmt = apply_structured_filters(stmt, filters)
        if self.dialect_name == "postgresql":
            stmt = apply_postgis_radius_filter(stmt, filters)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

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

        async def collect(stmt: Select[tuple[str]], suggestion_type: str) -> None:
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


def base_listing_query() -> Select[tuple[Listing]]:
    return (
        select(Listing)
        .join(ListingLocation, ListingLocation.listing_id == Listing.id)
        .join(ListingInventory, ListingInventory.listing_id == Listing.id)
        .join(BookEdition, BookEdition.id == Listing.book_edition_id)
        .join(Book, Book.id == BookEdition.book_id)
        .outerjoin(ListingCondition, ListingCondition.listing_id == Listing.id)
        .outerjoin(ListingDeliveryMethod, ListingDeliveryMethod.listing_id == Listing.id)
        .outerjoin(BookIdentifier, BookIdentifier.book_edition_id == BookEdition.id)
        .outerjoin(Publisher, Publisher.id == BookEdition.publisher_id)
        .outerjoin(AcademicMetadata, AcademicMetadata.book_edition_id == BookEdition.id)
        .outerjoin(BookAuthor, BookAuthor.book_id == Book.id)
        .outerjoin(Author, Author.id == BookAuthor.author_id)
        .outerjoin(BookCategory, BookCategory.book_id == Book.id)
        .outerjoin(Category, Category.id == BookCategory.category_id)
        .options(*search_listing_load_options())
    )


def apply_text_filters(
    stmt: Select[tuple[Listing]],
    filters: ListingSearchFilters,
) -> Select[tuple[Listing]]:
    if filters.q:
        needle = f"%{filters.q.lower()}%"
        # If the query is a known city alias, also match its alternate spellings
        # (e.g. searching "Bangalore" also matches "Bengaluru").
        city_needles = tuple(f"%{alias}%" for alias in expand_city_aliases(filters.q))
        city_or_state_clauses = [
            lower_contains(ListingLocation.city, alias) for alias in city_needles
        ] + [lower_contains(ListingLocation.state, alias) for alias in city_needles]
        stmt = stmt.where(
            or_(
                lower_contains(Listing.title_snapshot, needle),
                lower_contains(Listing.description, needle),
                lower_contains(BookEdition.title, needle),
                lower_contains(BookEdition.subtitle, needle),
                lower_contains(BookEdition.description, needle),
                lower_contains(Book.title, needle),
                lower_contains(Book.subtitle, needle),
                lower_contains(Author.name, needle),
                lower_contains(BookIdentifier.identifier_value, needle),
                lower_contains(Publisher.name, needle),
                lower_contains(Category.name, needle),
                lower_contains(Category.slug, needle),
                lower_contains(AcademicMetadata.school_board, needle),
                lower_contains(AcademicMetadata.college, needle),
                lower_contains(AcademicMetadata.university, needle),
                lower_contains(AcademicMetadata.course, needle),
                lower_contains(AcademicMetadata.exam, needle),
                *city_or_state_clauses,
                lower_contains(ListingLocation.neighborhood, needle),
                lower_contains(ListingLocation.public_area, needle),
                lower_contains(ListingLocation.country, needle),
            )
        )
    if filters.isbn:
        needle = f"%{filters.isbn.lower().replace('-', '').replace(' ', '')}%"
        stmt = stmt.where(lower_contains(BookIdentifier.identifier_value, needle))
    return stmt


def apply_structured_filters(
    stmt: Select[tuple[Listing]],
    filters: ListingSearchFilters,
) -> Select[tuple[Listing]]:
    if filters.min_price_amount_cents is not None:
        stmt = stmt.where(Listing.price_amount_cents >= filters.min_price_amount_cents)
    if filters.max_price_amount_cents is not None:
        stmt = stmt.where(Listing.price_amount_cents <= filters.max_price_amount_cents)
    if filters.free_only:
        stmt = stmt.where(
            or_(Listing.price_amount_cents.is_(None), Listing.price_amount_cents == 0)
        )
    if filters.city:
        needles = tuple(f"%{alias}%" for alias in expand_city_aliases(filters.city))
        stmt = stmt.where(
            or_(*(lower_contains(ListingLocation.city, alias) for alias in needles))
        )
    if filters.state:
        stmt = stmt.where(lower_contains(ListingLocation.state, f"%{filters.state.lower()}%"))
    if filters.country:
        stmt = stmt.where(lower_contains(ListingLocation.country, f"%{filters.country.lower()}%"))
    if filters.condition:
        stmt = stmt.where(ListingCondition.condition == filters.condition)
    if filters.language:
        stmt = stmt.where(BookEdition.language == filters.language)
    if filters.category:
        needle = f"%{filters.category.lower()}%"
        stmt = stmt.where(
            or_(lower_contains(Category.slug, needle), lower_contains(Category.name, needle))
        )
    if filters.author:
        stmt = stmt.where(lower_contains(Author.name, f"%{filters.author.lower()}%"))
    if filters.publisher:
        stmt = stmt.where(lower_contains(Publisher.name, f"%{filters.publisher.lower()}%"))
    if filters.publication_year is not None:
        stmt = stmt.where(BookEdition.publication_year == filters.publication_year)
    if filters.format:
        stmt = stmt.where(BookEdition.format == filters.format)
    if filters.negotiable is not None:
        stmt = stmt.where(Listing.negotiable.is_(filters.negotiable))
    if filters.campus_pickup is not None:
        stmt = stmt.where(ListingLocation.campus_pickup.is_(filters.campus_pickup))
    if filters.signed_copy is not None:
        stmt = stmt.where(ListingCondition.signed_by_author.is_(filters.signed_copy))
    if filters.first_edition is not None:
        stmt = stmt.where(ListingCondition.first_edition.is_(filters.first_edition))
    return stmt


def apply_postgis_radius_filter(
    stmt: Select[tuple[Listing]],
    filters: ListingSearchFilters,
) -> Select[tuple[Listing]]:
    if filters.latitude is None or filters.longitude is None or filters.distance_km is None:
        return stmt
    origin_point = func.ST_SetSRID(
        func.ST_MakePoint(filters.longitude, filters.latitude),
        4326,
    ).cast(Geography())
    # Use the generated `geog` column added in migration 0022 so the GIST index is picked up.
    listing_geog = literal_column("listing_locations.geog")
    return stmt.where(
        and_(
            ListingLocation.public_latitude.is_not(None),
            ListingLocation.public_longitude.is_not(None),
            func.ST_DWithin(listing_geog, origin_point, filters.distance_km * 1000),
        )
    )


def lower_contains(column: Any, needle: str) -> Any:  # noqa: ANN401
    return func.lower(func.coalesce(column, "")).like(needle)


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

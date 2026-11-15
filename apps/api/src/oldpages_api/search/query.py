"""Listing search as SQL: every filter, the sort and the page boundary run in the database.

Only the page of listings being shown is loaded into Python. Paging is keyset-based: the
cursor holds the last row's sort value and id, so page 50 costs the same as page 1.
"""

from __future__ import annotations

import base64
import json
import math
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Float,
    Select,
    Text,
    case,
    cast,
    exists,
    func,
    literal,
    literal_column,
    or_,
    select,
    tuple_,
    union,
)
from sqlalchemy.dialects.postgresql import JSONB, array
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement
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
from oldpages_api.identity.models import User
from oldpages_api.listings.models import (
    Listing,
    ListingCondition,
    ListingDeliveryMethod,
    ListingImage,
    ListingInventory,
    ListingLocation,
)
from oldpages_api.search.exceptions import SearchValidationError
from oldpages_api.search.models import ListingFavorite
from oldpages_api.search.schemas import ListingSearchFilters, SearchSort

EARTH_RADIUS_KM = 6371.0088
NO_DISTANCE_KM = 1_000_000.0  # sorts listings without coordinates after every real distance

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

# Common Indian city name aliases (English ↔ local). Searching "Bangalore" should also
# return "Bengaluru" listings, and vice-versa. Extend this list as more cities appear.
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

# A second handle on categories for the listing's own category, so subqueries on it
# aren't tied to the book-category subqueries.
ListingCategory = aliased(Category)


class Geography(UserDefinedType[Any]):
    cache_ok = True

    def get_col_spec(self, **kw: Any) -> str:  # noqa: ANN401
        return "geography"


def expand_city_aliases(value: str) -> tuple[str, ...]:
    """Return the input plus any alternate spellings from CITY_ALIASES."""
    key = value.strip().lower()
    return CITY_ALIASES.get(key, (key,))


def lower_contains(column: Any, needle: str) -> ColumnElement[bool]:  # noqa: ANN401
    return func.lower(func.coalesce(column, "")).like(needle)


def search_base(*columns: Any) -> Select[Any]:  # noqa: ANN401
    """Listing plus its one-to-one rows, so no join multiplies the result."""
    return (
        select(*columns)
        .select_from(Listing)
        .join(ListingLocation, ListingLocation.listing_id == Listing.id)
        .join(ListingInventory, ListingInventory.listing_id == Listing.id)
        .join(BookEdition, BookEdition.id == Listing.book_edition_id)
        .join(Book, Book.id == BookEdition.book_id)
        .outerjoin(ListingCondition, ListingCondition.listing_id == Listing.id)
    )


def distance_km(filters: ListingSearchFilters) -> ColumnElement[float] | None:
    """Haversine distance from the reader, in km; the same formula the results display."""
    if filters.latitude is None or filters.longitude is None:
        return None
    lat0 = math.radians(filters.latitude)
    lon0 = math.radians(filters.longitude)
    lat = func.radians(ListingLocation.public_latitude)
    lon = func.radians(ListingLocation.public_longitude)
    half_dlat = func.sin((lat - lat0) / 2)
    half_dlon = func.sin((lon - lon0) / 2)
    a = half_dlat * half_dlat + math.cos(lat0) * func.cos(lat) * half_dlon * half_dlon
    a = case((a > 1.0, 1.0), else_=a)  # rounding can push it a hair past asin's domain
    return cast(2 * EARTH_RADIUS_KM * func.asin(func.sqrt(a)), Float)


def search_conditions(filters: ListingSearchFilters, dialect: str) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [
        Listing.status == "active",
        Listing.deleted_at.is_(None),
        Listing.visibility == "public",
        ListingInventory.quantity_available > 0,
    ]
    if filters.q:
        conditions.append(text_match(filters.q))
    if filters.isbn:
        needle = f"%{filters.isbn.lower().replace('-', '').replace(' ', '')}%"
        conditions.append(
            BookEdition.id.in_(
                select(BookIdentifier.book_edition_id).where(
                    lower_contains(BookIdentifier.identifier_value, needle)
                )
            )
        )
    if filters.min_price_amount_cents is not None:
        conditions.append(Listing.price_amount_cents >= filters.min_price_amount_cents)
    if filters.max_price_amount_cents is not None:
        conditions.append(Listing.price_amount_cents <= filters.max_price_amount_cents)
    if filters.currency:
        conditions.append(Listing.currency == filters.currency)
    if filters.exclude_seller_id:
        own = select(User.id).where(User.public_id == filters.exclude_seller_id)
        conditions.append(Listing.seller_user_id.not_in(own))
    if filters.seller_id:
        seller = select(User.id).where(User.public_id == filters.seller_id)
        conditions.append(Listing.seller_user_id.in_(seller))
    if filters.free_only:
        conditions.append(
            or_(Listing.price_amount_cents.is_(None), Listing.price_amount_cents == 0)
        )
    if filters.city:
        needles = [f"%{alias}%" for alias in expand_city_aliases(filters.city)]
        conditions.append(or_(*(lower_contains(ListingLocation.city, n) for n in needles)))
    if filters.state:
        conditions.append(lower_contains(ListingLocation.state, f"%{filters.state.lower()}%"))
    if filters.country:
        conditions.append(lower_contains(ListingLocation.country, f"%{filters.country.lower()}%"))
    if filters.condition:
        conditions.append(ListingCondition.condition == filters.condition)
    if filters.language:
        conditions.append(BookEdition.language == filters.language)
    if filters.category:
        conditions.append(category_match(filters.category))
    if filters.author:
        conditions.append(Book.id.in_(books_by_author(f"%{filters.author.lower()}%")))
    if filters.publisher:
        conditions.append(
            BookEdition.publisher_id.in_(
                select(Publisher.id).where(
                    lower_contains(Publisher.name, f"%{filters.publisher.lower()}%")
                )
            )
        )
    if filters.publication_year is not None:
        conditions.append(BookEdition.publication_year == filters.publication_year)
    if filters.format:
        conditions.append(BookEdition.format == filters.format)
    if filters.negotiable is not None:
        conditions.append(Listing.negotiable.is_(filters.negotiable))
    if filters.campus_pickup is not None:
        conditions.append(ListingLocation.campus_pickup.is_(filters.campus_pickup))
    if filters.signed_copy is not None:
        conditions.append(ListingCondition.signed_by_author.is_(filters.signed_copy))
    if filters.first_edition is not None:
        conditions.append(ListingCondition.first_edition.is_(filters.first_edition))
    if filters.listing_mode:
        conditions.append(has_any_mode([filters.listing_mode], dialect))
    if filters.excluded_modes:
        conditions.append(~has_any_mode(filters.excluded_modes, dialect))
    if filters.delivery_method:
        conditions.append(
            exists().where(
                ListingDeliveryMethod.listing_id == Listing.id,
                ListingDeliveryMethod.method == filters.delivery_method,
                ListingDeliveryMethod.enabled.is_(True),
            )
        )
    if filters.actual_photos:
        conditions.append(exists().where(ListingImage.listing_id == Listing.id))
    distance = distance_km(filters)
    if distance is not None and filters.distance_km is not None:
        if dialect == "postgresql":
            # Narrows to the radius with the GIST index on the geog column (migration 0022).
            origin = func.ST_SetSRID(
                func.ST_MakePoint(filters.longitude, filters.latitude), 4326
            ).cast(Geography())
            conditions.append(
                func.ST_DWithin(
                    literal_column("listing_locations.geog"), origin, filters.distance_km * 1000
                )
            )
        conditions.append(distance <= filters.distance_km)
    return conditions


def text_match(q: str) -> ColumnElement[bool]:
    """Listings whose text matches, gathered per table so each lookup can use its index."""
    needle = f"%{q.lower()}%"
    city_needles = [f"%{alias}%" for alias in expand_city_aliases(q)]
    listing_hits = union(
        select(Listing.id).where(
            or_(
                lower_contains(Listing.title_snapshot, needle),
                lower_contains(Listing.description, needle),
            )
        ),
        # The seller's category; its slug carries the path ("...cbse.class-10.physics").
        select(Listing.id).where(
            Listing.category_id.in_(
                select(ListingCategory.id).where(
                    or_(
                        lower_contains(ListingCategory.name, needle),
                        lower_contains(ListingCategory.slug, needle.replace(" ", "-")),
                    )
                )
            )
        ),
        select(ListingLocation.listing_id).where(
            or_(
                *(lower_contains(ListingLocation.city, n) for n in city_needles),
                *(lower_contains(ListingLocation.state, n) for n in city_needles),
                lower_contains(ListingLocation.neighborhood, needle),
                lower_contains(ListingLocation.public_area, needle),
                lower_contains(ListingLocation.country, needle),
            )
        ),
    )
    book_hits = union(
        select(Book.id).where(
            or_(lower_contains(Book.title, needle), lower_contains(Book.subtitle, needle))
        ),
        books_by_author(needle),
        select(BookCategory.book_id)
        .join(Category, Category.id == BookCategory.category_id)
        .where(or_(lower_contains(Category.name, needle), lower_contains(Category.slug, needle))),
    )
    edition_hits = union(
        select(BookEdition.id).where(
            or_(
                lower_contains(BookEdition.title, needle),
                lower_contains(BookEdition.subtitle, needle),
                lower_contains(BookEdition.description, needle),
                BookEdition.publisher_id.in_(
                    select(Publisher.id).where(lower_contains(Publisher.name, needle))
                ),
            )
        ),
        select(BookIdentifier.book_edition_id).where(
            lower_contains(BookIdentifier.identifier_value, needle)
        ),
        select(AcademicMetadata.book_edition_id).where(
            or_(
                lower_contains(AcademicMetadata.school_board, needle),
                lower_contains(AcademicMetadata.college, needle),
                lower_contains(AcademicMetadata.university, needle),
                lower_contains(AcademicMetadata.course, needle),
                lower_contains(AcademicMetadata.exam, needle),
            )
        ),
    )
    return or_(
        Listing.id.in_(listing_hits),
        BookEdition.id.in_(edition_hits),
        Book.id.in_(book_hits),
    )


def books_by_author(needle: str) -> Select[Any]:
    return (
        select(BookAuthor.book_id)
        .join(Author, Author.id == BookAuthor.author_id)
        .where(lower_contains(Author.name, needle))
    )


def category_match(category: str) -> ColumnElement[bool]:
    slug = category.lower()
    needle = f"%{slug}%"
    # The listing's own category or anything below it, or a matching book category.
    in_subtree = select(ListingCategory.id).where(
        or_(ListingCategory.slug == slug, ListingCategory.slug.like(f"{slug}.%"))
    )
    return or_(
        Listing.category_id.in_(in_subtree),
        Book.id.in_(
            select(BookCategory.book_id)
            .join(Category, Category.id == BookCategory.category_id)
            .where(
                or_(lower_contains(Category.slug, needle), lower_contains(Category.name, needle))
            )
        ),
    )


def has_any_mode(modes: list[str], dialect: str) -> ColumnElement[bool]:
    if dialect == "postgresql":
        has_any: ColumnElement[bool] = cast(Listing.listing_modes, JSONB).has_any(
            array(modes, type_=Text)
        )
        return has_any
    entries = func.json_each(Listing.listing_modes).table_valued("value")
    return exists(select(literal(1)).select_from(entries).where(entries.c.value.in_(modes)))


def favorite_totals() -> Any:  # noqa: ANN401
    return (
        select(
            ListingFavorite.listing_id.label("listing_id"),
            func.count(ListingFavorite.id).label("total"),
        )
        .group_by(ListingFavorite.listing_id)
        .subquery("favorite_totals")
    )


def text_score(column: Any, q: str) -> ColumnElement[float]:  # noqa: ANN401
    lowered = func.lower(func.coalesce(column, ""))
    return case((lowered == q, 3.0), (lowered.like(f"%{q}%"), 1.5), else_=0.0)


def relevance(
    filters: ListingSearchFilters,
    favorites: ColumnElement[int],
    distance: ColumnElement[float] | None,
) -> ColumnElement[float]:
    score = cast(Listing.quality_score, Float) / 100.0
    score = score + case((favorites > 20, 20), else_=favorites) * 0.03
    if distance is not None:
        nearness = case((distance >= 100, 0.0), else_=1 - distance / 100.0)
        score = score + func.coalesce(nearness, 0.0) * 0.2
    if filters.q:
        q = filters.q.lower()
        author_exact = Book.id.in_(
            select(BookAuthor.book_id)
            .join(Author, Author.id == BookAuthor.author_id)
            .where(func.lower(Author.name) == q)
        )
        score = (
            score
            + text_score(Listing.title_snapshot, q)
            + text_score(BookEdition.title, q)
            + text_score(Book.title, q)
            + text_score(ListingLocation.city, q)
            + case((lower_contains(Listing.description, f"%{q}%"), 1.5), else_=0.0)
            + case(
                (author_exact, 3.0),
                (Book.id.in_(books_by_author(f"%{q}%")), 1.5),
                else_=0.0,
            )
        )
    return cast(score, Float)


def sort_order(
    filters: ListingSearchFilters,
    favorites: ColumnElement[int],
    dialect: str,
) -> tuple[ColumnElement[Any], bool]:
    """The sort value and whether it runs high-to-low. Listing.id breaks ties the same way."""
    sort: SearchSort = filters.sort
    distance = distance_km(filters)
    if sort == "nearest" and distance is not None:
        return func.coalesce(distance, NO_DISTANCE_KM), False
    if sort == "newest":
        if dialect == "sqlite":
            # SQLite keeps timestamps as text in mixed precisions; compare them as numbers.
            return func.julianday(Listing.created_at), True
        return Listing.created_at.expression, True
    if sort == "lowest_price":
        return func.coalesce(Listing.price_amount_cents, 0), False
    if sort == "highest_price":
        return func.coalesce(Listing.price_amount_cents, -1), True
    if sort == "best_condition":
        rank = case(
            *(
                (ListingCondition.condition == name, value)
                for name, value in CONDITION_RANK.items()
            ),
            else_=0,
        )
        return rank, True
    if sort == "most_saved":
        return favorites, True
    return relevance(filters, favorites, distance), True


def encode_cursor(sort: str, value: Any, listing_id: int, total: int) -> str:  # noqa: ANN401
    """Opaque page token: the last row's sort value and id, plus the first page's count."""
    if isinstance(value, datetime):
        value = {"dt": value.isoformat()}
    payload = {"s": sort, "v": value, "id": listing_id, "n": total}
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def decode_cursor(cursor: str, sort: str) -> tuple[Any, int, int]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        value, listing_id, total = payload["v"], payload["id"], payload["n"]
        if payload["s"] != sort or not isinstance(listing_id, int) or not isinstance(total, int):
            raise ValueError
        if isinstance(value, dict):
            value = datetime.fromisoformat(value["dt"])
        elif not isinstance(value, int | float):
            raise ValueError
    except (ValueError, KeyError, TypeError) as exc:
        raise SearchValidationError("Invalid search cursor.") from exc
    return value, listing_id, total


def after_cursor(
    sort_value: ColumnElement[Any],
    descending: bool,
    value: Any,
    listing_id: int,  # noqa: ANN401
) -> ColumnElement[bool]:
    row, boundary = tuple_(sort_value, Listing.id), tuple_(literal(value), literal(listing_id))
    return row < boundary if descending else row > boundary


__all__ = [
    "CONDITION_RANK",
    "after_cursor",
    "decode_cursor",
    "encode_cursor",
    "favorite_totals",
    "search_base",
    "search_conditions",
    "sort_order",
]

"""Seed 3 users in different Indian cities with 3 listings each — for exercising
the location switcher & radius filter.

Run inside the api container:
    docker compose exec api python -m oldpages_api.scripts.seed_locations
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.catalog.repository import CatalogRepository
from oldpages_api.catalog.schemas import (
    AuthorInput,
    BookCreateRequest,
    PublisherInput,
)
from oldpages_api.catalog.service import CatalogService
from oldpages_api.core.config import get_settings
from oldpages_api.identity.models import User, UserPreference, UserProfile
from oldpages_api.identity.repository import IdentityRepository
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.identity.security import hash_password, utc_now
from oldpages_api.listings.models import Listing, MediaAsset
from oldpages_api.listings.schemas import (
    ListingConditionInput,
    ListingCreateRequest,
    ListingDeliveryMethodInput,
    ListingImageInput,
    ListingLocationInput,
)
from oldpages_api.listings.service import ListingService
from oldpages_api.shared.db.database import get_session_factory
from oldpages_api.shared.db.ids import new_ulid

DEMO_PASSWORD = "OldPagesDemo!2026"  # noqa: S105


def isbn13(prefix12: str) -> str:
    """Return a valid ISBN-13 by computing the check digit for the 12-digit prefix."""
    assert len(prefix12) == 12 and prefix12.isdigit(), f"bad ISBN prefix: {prefix12!r}"
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(prefix12))
    check = (10 - (total % 10)) % 10
    return prefix12 + str(check)


@dataclass(frozen=True)
class CitySeed:
    city: str
    state: str
    country: str
    latitude: str
    longitude: str
    public_area: str
    neighborhood: str


@dataclass(frozen=True)
class UserSeed:
    email: str
    username: str
    display_name: str
    city: CitySeed


@dataclass(frozen=True)
class BookSeed:
    title: str
    author: str
    isbn_13: str
    publisher: str
    year: int
    language: str
    price_inr: int


CITIES = {
    "hyderabad": CitySeed(
        city="Hyderabad",
        state="Telangana",
        country="IN",
        latitude="17.3850",
        longitude="78.4867",
        public_area="Banjara Hills, Hyderabad",
        neighborhood="Banjara Hills",
    ),
    "bengaluru": CitySeed(
        city="Bengaluru",
        state="Karnataka",
        country="IN",
        latitude="12.9716",
        longitude="77.5946",
        public_area="Indiranagar, Bengaluru",
        neighborhood="Indiranagar",
    ),
    "pune": CitySeed(
        city="Pune",
        state="Maharashtra",
        country="IN",
        latitude="18.5204",
        longitude="73.8567",
        public_area="Koregaon Park, Pune",
        neighborhood="Koregaon Park",
    ),
}


USERS = [
    UserSeed(
        email="arjun.hyd@oldpages.in",
        username="arjun_hyd",
        display_name="Arjun Reddy (Hyderabad)",
        city=CITIES["hyderabad"],
    ),
    UserSeed(
        email="priya.blr@oldpages.in",
        username="priya_blr",
        display_name="Priya Iyer (Bengaluru)",
        city=CITIES["bengaluru"],
    ),
    UserSeed(
        email="rohan.pnq@oldpages.in",
        username="rohan_pnq",
        display_name="Rohan Deshmukh (Pune)",
        city=CITIES["pune"],
    ),
]


# 9 unique books — 3 per user. ISBNs are structurally valid mock values.
BOOKS_BY_CITY = {
    "hyderabad": [
        BookSeed(
            title="The Great Indian Novel",
            author="Shashi Tharoor",
            isbn_13=isbn13("978014012049"),
            publisher="Penguin Books India",
            year=1989,
            language="en",
            price_inr=299,
        ),
        BookSeed(
            title="Train to Pakistan",
            author="Khushwant Singh",
            isbn_13=isbn13("978014100118"),
            publisher="Penguin",
            year=1956,
            language="en",
            price_inr=199,
        ),
        BookSeed(
            title="Sacred Games",
            author="Vikram Chandra",
            isbn_13=isbn13("978006213035"),
            publisher="Harper Perennial",
            year=2006,
            language="en",
            price_inr=499,
        ),
    ],
    "bengaluru": [
        BookSeed(
            title="A Suitable Boy",
            author="Vikram Seth",
            isbn_13=isbn13("978006078652"),
            publisher="Harper Perennial",
            year=1993,
            language="en",
            price_inr=699,
        ),
        BookSeed(
            title="The White Tiger",
            author="Aravind Adiga",
            isbn_13=isbn13("978141656260"),
            publisher="Free Press",
            year=2008,
            language="en",
            price_inr=349,
        ),
        BookSeed(
            title="Midnight's Children",
            author="Salman Rushdie",
            isbn_13=isbn13("978081297653"),
            publisher="Random House",
            year=1981,
            language="en",
            price_inr=449,
        ),
    ],
    "pune": [
        BookSeed(
            title="The God of Small Things",
            author="Arundhati Roy",
            isbn_13=isbn13("978081297965"),
            publisher="Random House",
            year=1997,
            language="en",
            price_inr=349,
        ),
        BookSeed(
            title="Interpreter of Maladies",
            author="Jhumpa Lahiri",
            isbn_13=isbn13("978061810136"),
            publisher="Mariner Books",
            year=1999,
            language="en",
            price_inr=299,
        ),
        BookSeed(
            title="Shantaram",
            author="Gregory David Roberts",
            isbn_13=isbn13("978031233052"),
            publisher="St. Martin's Griffin",
            year=2003,
            language="en",
            price_inr=599,
        ),
    ],
}


async def ensure_user(session: AsyncSession, seed: UserSeed) -> User:
    repo = IdentityRepository(session)
    existing = await repo.get_user_by_email(seed.email)
    if existing is not None:
        print(f"  · user already exists: {seed.email}")
        return existing
    user = User(
        email=seed.email,
        email_verified_at=utc_now(),
        password_hash=hash_password(DEMO_PASSWORD),
        status="active",
    )
    repo.add(user)
    await repo.flush()
    repo.add(UserProfile(user_id=user.id, display_name=seed.display_name, username=seed.username))
    repo.add(UserPreference(user_id=user.id))
    await repo.commit()
    print(f"  ✓ created user: {seed.email} / {DEMO_PASSWORD}")
    return user


async def ensure_book(session: AsyncSession, actor: User, seed: BookSeed) -> tuple[str, int]:
    """Return (public_id, internal_id) of the book edition."""
    repo = CatalogRepository(session)
    existing = await repo.get_edition_by_identifier("isbn13", seed.isbn_13)
    if existing is not None:
        return existing.public_id, existing.id
    await CatalogService(session).create_book(
        BookCreateRequest(
            authors=[AuthorInput(name=seed.author)],
            description=f"Seeded copy of '{seed.title}' by {seed.author}.",
            edition="Paperback",
            format="paperback",
            isbn_13=seed.isbn_13,
            language=seed.language,
            page_count=300,
            publication_year=seed.year,
            publisher=PublisherInput(name=seed.publisher),
            title=seed.title,
        ),
        actor,
        AuthenticatedRequestContext(),
    )
    edition = await repo.get_edition_by_identifier("isbn13", seed.isbn_13)
    if edition is None:  # pragma: no cover — sanity
        raise RuntimeError(f"Failed to insert book '{seed.title}'")
    print(f"    · created book: {seed.title} ({seed.isbn_13})")
    return edition.public_id, edition.id


async def ensure_listing(
    session: AsyncSession,
    actor: User,
    edition_public_id: str,
    edition_id: int,
    book: BookSeed,
    city: CitySeed,
) -> None:
    # Idempotency: skip if this seller already has an active listing for this edition.
    existing = await session.execute(
        select(Listing).where(
            Listing.seller_user_id == actor.id,
            Listing.book_edition_id == edition_id,
            Listing.status == "active",
        )
    )
    if existing.scalar_one_or_none() is not None:
        print(f"    · already listed: {book.title}")
        return

    media_public_id = new_ulid()
    storage_key = f"seed-loc/{actor.public_id}/{media_public_id}.jpg"
    media = MediaAsset(
        byte_size=256_000,
        content_type="image/jpeg",
        original_filename=f"{book.isbn_13}.jpg",
        public_id=media_public_id,
        public_url=f"http://localhost:9000/oldpages-media/{storage_key}",
        status="approved",
        storage_key=storage_key,
        upload_expires_at=utc_now() + timedelta(minutes=15),
        user_id=actor.id,
    )
    session.add(media)
    await session.flush()

    service = ListingService(session, get_settings())
    listing = await service.create_listing(
        ListingCreateRequest(
            book_id=edition_public_id,
            condition=ListingConditionInput(condition="very_good"),
            delivery_methods=[ListingDeliveryMethodInput(method="pickup")],
            description=f"Local pickup in {city.city}. Well-loved copy of '{book.title}'.",
            images=[ListingImageInput(media_id=media.public_id, alt_text=book.title)],
            listing_modes=["sell"],
            location=ListingLocationInput(
                campus_pickup=False,
                city=city.city,
                country=city.country,
                exact_latitude=city.latitude,
                exact_longitude=city.longitude,
                neighborhood=city.neighborhood,
                public_area=city.public_area,
                state=city.state,
            ),
            price_amount_cents=book.price_inr * 100,
        ),
        actor,
        AuthenticatedRequestContext(),
    )
    await service.publish_listing(listing.id, actor, AuthenticatedRequestContext())
    print(f"    ✓ listed: {book.title} — ₹{book.price_inr} — {city.city}")


async def run() -> None:
    async with get_session_factory()() as session:
        for user_seed in USERS:
            print(f"\n[{user_seed.city.city}] {user_seed.email}")
            user = await ensure_user(session, user_seed)
            city_key = next(k for k, v in CITIES.items() if v is user_seed.city)
            for book in BOOKS_BY_CITY[city_key]:
                edition_public_id, edition_id = await ensure_book(session, user, book)
                await ensure_listing(
                    session, user, edition_public_id, edition_id, book, user_seed.city
                )

    print("\n" + "=" * 60)
    print("Demo credentials (password: {}):".format(DEMO_PASSWORD))
    print("=" * 60)
    for u in USERS:
        print(f"  {u.email:32s}  {u.city.city:12s}  ({u.city.latitude}, {u.city.longitude})")
    print("\nSwitch cities from the header 📍 and search — you'll see only")
    print("listings within the active radius.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

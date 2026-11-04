from __future__ import annotations

import statistics
import time
from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.catalog.models import Category
from oldpages_api.search.models import SearchQueryLog


@pytest.mark.asyncio
async def test_search_supports_title_author_isbn_category_and_location(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    category_id = await create_category(session_factory, name="Fiction", slug="fiction")
    book = await create_book(
        client,
        token,
        authors=[{"name": "Munshi Premchand"}],
        category_ids=[category_id],
        isbn_13="9780143039433",
        title="Godaan",
    )
    listing = await create_published_listing(client, token, book["id"], city="Pune")

    title_response = await client.get("/api/v1/search/listings", params={"q": "Godaan"})
    author_response = await client.get(
        "/api/v1/search/listings",
        params={"author": "Premchand"},
    )
    isbn_response = await client.get(
        "/api/v1/search/listings",
        params={"isbn": "978-0-1430-3943-3"},
    )
    category_response = await client.get(
        "/api/v1/search/listings",
        params={"category": "fiction"},
    )
    location_response = await client.get(
        "/api/v1/search/listings",
        params={"city": "Pune", "listing_mode": "sell"},
    )

    for response in [
        title_response,
        author_response,
        isbn_response,
        category_response,
        location_response,
    ]:
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["id"] == listing["id"]


@pytest.mark.asyncio
async def test_nearest_sort_uses_public_coordinates_and_hides_exact_location(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    pune_book = await create_book(client, token, title="Nearby Book", isbn_13="9780143039433")
    mumbai_book = await create_book(client, token, title="Farther Book", isbn_13="9780131103627")
    pune_listing = await create_published_listing(
        client,
        token,
        pune_book["id"],
        city="Pune",
        exact_latitude="18.520430",
        exact_longitude="73.856744",
        public_area="Deccan, Pune",
    )
    await create_published_listing(
        client,
        token,
        mumbai_book["id"],
        city="Mumbai",
        exact_latitude="19.076090",
        exact_longitude="72.877426",
        public_area="Fort, Mumbai",
    )

    response = await client.get(
        "/api/v1/search/listings",
        params={
            "latitude": 18.5204,
            "longitude": 73.8567,
            "sort": "nearest",
        },
    )

    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert item["id"] == pune_listing["id"]
    assert item["distance_km"] is not None
    assert "exact_latitude" not in item["location"]
    assert "pickup_notes_private" not in item["location"]


@pytest.mark.asyncio
async def test_zero_result_searches_are_recorded(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    book = await create_book(client, token, title="Visible Book")
    await create_published_listing(client, token, book["id"], city="Pune")

    response = await client.get("/api/v1/search/listings", params={"q": "not-a-real-title"})

    assert response.status_code == 200
    assert response.json()["items"] == []
    async with session_factory() as session:
        result = await session.execute(
            select(SearchQueryLog).where(SearchQueryLog.zero_results.is_(True))
        )
        logs = list(result.scalars().all())
    assert len(logs) == 1
    assert logs[0].query == "not-a-real-title"
    assert logs[0].result_count == 0


@pytest.mark.asyncio
async def test_saved_search_wishlist_favorites_and_follows_require_authentication(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller@example.com", username="seller")
    buyer = await register_user(client, email="buyer@example.com", username="buyer")
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    book = await create_book(client, seller_token, title="Favorite Book")
    listing = await create_published_listing(client, seller_token, book["id"], city="Pune")

    unauthenticated = await client.post(
        "/api/v1/saved-searches",
        json={"name": "Pune books", "query": "Favorite"},
    )
    assert unauthenticated.status_code == 401

    saved_search = await client.post(
        "/api/v1/saved-searches",
        headers=auth(buyer_token),
        json={
            "filters": {"city": "Pune"},
            "name": "Pune books",
            "query": "Favorite",
            "sort": "newest",
        },
    )
    wishlist = await client.post(f"/api/v1/wishlists/{book['id']}", headers=auth(buyer_token))
    favorite = await client.post(
        f"/api/v1/listings/{listing['id']}/favorite",
        headers=auth(buyer_token),
    )
    follow = await client.post(
        "/api/v1/follows",
        headers=auth(buyer_token),
        json={"target_id": seller["user"]["id"], "target_type": "seller"},
    )
    search = await client.get("/api/v1/search/listings", params={"q": "Favorite"})

    assert saved_search.status_code == 201, saved_search.text
    assert saved_search.json()["last_result_count"] == 1
    assert wishlist.status_code == 201, wishlist.text
    assert favorite.status_code == 201, favorite.text
    assert follow.status_code == 201, follow.text
    assert search.status_code == 200
    assert search.json()["items"][0]["favorite_count"] == 1

    assert (
        await client.delete(
            f"/api/v1/listings/{listing['id']}/favorite",
            headers=auth(buyer_token),
        )
    ).status_code == 204
    assert (
        await client.delete(f"/api/v1/wishlists/{book['id']}", headers=auth(buyer_token))
    ).status_code == 204
    assert (
        await client.delete(
            f"/api/v1/follows/{follow.json()['id']}",
            headers=auth(buyer_token),
        )
    ).status_code == 204


@pytest.mark.asyncio
async def test_suggestions_return_autocomplete_matches(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    book = await create_book(
        client,
        token,
        authors=[{"name": "Munshi Premchand"}],
        isbn_13="9780143039433",
        title="Godaan",
    )
    await create_published_listing(client, token, book["id"], city="Pune")

    response = await client.get("/api/v1/search/suggestions", params={"q": "Go"})

    assert response.status_code == 200
    assert {"text": "Godaan", "type": "title"} in response.json()["items"]


@pytest.mark.asyncio
async def test_search_smoke_load_stays_under_documented_p95_target(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    book = await create_book(client, token, title="Load Test Book", isbn_13="9780143039433")
    await create_published_listing(client, token, book["id"], city="Pune")
    latencies: list[float] = []

    for _ in range(20):
        started = time.perf_counter()
        response = await client.get("/api/v1/search/listings", params={"q": "Load Test"})
        latencies.append((time.perf_counter() - started) * 1000)
        assert response.status_code == 200

    p95_ms = statistics.quantiles(latencies, n=20)[18]
    assert p95_ms < 700


async def create_category(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    name: str,
    slug: str,
) -> str:
    async with session_factory() as session:
        category = Category(name=name, slug=slug)
        session.add(category)
        await session.commit()
        return category.public_id


async def create_book(
    client: AsyncClient,
    token: str,
    *,
    authors: list[dict[str, str]] | None = None,
    category_ids: list[str] | None = None,
    isbn_13: str | None = None,
    title: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "academic_metadata": {
            "college": "Fergusson College",
            "course": "Hindi Literature",
            "subject": "Hindi",
        },
        "authors": authors or [{"name": "Search Author"}],
        "category_ids": category_ids or [],
        "description": "A catalog entry for search tests.",
        "format": "paperback",
        "genres": ["Literary Fiction"],
        "language": "en",
        "page_count": 250,
        "publisher": {"name": "Search Publisher"},
        "subjects": ["Indian literature"],
        "title": title,
    }
    if isbn_13 is not None:
        payload["isbn_13"] = isbn_13
    response = await client.post("/api/v1/books", headers=auth(token), json=payload)
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def create_published_listing(
    client: AsyncClient,
    token: str,
    book_id: str,
    *,
    city: str,
    exact_latitude: str = "18.520430",
    exact_longitude: str = "73.856744",
    public_area: str = "Deccan, Pune",
) -> dict[str, Any]:
    media = await upload_media(client, token)
    response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json={
            "book_id": book_id,
            "condition": {
                "condition": "good",
                "damage_details": "Light shelf wear.",
                "highlighting_percent": 5,
            },
            "delivery_methods": [{"method": "pickup"}],
            "description": "A searchable active listing with enough detail for ranking.",
            "images": [{"alt_text": "Actual book cover", "media_id": media["id"]}],
            "listing_modes": ["sell"],
            "location": {
                "campus_pickup": True,
                "city": city,
                "country": "IN",
                "exact_latitude": exact_latitude,
                "exact_longitude": exact_longitude,
                "neighborhood": "Deccan",
                "pickup_notes_private": "Meet at the library gate.",
                "public_area": public_area,
                "state": "Maharashtra",
            },
            "negotiable": True,
            "price_amount_cents": 45000,
            "quantity": 1,
        },
    )
    assert response.status_code == 201, response.text
    listing = response.json()
    publish = await client.post(f"/api/v1/listings/{listing['id']}/publish", headers=auth(token))
    assert publish.status_code == 200, publish.text
    return cast("dict[str, Any]", publish.json())


async def upload_media(client: AsyncClient, token: str) -> dict[str, Any]:
    upload_response = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": "listing.jpg"},
    )
    assert upload_response.status_code == 200, upload_response.text
    media_id = upload_response.json()["id"]
    complete_response = await client.post(
        f"/api/v1/media/{media_id}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete_response.status_code == 200, complete_response.text
    return cast("dict[str, Any]", complete_response.json())


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import auth, create_book, listing_payload, upload_media
from oldpages_api.search.repository import SearchRepository
from oldpages_api.search.schemas import ListingSearchFilters

SEARCH = "/api/v1/search/listings"
PUNE = (18.5204, 73.8567)
MUMBAI = (19.0760, 72.8777)
DELHI = (28.6139, 77.2090)


async def publish(
    client: AsyncClient,
    token: str,
    title: str,
    *,
    price: int | None = 45_000,
    modes: list[str] | None = None,
    condition: str = "good",
    at: tuple[float, float] = PUNE,
    shipping: bool = True,
) -> str:
    book = await create_book(client, token, title=title)
    media = await upload_media(client, token)
    payload = listing_payload(book_id=book["id"], image_id=media["id"])
    payload["price_amount_cents"] = price
    payload["listing_modes"] = modes or ["sell"]
    payload["condition"]["condition"] = condition
    payload["location"]["exact_latitude"] = f"{at[0]:.6f}"
    payload["location"]["exact_longitude"] = f"{at[1]:.6f}"
    if not shipping:
        payload["delivery_methods"] = [{"method": "pickup"}]
    created = await client.post("/api/v1/listings", headers=auth(token), json=payload)
    assert created.status_code == 201, created.text
    published = await client.post(
        f"/api/v1/listings/{created.json()['id']}/publish", headers=auth(token)
    )
    assert published.status_code == 200, published.text
    return str(published.json()["id"])


async def titles(client: AsyncClient, **params: Any) -> list[str]:
    response = await client.get(SEARCH, params=params)
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


@pytest.mark.asyncio
async def test_every_sort_orders_in_the_database(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    await publish(client, token, "Cheap Delhi", price=10_000, condition="acceptable", at=DELHI)
    await publish(client, token, "Free Mumbai", price=None, modes=["donate"], at=MUMBAI)
    await publish(client, token, "Pricey Pune", price=90_000, condition="like_new", at=PUNE)

    assert await titles(client, sort="newest") == ["Pricey Pune", "Free Mumbai", "Cheap Delhi"]
    assert await titles(client, sort="lowest_price") == [
        "Free Mumbai",
        "Cheap Delhi",
        "Pricey Pune",
    ]
    assert (await titles(client, sort="highest_price"))[0] == "Pricey Pune"
    assert (await titles(client, sort="best_condition"))[0] == "Pricey Pune"
    near_pune = {"sort": "nearest", "latitude": PUNE[0], "longitude": PUNE[1]}
    assert await titles(client, **near_pune) == ["Pricey Pune", "Free Mumbai", "Cheap Delhi"]
    assert await titles(client, **near_pune, distance_km=200) == ["Pricey Pune", "Free Mumbai"]


@pytest.mark.asyncio
async def test_relevance_prefers_exact_title_matches(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    await publish(client, token, "Organic Chemistry Workbook")
    await publish(client, token, "Chemistry")

    assert await titles(client, q="chemistry") == ["Chemistry", "Organic Chemistry Workbook"]


@pytest.mark.asyncio
async def test_mode_delivery_and_photo_filters_run_in_sql(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    await publish(client, token, "For Sale")
    await publish(client, token, "Gift", price=None, modes=["donate"], shipping=False)
    await publish(client, token, "Swap", price=None, modes=["exchange"])

    assert await titles(client, listing_mode="donate") == ["Gift"]
    assert sorted(await titles(client, delivery_method="shipping")) == ["For Sale", "Swap"]
    assert len(await titles(client, actual_photos=True)) == 3
    response = await client.get(SEARCH, params={"listing_mode": "donate"})
    assert response.json()["result_count"] == 1

    async with session_factory() as session:  # disabled modes come from settings, not the URL
        hidden = ListingSearchFilters(excluded_modes=["donate", "exchange"])
        assert await SearchRepository(session).count_matching(hidden) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("sort", ["relevance", "newest", "lowest_price", "most_saved"])
async def test_keyset_pages_cover_every_listing_once(
    sort: str, client: AsyncClient, register_user: RegisterUser
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    expected = {await publish(client, token, f"Paged {n}", price=5_000 * (n % 3)) for n in range(7)}

    seen: list[str] = []
    cursor = None
    for _ in range(10):
        params: dict[str, Any] = {"sort": sort, "limit": 3}
        if cursor:
            params["cursor"] = cursor
        body = (await client.get(SEARCH, params=params)).json()
        assert body["result_count"] == 7
        seen.extend(item["id"] for item in body["items"])
        cursor = body["next_cursor"]
        if cursor is None:
            break

    assert len(seen) == 7
    assert set(seen) == expected


@pytest.mark.asyncio
async def test_cursor_is_tied_to_its_sort_and_rejects_garbage(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    token = (await register_user(client))["tokens"]["access_token"]
    for n in range(3):
        await publish(client, token, f"Cursor {n}")
    cursor = (await client.get(SEARCH, params={"sort": "newest", "limit": 1})).json()["next_cursor"]

    other_sort = await client.get(SEARCH, params={"sort": "lowest_price", "cursor": cursor})
    garbage = await client.get(SEARCH, params={"cursor": "not-a-cursor"})

    assert other_sort.status_code == 422
    assert garbage.status_code == 422

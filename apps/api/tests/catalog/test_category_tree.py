from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import auth, create_book, listing_payload, upload_media
from oldpages_api.catalog.models import Category
from oldpages_api.catalog.taxonomy import TAXONOMY, flatten
from oldpages_api.catalog.taxonomy_sync import sync_categories

CLASS_10_PHYSICS = "academic.school.cbse.class-10.science"


async def load_taxonomy(session_factory: async_sessionmaker[AsyncSession]) -> tuple[int, int]:
    async with session_factory() as session:
        result = await session.run_sync(lambda s: sync_categories(s.connection()))
        await session.commit()
        return result


@pytest.mark.asyncio
async def test_sync_is_repeatable(session_factory: async_sessionmaker[AsyncSession]) -> None:
    total = len(flatten())

    assert await load_taxonomy(session_factory) == (total, 0)
    assert await load_taxonomy(session_factory) == (0, total)
    async with session_factory() as session:
        assert await session.scalar(select(func.count(Category.id))) == total


@pytest.mark.asyncio
async def test_levels_list_one_dropdown_per_chosen_step(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await load_taxonomy(session_factory)

    top = (await client.get("/api/v1/categories/levels")).json()
    deep = (await client.get("/api/v1/categories/levels", params={"slug": CLASS_10_PHYSICS})).json()
    leaf_parent = (
        await client.get(
            "/api/v1/categories/levels", params={"slug": "academic.school.cbse.class-10"}
        )
    ).json()
    missing = await client.get("/api/v1/categories/levels", params={"slug": "no.such.thing"})

    assert top["path"] == []
    assert [o["name"] for o in top["levels"][0]["options"]] == [n.name for n in TAXONOMY]
    # A leaf adds no dropdown of its own.
    assert [level["label"] for level in deep["levels"]] == [
        "Category",
        "Type",
        "Board",
        "Class / Grade",
        "Subject",
    ]
    assert [p["name"] for p in deep["path"]] == [
        "Academic & Educational",
        "School Books",
        "CBSE",
        "Class 10",
        "Science",
    ]
    assert leaf_parent["levels"][-1]["parent_slug"] == "academic.school.cbse.class-10"
    assert "Mathematics" in [o["name"] for o in leaf_parent["levels"][-1]["options"]]
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_listing_category_drives_search(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await load_taxonomy(session_factory)
    token = (await register_user(client))["tokens"]["access_token"]
    book = await create_book(client, token, title="Lakhmir Singh Science")
    media = await upload_media(client, token)
    payload = listing_payload(book_id=book["id"], image_id=media["id"])
    payload["category"] = CLASS_10_PHYSICS
    created = await client.post("/api/v1/listings", headers=auth(token), json=payload)
    assert created.status_code == 201, created.text
    published = await client.post(
        f"/api/v1/listings/{created.json()['id']}/publish", headers=auth(token)
    )
    assert published.status_code == 200, published.text
    listing = published.json()

    async def found(**params: Any) -> bool:
        response = await client.get("/api/v1/search/listings", params=params)
        assert response.status_code == 200, response.text
        return listing["id"] in [item["id"] for item in response.json()["items"]]

    assert listing["category"] == {"name": "Science", "slug": CLASS_10_PHYSICS}
    assert await found(category="academic")
    assert await found(category="academic.school.cbse")
    assert await found(category=CLASS_10_PHYSICS)
    assert not await found(category="academic.college")
    assert not await found(category="academic.school.cbse.class-1")  # not a prefix of class-10
    assert await found(q="cbse")
    assert await found(q="class 10")

    cleared = await client.patch(
        f"/api/v1/listings/{listing['id']}", headers=auth(token), json={"category": None}
    )
    bad = await client.patch(
        f"/api/v1/listings/{listing['id']}", headers=auth(token), json={"category": "made.up"}
    )

    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["category"] is None
    assert bad.status_code == 422
    assert not await found(category="academic.school")

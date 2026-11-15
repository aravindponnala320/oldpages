from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from helpers import auth, create_book, create_published_listing, listing_payload, upload_media


async def tokens(client: AsyncClient, register_user: RegisterUser) -> tuple[str, str]:
    seller = await register_user(client, email="owner@example.com", username="owner")
    other = await register_user(client, email="other@example.com", username="other")
    return seller["tokens"]["access_token"], other["tokens"]["access_token"]


async def status_for(client: AsyncClient, listing_id: str, token: str | None) -> int:
    headers = auth(token) if token else {}
    return (await client.get(f"/api/v1/listings/{listing_id}", headers=headers)).status_code


@pytest.mark.asyncio
async def test_drafts_and_private_listings_are_for_the_seller_only(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    seller, other = await tokens(client, register_user)
    book = await create_book(client, seller, title="Hidden Book")
    media = await upload_media(client, seller, filename="hidden.jpg")
    draft = await client.post(
        "/api/v1/listings",
        headers=auth(seller),
        json=listing_payload(book_id=book["id"], image_id=media["id"]),
    )
    second_media = await upload_media(client, seller, filename="hidden-2.jpg")
    private_payload = listing_payload(book_id=book["id"], image_id=second_media["id"])
    private_payload["visibility"] = "private"
    private = await client.post("/api/v1/listings", headers=auth(seller), json=private_payload)
    published_private = await client.post(
        f"/api/v1/listings/{private.json()['id']}/publish", headers=auth(seller)
    )
    assert published_private.status_code == 200, published_private.text

    for listing_id in (draft.json()["id"], private.json()["id"]):
        assert await status_for(client, listing_id, seller) == 200
        assert await status_for(client, listing_id, other) == 404
        assert await status_for(client, listing_id, None) == 404


@pytest.mark.asyncio
async def test_public_listings_stay_open_to_everyone(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    seller, other = await tokens(client, register_user)
    listing = await create_published_listing(client, seller, title="Open Book")

    assert await status_for(client, listing["id"], None) == 200
    assert await status_for(client, listing["id"], other) == 200

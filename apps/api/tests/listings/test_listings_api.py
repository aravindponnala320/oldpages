from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient

from conftest import RegisterUser

PRICE_MODES = {"sell", "sell_exchange", "rent", "bulk_sale"}
ALL_MODES = [
    "sell",
    "exchange",
    "sell_exchange",
    "donate",
    "lend",
    "rent",
    "request",
    "giveaway",
    "bulk_sale",
]


@pytest.mark.asyncio
async def test_create_from_isbn_publish_hides_exact_location_and_media_is_not_public(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    token = registered["tokens"]["access_token"]
    book = await create_book(client, token, title="Godaan Listing", isbn_13="9780143039433")
    media = await upload_media(client, token)

    create_response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(isbn="978-0-1430-3943-3", image_id=media["id"]),
    )

    assert create_response.status_code == 201, create_response.text
    listing = create_response.json()
    assert listing["book"]["id"] == book["id"]
    assert listing["status"] == "draft"
    assert listing["images"][0]["media"]["status"] == "uploaded"
    assert listing["images"][0]["public_url"] is None
    assert "exact_latitude" not in listing["location"]
    assert "pickup_notes_private" not in listing["location"]

    publish_response = await client.post(
        f"/api/v1/listings/{listing['id']}/publish",
        headers=auth(token),
    )
    assert publish_response.status_code == 200
    published = publish_response.json()
    assert published["status"] == "active"
    assert published["quality_score"] >= 70

    public_response = await client.get(f"/api/v1/listings/{listing['id']}")
    assert public_response.status_code == 200
    assert "exact_longitude" not in public_response.json()["location"]


@pytest.mark.asyncio
async def test_only_listing_owner_can_modify(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(client, email="owner@example.com", username="owner")
    other = await register_user(client, email="other@example.com", username="other")
    owner_token = owner["tokens"]["access_token"]
    other_token = other["tokens"]["access_token"]
    book = await create_book(client, owner_token, title="Owner Book")
    media = await upload_media(client, owner_token)
    listing = await create_listing(client, owner_token, book["id"], media["id"])

    patch_response = await client.patch(
        f"/api/v1/listings/{listing['id']}",
        headers=auth(other_token),
        json={"description": "Not mine"},
    )
    publish_response = await client.post(
        f"/api/v1/listings/{listing['id']}/publish",
        headers=auth(other_token),
    )
    delete_response = await client.delete(
        f"/api/v1/listings/{listing['id']}",
        headers=auth(other_token),
    )

    assert patch_response.status_code == 403
    assert publish_response.status_code == 403
    assert delete_response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_state_transitions_fail(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    token = registered["tokens"]["access_token"]
    book = await create_book(client, token, title="Transitions")
    media = await upload_media(client, token)
    listing = await create_listing(client, token, book["id"], media["id"])

    pause_draft = await client.post(f"/api/v1/listings/{listing['id']}/pause", headers=auth(token))
    assert pause_draft.status_code == 409

    published = await client.post(f"/api/v1/listings/{listing['id']}/publish", headers=auth(token))
    assert published.status_code == 200

    publish_again = await client.post(
        f"/api/v1/listings/{listing['id']}/publish",
        headers=auth(token),
    )
    assert publish_again.status_code == 409

    paused = await client.post(f"/api/v1/listings/{listing['id']}/pause", headers=auth(token))
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    relisted = await client.post(f"/api/v1/listings/{listing['id']}/relist", headers=auth(token))
    assert relisted.status_code == 200
    assert relisted.json()["status"] == "active"


@pytest.mark.asyncio
async def test_price_history_is_preserved(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    token = registered["tokens"]["access_token"]
    book = await create_book(client, token, title="Price History")
    media = await upload_media(client, token)
    listing = await create_listing(client, token, book["id"], media["id"])

    update_response = await client.patch(
        f"/api/v1/listings/{listing['id']}",
        headers=auth(token),
        json={"price_amount_cents": 35000},
    )

    assert update_response.status_code == 200
    history = update_response.json()["price_history"]
    assert len(history) == 2
    assert history[0]["old_amount_cents"] is None
    assert history[0]["new_amount_cents"] == 45000
    assert history[1]["old_amount_cents"] == 45000
    assert history[1]["new_amount_cents"] == 35000


@pytest.mark.asyncio
async def test_delete_soft_deletes_and_public_get_returns_not_found(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    token = registered["tokens"]["access_token"]
    book = await create_book(client, token, title="Delete Listing")
    media = await upload_media(client, token)
    listing = await create_listing(client, token, book["id"], media["id"])

    delete_response = await client.delete(f"/api/v1/listings/{listing['id']}", headers=auth(token))
    public_response = await client.get(f"/api/v1/listings/{listing['id']}")

    assert delete_response.status_code == 204
    assert public_response.status_code == 404


@pytest.mark.parametrize("mode", ALL_MODES)
@pytest.mark.asyncio
async def test_create_draft_listing_for_every_listing_type(
    mode: str,
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(
        client,
        email=f"{mode}@example.com",
        username=f"{mode}_user",
    )
    token = registered["tokens"]["access_token"]
    book = await create_book(client, token, title=f"Mode {mode}")
    media = await upload_media(client, token, filename=f"{mode}.jpg")

    create_response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(
            book_id=book["id"],
            image_id=media["id"],
            listing_modes=[mode],
            price_amount_cents=25000 if mode in PRICE_MODES else None,
        ),
    )

    assert create_response.status_code == 201, create_response.text
    assert create_response.json()["listing_modes"] == [mode]


async def create_book(
    client: AsyncClient,
    token: str,
    *,
    isbn_13: str | None = None,
    title: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "authors": [{"name": "Listing Author"}],
        "description": "A catalog entry for listing tests.",
        "format": "paperback",
        "language": "en",
        "page_count": 250,
        "publisher": {"name": "Listing Publisher"},
        "title": title,
    }
    if isbn_13 is not None:
        payload["isbn_13"] = isbn_13
    response = await client.post("/api/v1/books", headers=auth(token), json=payload)
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def upload_media(
    client: AsyncClient,
    token: str,
    *,
    filename: str = "listing.jpg",
) -> dict[str, Any]:
    upload_url_response = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": filename},
    )
    assert upload_url_response.status_code == 200, upload_url_response.text
    media_id = upload_url_response.json()["id"]

    complete_response = await client.post(
        f"/api/v1/media/{media_id}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete_response.status_code == 200, complete_response.text
    assert complete_response.json()["public_url"] is None
    return cast("dict[str, Any]", complete_response.json())


async def create_listing(
    client: AsyncClient,
    token: str,
    book_id: str,
    media_id: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(book_id=book_id, image_id=media_id),
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def listing_payload(
    *,
    book_id: str | None = None,
    image_id: str,
    isbn: str | None = None,
    listing_modes: list[str] | None = None,
    price_amount_cents: int | None = 45000,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "condition": {
            "condition": "good",
            "damage_details": "Light shelf wear.",
            "highlighting_percent": 5,
        },
        "delivery_methods": [{"method": "pickup", "notes": "Public pickup only"}],
        "description": "A clean used copy with readable pages and no missing chapters.",
        "images": [{"alt_text": "Actual book cover", "media_id": image_id}],
        "listing_modes": listing_modes or ["sell"],
        "location": {
            "campus_pickup": True,
            "city": "Pune",
            "country": "IN",
            "exact_latitude": "18.520430",
            "exact_longitude": "73.856744",
            "neighborhood": "Deccan",
            "pickup_notes_private": "Meet at the library gate.",
            "public_area": "Deccan, Pune",
            "state": "Maharashtra",
        },
        "negotiable": True,
        "price_amount_cents": price_amount_cents,
        "quantity": 1,
    }
    if book_id is not None:
        payload["book_id"] = book_id
    if isbn is not None:
        payload["isbn"] = isbn
    return payload


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

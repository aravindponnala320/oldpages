from __future__ import annotations

from typing import Any, cast

from httpx import AsyncClient


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_book(
    client: AsyncClient,
    token: str,
    *,
    title: str,
    isbn_13: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "authors": [{"name": "API Test Author"}],
        "description": "A catalog entry for API integration tests.",
        "format": "paperback",
        "language": "en",
        "page_count": 240,
        "publisher": {"name": "API Test Publisher"},
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
    filename: str = "api-test.jpg",
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
    return cast("dict[str, Any]", complete_response.json())


async def create_published_listing(
    client: AsyncClient,
    token: str,
    *,
    title: str,
    price_amount_cents: int = 45_000,
) -> dict[str, Any]:
    book = await create_book(client, token, title=title)
    media = await upload_media(client, token, filename=f"{title.lower().replace(' ', '-')}.jpg")
    create_response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(
            book_id=book["id"],
            image_id=media["id"],
            price_amount_cents=price_amount_cents,
        ),
    )
    assert create_response.status_code == 201, create_response.text
    publish_response = await client.post(
        f"/api/v1/listings/{create_response.json()['id']}/publish",
        headers=auth(token),
    )
    assert publish_response.status_code == 200, publish_response.text
    return cast("dict[str, Any]", publish_response.json())


def listing_payload(
    *,
    book_id: str,
    image_id: str,
    price_amount_cents: int = 45_000,
) -> dict[str, Any]:
    return {
        "book_id": book_id,
        "condition": {
            "condition": "good",
            "damage_details": "Light shelf wear.",
            "highlighting_percent": 5,
        },
        "delivery_methods": [
            {"method": "pickup", "notes": "Public pickup only"},
            {"method": "shipping", "notes": "Ships after payment confirmation"},
        ],
        "description": "A clean used copy with readable pages and no missing chapters.",
        "images": [{"alt_text": "Actual book cover", "media_id": image_id}],
        "listing_modes": ["sell"],
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

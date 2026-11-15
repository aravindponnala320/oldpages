from __future__ import annotations

from typing import Any, cast

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.identity.models import User, UserPreference


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
    country: str = "IN",
) -> dict[str, Any]:
    book = await create_book(client, token, title=title)
    media = await upload_media(client, token, filename=f"{title.lower().replace(' ', '-')}.jpg")
    payload = listing_payload(
        book_id=book["id"],
        image_id=media["id"],
        price_amount_cents=price_amount_cents,
    )
    payload["location"]["country"] = country
    create_response = await client.post("/api/v1/listings", headers=auth(token), json=payload)
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


def address(name: str) -> dict[str, str]:
    return {
        "address_line1": "Library Road 1",
        "city": "Pune",
        "country": "IN",
        "name": name,
        "phone": "+911234567890",
        "pincode": "411001",
        "state": "Maharashtra",
    }


async def create_shipping_order(
    client: AsyncClient,
    register_user: RegisterUser,
    *,
    suffix: str,
    price_amount_cents: int = 12_000,
) -> dict[str, Any]:
    seller = await register_user(
        client,
        email=f"seller-payments-{suffix}@example.com",
        username=f"seller-payments-{suffix}",
    )
    buyer = await register_user(
        client,
        email=f"buyer-payments-{suffix}@example.com",
        username=f"buyer-payments-{suffix}",
    )
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    listing = await create_published_listing(
        client,
        seller_token,
        title=f"Payments Book {suffix}",
        price_amount_cents=price_amount_cents,
    )

    cart_response = await client.post(
        "/api/v1/carts",
        headers=auth(buyer_token),
        json={"seller_id": seller["user"]["id"]},
    )
    assert cart_response.status_code == 201, cart_response.text
    cart_id = cart_response.json()["id"]

    add_item_response = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=auth(buyer_token),
        json={"listing_id": listing["id"], "quantity": 1},
    )
    assert add_item_response.status_code == 200, add_item_response.text

    checkout_response = await client.post(
        f"/api/v1/carts/{cart_id}/checkout",
        headers=auth(buyer_token),
        json={"fulfillment_method": "shipping", "idempotency_key": f"checkout-{suffix}"},
    )
    assert checkout_response.status_code == 200, checkout_response.text
    order = checkout_response.json()

    payment_response = await client.post(
        f"/api/v1/payments/{order['id']}/initiate",
        headers=auth(buyer_token),
        json={"idempotency_key": f"pay-{suffix}", "provider": "local"},
    )
    assert payment_response.status_code == 201, payment_response.text

    return {
        "buyer": buyer,
        "buyer_token": buyer_token,
        "cart_id": cart_id,
        "listing": listing,
        "order": order,
        "payment": payment_response.json()["payment"],
        "provider_data": payment_response.json()["provider_data"],
        "seller": seller,
        "seller_token": seller_token,
    }


async def capture_order_payment(
    client: AsyncClient,
    order_id: str,
    provider_payment_id: str,
    *,
    event_id: str,
) -> None:
    capture = await client.post(
        "/api/v1/payments/webhook/local",
        json={
            "event_id": event_id,
            "provider_payment_id": provider_payment_id,
            "status": "captured",
            "type": "payment.captured",
        },
    )
    assert capture.status_code == 200, capture.text
    assert capture.json() == {"status": "processed"}


async def grant_role(
    session_factory: async_sessionmaker[AsyncSession], public_id: str, role: str
) -> None:
    async with session_factory() as session:
        user_id = await session.scalar(select(User.id).where(User.public_id == public_id))
        preference = await session.scalar(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        assert preference is not None
        preference.metadata_json = {**preference.metadata_json, "roles": [role]}
        await session.commit()

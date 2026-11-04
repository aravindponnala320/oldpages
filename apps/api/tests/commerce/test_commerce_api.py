from __future__ import annotations

from datetime import timedelta
from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.commerce.models import Offer
from oldpages_api.identity.security import utc_now


@pytest.mark.asyncio
async def test_accepted_offer_reserves_last_copy_atomically(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller-commerce@example.com", username="seller-c")
    buyer_one = await register_user(client, email="buyer-one@example.com", username="buyer-one")
    buyer_two = await register_user(client, email="buyer-two@example.com", username="buyer-two")
    seller_token = seller["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Reserved Book")

    first_offer = await create_offer(
        client,
        buyer_one["tokens"]["access_token"],
        listing["id"],
        amount_cents=40000,
    )
    second_offer = await create_offer(
        client,
        buyer_two["tokens"]["access_token"],
        listing["id"],
        amount_cents=41000,
    )

    accept_first = await client.post(
        f"/api/v1/offers/{first_offer['id']}/accept",
        headers=auth(seller_token),
        json={},
    )
    accept_second = await client.post(
        f"/api/v1/offers/{second_offer['id']}/accept",
        headers=auth(seller_token),
        json={},
    )
    listing_after = await client.get(f"/api/v1/listings/{listing['id']}")

    assert accept_first.status_code == 200, accept_first.text
    assert accept_first.json()["transaction_id"] is not None
    assert accept_second.status_code == 409
    assert listing_after.json()["status"] == "reserved"
    assert listing_after.json()["inventory"]["quantity_available"] == 0


@pytest.mark.asyncio
async def test_expired_offers_cannot_be_accepted(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller = await register_user(client, email="seller-expired@example.com", username="seller-exp")
    buyer = await register_user(client, email="buyer-expired@example.com", username="buyer-exp")
    listing = await create_published_listing(
        client,
        seller["tokens"]["access_token"],
        title="Expired Offer Book",
    )
    offer = await create_offer(
        client,
        buyer["tokens"]["access_token"],
        listing["id"],
        amount_cents=35000,
    )
    async with session_factory() as session:
        result = await session.execute(select(Offer).where(Offer.public_id == offer["id"]))
        offer_model = result.scalar_one()
        offer_model.expires_at = utc_now() - timedelta(minutes=1)
        await session.commit()

    response = await client.post(
        f"/api/v1/offers/{offer['id']}/accept",
        headers=auth(seller["tokens"]["access_token"]),
        json={},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_pickup_completion_and_transaction_linked_reviews(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller-review@example.com", username="seller-r")
    buyer = await register_user(client, email="buyer-review@example.com", username="buyer-r")
    stranger = await register_user(client, email="stranger-review@example.com", username="str-r")
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Reviewable Book")
    offer = await create_offer(client, buyer_token, listing["id"], amount_cents=30000)
    accepted = await client.post(
        f"/api/v1/offers/{offer['id']}/accept",
        headers=auth(seller_token),
        json={},
    )
    transaction_id = accepted.json()["transaction_id"]

    early_review = await client.post(
        "/api/v1/reviews",
        headers=auth(buyer_token),
        json={"rating": 5, "transaction_id": transaction_id},
    )
    pickup = await client.post(
        "/api/v1/pickups",
        headers=auth(buyer_token),
        json={
            "public_location_label": "Library gate",
            "transaction_id": transaction_id,
        },
    )
    stranger_pickup = await client.post(
        "/api/v1/pickups",
        headers=auth(stranger["tokens"]["access_token"]),
        json={
            "public_location_label": "Library gate",
            "transaction_id": transaction_id,
        },
    )
    confirm = await client.post(
        f"/api/v1/pickups/{pickup.json()['id']}/confirm",
        headers=auth(seller_token),
        json={},
    )
    complete = await client.post(
        f"/api/v1/transactions/{transaction_id}/complete",
        headers=auth(buyer_token),
        json={"handover_code": pickup.json()["handover_code"]},
    )
    first_review = await client.post(
        "/api/v1/reviews",
        headers=auth(buyer_token),
        json={
            "comment": "Accurate description and easy pickup.",
            "dimensions": [{"dimension": "pickup punctuality", "rating": 5}],
            "rating": 5,
            "transaction_id": transaction_id,
        },
    )
    duplicate_review = await client.post(
        "/api/v1/reviews",
        headers=auth(buyer_token),
        json={"rating": 4, "transaction_id": transaction_id},
    )
    seller_review = await client.post(
        "/api/v1/reviews",
        headers=auth(seller_token),
        json={"rating": 5, "transaction_id": transaction_id},
    )

    assert accepted.status_code == 200, accepted.text
    assert early_review.status_code == 409
    assert pickup.status_code == 201, pickup.text
    assert pickup.json()["exact_latitude"] == "18.520430"
    assert pickup.json()["pickup_notes_private"] == "Meet at the library gate."
    assert stranger_pickup.status_code == 403
    assert confirm.status_code == 200, confirm.text
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "completed"
    assert first_review.status_code == 201, first_review.text
    assert first_review.json()["review_type"] == "buyer_reviews_seller"
    assert duplicate_review.status_code == 409
    assert seller_review.status_code == 201, seller_review.text
    assert seller_review.json()["review_type"] == "seller_reviews_buyer"


@pytest.mark.asyncio
async def test_counter_reject_and_withdraw_offer_flow(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller-counter@example.com", username="seller-ctr")
    buyer = await register_user(client, email="buyer-counter@example.com", username="buyer-ctr")
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Counter Book")
    offer = await create_offer(client, buyer_token, listing["id"], amount_cents=20000)

    counter = await client.post(
        f"/api/v1/offers/{offer['id']}/counter",
        headers=auth(seller_token),
        json={"amount_cents": 24000, "message": "I can do 240."},
    )
    reject = await client.post(
        f"/api/v1/offers/{counter.json()['id']}/reject",
        headers=auth(buyer_token),
        json={},
    )
    withdrawn_offer = await create_offer(client, buyer_token, listing["id"], amount_cents=22000)
    withdraw = await client.post(
        f"/api/v1/offers/{withdrawn_offer['id']}/withdraw",
        headers=auth(buyer_token),
        json={},
    )

    assert counter.status_code == 200, counter.text
    assert counter.json()["offer_type"] == "counter"
    assert counter.json()["parent_offer_id"] == offer["id"]
    assert reject.status_code == 200, reject.text
    assert reject.json()["status"] == "rejected"
    assert withdraw.status_code == 200, withdraw.text
    assert withdraw.json()["status"] == "withdrawn"


async def create_offer(
    client: AsyncClient,
    token: str,
    listing_id: str,
    *,
    amount_cents: int,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/offers",
        headers=auth(token),
        json={
            "amount_cents": amount_cents,
            "fulfillment_method": "pickup",
            "listing_id": listing_id,
            "quantity": 1,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def create_published_listing(
    client: AsyncClient,
    token: str,
    *,
    title: str,
    quantity: int = 1,
) -> dict[str, Any]:
    book = await create_book(client, token, title=title)
    media = await upload_media(client, token)
    create_response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(book_id=book["id"], image_id=media["id"], quantity=quantity),
    )
    assert create_response.status_code == 201, create_response.text
    publish_response = await client.post(
        f"/api/v1/listings/{create_response.json()['id']}/publish",
        headers=auth(token),
    )
    assert publish_response.status_code == 200, publish_response.text
    return cast("dict[str, Any]", publish_response.json())


async def create_book(client: AsyncClient, token: str, *, title: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/books",
        headers=auth(token),
        json={
            "authors": [{"name": "Commerce Author"}],
            "description": "A catalog entry for commerce tests.",
            "format": "paperback",
            "language": "en",
            "page_count": 250,
            "publisher": {"name": "Commerce Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def upload_media(client: AsyncClient, token: str) -> dict[str, Any]:
    upload_response = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": "commerce.jpg"},
    )
    assert upload_response.status_code == 200, upload_response.text
    complete_response = await client.post(
        f"/api/v1/media/{upload_response.json()['id']}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete_response.status_code == 200, complete_response.text
    return cast("dict[str, Any]", complete_response.json())


def listing_payload(*, book_id: str, image_id: str, quantity: int) -> dict[str, Any]:
    return {
        "book_id": book_id,
        "condition": {
            "condition": "good",
            "damage_details": "Light shelf wear.",
            "highlighting_percent": 5,
        },
        "delivery_methods": [{"method": "pickup"}],
        "description": "A clean copy for a commerce flow test.",
        "images": [{"alt_text": "Actual cover", "media_id": image_id}],
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
        "price_amount_cents": 45000,
        "quantity": quantity,
    }


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

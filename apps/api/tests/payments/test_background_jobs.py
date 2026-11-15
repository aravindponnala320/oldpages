from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import (
    address,
    auth,
    capture_order_payment,
    create_published_listing,
    create_shipping_order,
)
from oldpages_api.identity.security import utc_now
from oldpages_api.payments.models import Payment
from oldpages_api.payments.service import PaymentsService
from oldpages_api.search.tasks import send_saved_search_alerts

LATER = timedelta(minutes=1)  # a cutoff just after now, so everything made so far is "old"


async def order_status(client: AsyncClient, order_id: str, token: str) -> str:
    response = await client.get(f"/api/v1/orders/{order_id}", headers=auth(token))
    assert response.status_code == 200, response.text
    return str(response.json()["status"])


async def listing_stock(client: AsyncClient, listing_id: str) -> tuple[str, int]:
    listing = (await client.get(f"/api/v1/listings/{listing_id}")).json()
    return listing["status"], listing["inventory"]["quantity_available"]


async def set_payment_status(
    session_factory: async_sessionmaker[AsyncSession], provider_payment_id: str, status: str
) -> None:
    async with session_factory() as session:
        payment = await session.scalar(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        assert payment is not None
        payment.status = status
        await session.commit()


async def deliver(client: AsyncClient, flow: dict[str, Any]) -> None:
    order_id = flow["order"]["id"]
    await capture_order_payment(
        client, order_id, flow["payment"]["provider_payment_id"], event_id=f"cap-{order_id}"
    )
    seller = auth(flow["seller_token"])
    assert (await client.post(f"/api/v1/orders/{order_id}/accept", headers=seller)).is_success
    shipment = await client.post(
        "/api/v1/shipments",
        headers=seller,
        json={
            "from_address": address("Seller"),
            "order_id": order_id,
            "provider": "local",
            "to_address": address("Buyer"),
            "weight_grams": 400,
        },
    )
    assert shipment.status_code == 201, shipment.text
    delivered = await client.post(
        "/api/v1/shipments/webhook/local",
        json={
            "event_id": f"delivered-{order_id}",
            "provider_shipment_id": shipment.json()["provider_shipment_id"],
            "status": "delivered",
            "type": "shipment.delivered",
        },
    )
    assert delivered.status_code == 200, delivered.text


@pytest.mark.asyncio
async def test_unpaid_checkouts_expire_and_put_the_book_back(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="unpaid")
    order_id, listing_id = flow["order"]["id"], flow["listing"]["id"]
    await set_payment_status(session_factory, flow["payment"]["provider_payment_id"], "failed")
    assert await listing_stock(client, listing_id) == ("reserved", 0)

    async with session_factory() as session:
        too_early = await PaymentsService(session).expire_unpaid_orders(utc_now() - LATER)
    async with session_factory() as session:
        expired = await PaymentsService(session).expire_unpaid_orders(utc_now() + LATER)

    assert (too_early, expired) == (0, 1)
    assert await order_status(client, order_id, flow["buyer_token"]) == "cancelled"
    assert await listing_stock(client, listing_id) == ("active", 1)


@pytest.mark.asyncio
async def test_an_authorized_payment_keeps_its_order(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="authorized")
    # The local provider authorizes on initiation, as a card hold would.
    assert flow["payment"]["status"] == "authorized"
    async with session_factory() as session:
        assert await PaymentsService(session).expire_unpaid_orders(utc_now() + LATER) == 0
    assert await order_status(client, flow["order"]["id"], flow["buyer_token"]) == (
        "awaiting_payment"
    )


@pytest.mark.asyncio
async def test_delivered_orders_complete_after_buyer_protection_unless_disputed(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    quiet = await create_shipping_order(client, register_user, suffix="protect-quiet")
    disputed = await create_shipping_order(client, register_user, suffix="protect-dispute")
    await deliver(client, quiet)
    await deliver(client, disputed)
    dispute = await client.post(
        "/api/v1/disputes",
        headers=auth(disputed["buyer_token"]),
        json={
            "description": "The cover is torn.",
            "order_id": disputed["order"]["id"],
            "reason": "item_not_as_described",
        },
    )
    assert dispute.status_code == 201, dispute.text

    async with session_factory() as session:
        assert await PaymentsService(session).complete_protected_orders(utc_now() - LATER) == 0
    async with session_factory() as session:
        assert await PaymentsService(session).complete_protected_orders(utc_now() + LATER) == 1

    assert await order_status(client, quiet["order"]["id"], quiet["buyer_token"]) == "completed"
    assert await listing_stock(client, quiet["listing"]["id"]) == ("completed", 0)
    assert await order_status(client, disputed["order"]["id"], disputed["buyer_token"]) == (
        "disputed"
    )


@pytest.mark.asyncio
async def test_an_accepted_offer_that_goes_nowhere_releases_its_copy(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller = await register_user(client, email="seller-hold@example.com", username="seller-hold")
    buyer = await register_user(client, email="buyer-hold@example.com", username="buyer-hold")
    seller_token = seller["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Held Copy")
    offer = await client.post(
        "/api/v1/offers",
        headers=auth(buyer["tokens"]["access_token"]),
        json={
            "amount_cents": 40_000,
            "fulfillment_method": "pickup",
            "listing_id": listing["id"],
            "quantity": 1,
        },
    )
    assert offer.status_code == 201, offer.text
    accepted = await client.post(
        f"/api/v1/offers/{offer.json()['id']}/accept", headers=auth(seller_token), json={}
    )
    assert accepted.status_code == 200, accepted.text
    assert await listing_stock(client, listing["id"]) == ("reserved", 0)

    async with session_factory() as session:
        assert await PaymentsService(session).expire_offer_holds(utc_now() - LATER) == 0
    async with session_factory() as session:
        assert await PaymentsService(session).expire_offer_holds(utc_now() + LATER) == 1

    assert await listing_stock(client, listing["id"]) == ("active", 1)
    transaction = await client.get(
        f"/api/v1/transactions/{accepted.json()['transaction_id']}", headers=auth(seller_token)
    )
    assert transaction.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_saved_searches_hear_about_new_books_once(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller = await register_user(client, email="seller-alert@example.com", username="seller-alert")
    reader = await register_user(client, email="reader-alert@example.com", username="reader-alert")
    reader_token = reader["tokens"]["access_token"]
    saved = await client.post(
        "/api/v1/saved-searches",
        headers=auth(reader_token),
        json={"name": "Lighthouses", "query": "Lighthouse Keeper"},
    )
    assert saved.status_code == 201, saved.text
    await create_published_listing(
        client, seller["tokens"]["access_token"], title="The Lighthouse Keeper"
    )

    first = await send_saved_search_alerts(session_factory)
    second = await send_saved_search_alerts(session_factory)

    assert (first, second) == (1, 0)
    notifications = await client.get("/api/v1/notifications", headers=auth(reader_token))
    items = notifications.json()["items"]
    assert [n["type"] for n in items] == ["saved_search_match"]
    assert items[0]["body"] == "1 book matches your saved search."

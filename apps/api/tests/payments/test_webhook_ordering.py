from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import address, auth, capture_order_payment, create_shipping_order
from oldpages_api.payments.models import Payment


async def send_payment_event(
    client: AsyncClient, provider_payment_id: str, event_id: str, status: str
) -> None:
    response = await client.post(
        "/api/v1/payments/webhook/local",
        json={
            "event_id": event_id,
            "provider_payment_id": provider_payment_id,
            "status": status,
            "type": f"payment.{status}",
        },
    )
    assert response.status_code == 200, response.text  # accepted, so providers stop retrying


async def order_status(client: AsyncClient, order_id: str, token: str) -> str:
    response = await client.get(f"/api/v1/orders/{order_id}", headers=auth(token))
    assert response.status_code == 200, response.text
    return str(response.json()["status"])


async def payment_status(
    session_factory: async_sessionmaker[AsyncSession], provider_payment_id: str
) -> str:
    async with session_factory() as session:
        status = await session.scalar(
            select(Payment.status).where(Payment.provider_payment_id == provider_payment_id)
        )
    return str(status)


@pytest.mark.asyncio
async def test_late_payment_events_cannot_undo_a_capture_or_refund(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="late-events")
    order_id, token = flow["order"]["id"], flow["buyer_token"]
    payment_id = flow["payment"]["provider_payment_id"]
    await capture_order_payment(client, order_id, payment_id, event_id="evt-capture")

    await send_payment_event(client, payment_id, "evt-late-auth", "authorized")
    await send_payment_event(client, payment_id, "evt-late-fail", "failed")
    assert await order_status(client, order_id, token) == "paid"
    assert await payment_status(session_factory, payment_id) == "captured"

    await send_payment_event(client, payment_id, "evt-refund", "refunded")
    await send_payment_event(client, payment_id, "evt-replayed-capture", "captured")
    assert await order_status(client, order_id, token) == "refunded"
    assert await payment_status(session_factory, payment_id) == "refunded"


@pytest.mark.asyncio
async def test_shipment_events_only_move_forward(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="ship-order")
    order_id = flow["order"]["id"]
    seller, buyer = flow["seller_token"], flow["buyer_token"]
    await capture_order_payment(
        client, order_id, flow["payment"]["provider_payment_id"], event_id="evt-cap"
    )
    assert (
        await client.post(f"/api/v1/orders/{order_id}/accept", headers=auth(seller))
    ).status_code == 200
    created = await client.post(
        "/api/v1/shipments",
        headers=auth(seller),
        json={
            "from_address": address("Seller"),
            "order_id": order_id,
            "provider": "local",
            "to_address": address("Buyer"),
            "weight_grams": 550,
        },
    )
    assert created.status_code == 201, created.text
    shipment_id = created.json()["provider_shipment_id"]
    shipment_url = f"/api/v1/shipments/{created.json()['id']}"

    async def ship(event_id: str, status: str) -> int:
        response = await client.post(
            "/api/v1/shipments/webhook/local",
            json={
                "event_id": event_id,
                "provider_shipment_id": shipment_id,
                "status": status,
                "type": f"shipment.{status}",
            },
        )
        return response.status_code

    assert await ship("evt-delivered", "delivered") == 200
    assert await ship("evt-late-transit", "in_transit") == 200
    assert await ship("evt-made-up", "teleported") == 200  # unknown status: ignored, not a 500

    assert await order_status(client, order_id, buyer) == "delivered"
    shipment = await client.get(shipment_url, headers=auth(seller))
    assert shipment.json()["status"] == "delivered"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value"), [("amount_cents", 100), ("currency", "USD")], ids=["amount", "currency"]
)
async def test_a_capture_that_does_not_match_the_order_does_not_pay_it(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
    field: str,
    value: object,
) -> None:
    flow = await create_shipping_order(client, register_user, suffix=f"mismatch-{field}")
    payment_id = flow["payment"]["provider_payment_id"]
    response = await client.post(
        "/api/v1/payments/webhook/local",
        json={
            "event_id": f"evt-short-{field}",
            "provider_payment_id": payment_id,
            "status": "captured",
            "type": "payment.captured",
            "amount_cents": flow["order"]["total_cents"],
            "currency": flow["order"]["currency"],
            field: value,
        },
    )
    assert response.status_code == 200, response.text
    assert await order_status(client, flow["order"]["id"], flow["buyer_token"]) == (
        "awaiting_payment"
    )
    assert await payment_status(session_factory, payment_id) == "captured"


@pytest.mark.asyncio
async def test_a_partial_refund_leaves_the_order_paid(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="partial-refund")
    order_id, token = flow["order"]["id"], flow["buyer_token"]
    payment_id = flow["payment"]["provider_payment_id"]
    total = flow["order"]["total_cents"]
    await capture_order_payment(client, order_id, payment_id, event_id="evt-cap-partial")

    async def refund(event_id: str, amount: int) -> None:
        response = await client.post(
            "/api/v1/payments/webhook/local",
            json={
                "amount_cents": amount,
                "event_id": event_id,
                "provider_payment_id": payment_id,
                "status": "refunded",
                "type": "payment.refunded",
            },
        )
        assert response.status_code == 200, response.text

    await refund("evt-refund-part", 1_000)
    assert await order_status(client, order_id, token) == "paid"
    assert await payment_status(session_factory, payment_id) == "captured"

    await refund("evt-refund-rest", total - 1_000)
    assert await order_status(client, order_id, token) == "refunded"
    assert await payment_status(session_factory, payment_id) == "refunded"

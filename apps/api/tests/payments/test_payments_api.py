from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from helpers import (
    address,
    auth,
    capture_order_payment,
    create_published_listing,
    create_shipping_order,
)


@pytest.mark.asyncio
async def test_cart_and_order_use_listing_currency_and_never_mix(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller-fx@example.com", username="seller-fx")
    buyer = await register_user(client, email="buyer-fx@example.com", username="buyer-fx")
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    usd_listing = await create_published_listing(
        client, seller_token, title="Boston Book", price_amount_cents=1_500, country="US"
    )
    inr_listing = await create_published_listing(client, seller_token, title="Pune Book")
    cart = await client.post(
        "/api/v1/carts", headers=auth(buyer_token), json={"seller_id": seller["user"]["id"]}
    )
    cart_id = cart.json()["id"]

    added = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=auth(buyer_token),
        json={"listing_id": usd_listing["id"], "quantity": 1},
    )
    mixed = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=auth(buyer_token),
        json={"listing_id": inr_listing["id"], "quantity": 1},
    )
    order = await client.post(
        f"/api/v1/carts/{cart_id}/checkout",
        headers=auth(buyer_token),
        json={"fulfillment_method": "shipping", "idempotency_key": "checkout-fx"},
    )

    assert added.status_code == 200, added.text
    assert added.json()["currency"] == "USD"
    assert mixed.status_code == 422, mixed.text
    assert order.status_code == 200, order.text
    assert order.json()["currency"] == "USD"


@pytest.mark.asyncio
async def test_checkout_payment_and_webhook_idempotency(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="capture")
    order = flow["order"]
    seller_token = flow["seller_token"]
    buyer_token = flow["buyer_token"]
    assert order["status"] == "awaiting_payment"
    assert order["subtotal_cents"] == 12_000
    assert order["platform_fee_cents"] == 300
    assert order["total_cents"] == 12_300

    second_payment = await client.post(
        f"/api/v1/payments/{order['id']}/initiate",
        headers=auth(buyer_token),
        json={"idempotency_key": "pay-capture", "provider": "local"},
    )
    assert second_payment.status_code == 201, second_payment.text
    assert flow["payment"]["id"] == second_payment.json()["payment"]["id"]
    assert flow["payment"]["status"] == "authorized"

    unpaid_accept = await client.post(
        f"/api/v1/orders/{order['id']}/accept",
        headers=auth(seller_token),
    )
    assert unpaid_accept.status_code == 409

    first_webhook = await client.post(
        "/api/v1/payments/webhook/local",
        json={
            "event_id": "evt-payment-1",
            "provider_payment_id": flow["payment"]["provider_payment_id"],
            "status": "captured",
            "type": "payment.captured",
        },
    )
    duplicate_webhook = await client.post(
        "/api/v1/payments/webhook/local",
        json={
            "event_id": "evt-payment-1",
            "provider_payment_id": flow["payment"]["provider_payment_id"],
            "status": "captured",
            "type": "payment.captured",
        },
    )
    assert first_webhook.status_code == 200, first_webhook.text
    assert first_webhook.json() == {"status": "processed"}
    assert duplicate_webhook.status_code == 200, duplicate_webhook.text
    assert duplicate_webhook.json() == {"status": "already_processed"}

    paid_order = await client.get(f"/api/v1/orders/{order['id']}", headers=auth(buyer_token))
    assert paid_order.status_code == 200, paid_order.text
    assert paid_order.json()["status"] == "paid"

    accepted = await client.post(
        f"/api/v1/orders/{order['id']}/accept",
        headers=auth(seller_token),
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_shipping_webhook_and_payout_cap(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="shipping")
    order = flow["order"]
    seller_token = flow["seller_token"]
    buyer_token = flow["buyer_token"]
    await capture_order_payment(
        client,
        order["id"],
        flow["payment"]["provider_payment_id"],
        event_id="evt-payment-shipping-capture",
    )

    accepted = await client.post(
        f"/api/v1/orders/{order['id']}/accept",
        headers=auth(seller_token),
    )
    assert accepted.status_code == 200, accepted.text

    shipment_response = await client.post(
        "/api/v1/shipments",
        headers=auth(seller_token),
        json={
            "from_address": address("Seller"),
            "order_id": order["id"],
            "provider": "local",
            "to_address": address("Buyer"),
            "weight_grams": 550,
        },
    )
    assert shipment_response.status_code == 201, shipment_response.text
    shipment = shipment_response.json()
    assert shipment["status"] == "label_generated"

    in_transit = await client.post(
        "/api/v1/shipments/webhook/local",
        json={
            "event_id": "evt-shipment-in-transit",
            "provider_shipment_id": shipment["provider_shipment_id"],
            "status": "in_transit",
            "tracking_number": "LOCALTRACK1",
            "type": "shipment.in_transit",
        },
    )
    assert in_transit.status_code == 200, in_transit.text

    shipped_order = await client.get(f"/api/v1/orders/{order['id']}", headers=auth(buyer_token))
    assert shipped_order.status_code == 200, shipped_order.text
    assert shipped_order.json()["status"] == "shipped"

    delivered = await client.post(
        "/api/v1/shipments/webhook/local",
        json={
            "event_id": "evt-shipment-delivered",
            "provider_shipment_id": shipment["provider_shipment_id"],
            "status": "delivered",
            "type": "shipment.delivered",
        },
    )
    assert delivered.status_code == 200, delivered.text

    payout = await client.post(
        f"/api/v1/payments/{order['id']}/payouts",
        headers=auth(seller_token),
    )
    assert payout.status_code == 200, payout.text
    assert payout.json()["amount_cents"] == 12_000
    assert payout.json()["status"] == "paid"

    second_payout = await client.post(
        f"/api/v1/payments/{order['id']}/payouts",
        headers=auth(seller_token),
    )
    assert second_payout.status_code == 422


@pytest.mark.asyncio
async def test_refunds_are_idempotent_against_remaining_captured_amount(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="refund")
    order = flow["order"]
    buyer_token = flow["buyer_token"]
    seller_token = flow["seller_token"]
    await capture_order_payment(
        client,
        order["id"],
        flow["payment"]["provider_payment_id"],
        event_id="evt-payment-refund-capture",
    )

    seller_refund = await client.post(
        f"/api/v1/payments/{order['id']}/refunds",
        headers=auth(seller_token),
        json={"amount_cents": 500, "reason": "Seller cancelled one item"},
    )
    assert seller_refund.status_code == 200, seller_refund.text
    assert seller_refund.json()["amount_cents"] == 500
    assert seller_refund.json()["status"] == "succeeded"

    over_refund = await client.post(
        f"/api/v1/payments/{order['id']}/refunds",
        headers=auth(buyer_token),
        json={"amount_cents": 12_000, "reason": "Too much"},
    )
    assert over_refund.status_code == 422

    remaining_refund = await client.post(
        f"/api/v1/payments/{order['id']}/refunds",
        headers=auth(buyer_token),
        json={"reason": "Full refund remaining balance"},
    )
    assert remaining_refund.status_code == 200, remaining_refund.text
    assert remaining_refund.json()["amount_cents"] == 11_800

    refunded_order = await client.get(f"/api/v1/orders/{order['id']}", headers=auth(buyer_token))
    assert refunded_order.status_code == 200, refunded_order.text
    assert refunded_order.json()["status"] == "refunded"

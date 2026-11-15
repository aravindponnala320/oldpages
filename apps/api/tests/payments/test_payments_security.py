from __future__ import annotations

from typing import Literal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import auth, capture_order_payment, create_shipping_order, grant_role
from oldpages_api.core.config import Settings


@pytest.mark.asyncio
@pytest.mark.parametrize("environment", ["staging", "production"])
async def test_unsigned_local_webhooks_are_refused_outside_development(
    client: AsyncClient,
    register_user: RegisterUser,
    monkeypatch: pytest.MonkeyPatch,
    environment: Literal["staging", "production"],
) -> None:
    flow = await create_shipping_order(client, register_user, suffix=f"fake-{environment}")
    import oldpages_api.payments.service as payments_service

    monkeypatch.setattr(
        payments_service, "get_settings", lambda: Settings.model_construct(environment=environment)
    )

    fake_capture = await client.post(
        "/api/v1/payments/webhook/local",
        json={
            "event_id": "evt-forged",
            "order_id": flow["order"]["id"],
            "status": "captured",
            "type": "payment.captured",
        },
    )
    fake_delivery = await client.post(
        "/api/v1/shipments/webhook/local",
        json={"event_id": "evt-forged-ship", "status": "delivered"},
    )
    order = await client.get(
        f"/api/v1/orders/{flow['order']['id']}", headers=auth(flow["buyer_token"])
    )

    assert fake_capture.status_code == 422, fake_capture.text
    assert fake_delivery.status_code == 422, fake_delivery.text
    assert order.json()["status"] == "awaiting_payment"


@pytest.mark.asyncio
async def test_only_moderators_can_resolve_disputes(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    flow = await create_shipping_order(client, register_user, suffix="dispute")
    await capture_order_payment(
        client,
        flow["order"]["id"],
        flow["payment"]["provider_payment_id"],
        event_id="evt-dispute-capture",
    )
    dispute = await client.post(
        "/api/v1/disputes",
        headers=auth(flow["buyer_token"]),
        json={
            "order_id": flow["order"]["id"],
            "reason": "item_not_received",
            "description": "Nothing arrived.",
        },
    )
    assert dispute.status_code == 201, dispute.text
    moderator = await register_user(client, email="mod@example.com", username="mod")
    await grant_role(session_factory, moderator["user"]["id"], "moderator")
    resolve_url = f"/api/v1/disputes/{dispute.json()['id']}/resolve"
    body = {"resolution": "resolved_seller"}

    by_seller = await client.post(resolve_url, headers=auth(flow["seller_token"]), json=body)
    by_buyer = await client.post(resolve_url, headers=auth(flow["buyer_token"]), json=body)
    by_moderator = await client.post(
        resolve_url, headers=auth(moderator["tokens"]["access_token"]), json=body
    )

    assert by_seller.status_code == 403, by_seller.text
    assert by_buyer.status_code == 403, by_buyer.text
    assert by_moderator.status_code == 200, by_moderator.text
    assert by_moderator.json()["status"] == "resolved_seller"

from __future__ import annotations

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import auth, create_published_listing
from oldpages_api.identity.models import User
from oldpages_api.identity.security import utc_now
from oldpages_api.subscriptions.models import Coupon, SubscriptionPlan


@pytest.mark.asyncio
async def test_subscription_lifecycle_and_coupon_validation(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        plan = SubscriptionPlan(
            billing_interval="monthly",
            community_limit=2,
            description="Seller Pro plan",
            features_json=["storefront", "analytics"],
            listing_limit=50,
            name="Seller Pro",
            price_cents=99900,
            saved_search_limit=25,
            slug="seller-pro",
            sort_order=1,
        )
        coupon = Coupon(
            code="SAVE10",
            discount_type="percent",
            discount_value=10,
            is_active=True,
            min_order_cents=10_000,
            valid_from=utc_now() - timedelta(days=1),
            valid_until=utc_now() + timedelta(days=1),
        )
        session.add_all([plan, coupon])
        await session.commit()
        plan_id = plan.public_id

    user = await register_user(
        client,
        email="subscription-user@example.com",
        username="subscription-user",
    )
    other = await register_user(
        client,
        email="subscription-other@example.com",
        username="subscription-other",
    )
    admin = await register_user(
        client,
        email="subscription-admin@example.com",
        username="subscription-admin",
    )
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.email == admin["user"]["email"]))
        admin_user = result.scalar_one()
        admin_user.is_superuser = True
        await session.commit()

    user_token = user["tokens"]["access_token"]
    other_token = other["tokens"]["access_token"]
    admin_token = admin["tokens"]["access_token"]

    plans_response = await client.get("/api/v1/subscription-plans")
    assert plans_response.status_code == 200, plans_response.text
    assert plans_response.json()[0]["slug"] == "seller-pro"

    free_entitlements = await client.get(
        "/api/v1/subscriptions/entitlements/me",
        headers=auth(user_token),
    )
    assert free_entitlements.status_code == 200, free_entitlements.text
    assert free_entitlements.json()["active"] is False
    assert free_entitlements.json()["limits"]["listing_limit"] == 10

    subscribe_response = await client.post(
        "/api/v1/subscriptions",
        headers=auth(user_token),
        json={"plan_id": plan_id},
    )
    assert subscribe_response.status_code == 201, subscribe_response.text
    subscription = subscribe_response.json()
    assert subscription["status"] == "active"
    assert subscription["plan"]["features_json"] == ["storefront", "analytics"]

    paid_entitlements = await client.get(
        "/api/v1/subscriptions/entitlements/me",
        headers=auth(user_token),
    )
    assert paid_entitlements.status_code == 200, paid_entitlements.text
    assert paid_entitlements.json()["active"] is True
    assert paid_entitlements.json()["features"] == ["storefront", "analytics"]
    assert paid_entitlements.json()["limits"]["listing_limit"] == 50

    duplicate_response = await client.post(
        "/api/v1/subscriptions",
        headers=auth(user_token),
        json={"plan_id": plan_id},
    )
    assert duplicate_response.status_code == 422

    forbidden_cancel = await client.delete(
        f"/api/v1/subscriptions/{subscription['id']}",
        headers=auth(other_token),
    )
    assert forbidden_cancel.status_code == 403

    cancel_response = await client.delete(
        f"/api/v1/subscriptions/{subscription['id']}",
        headers=auth(user_token),
    )
    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["status"] == "cancelled"

    cancelled_entitlements = await client.get(
        "/api/v1/subscriptions/entitlements/me",
        headers=auth(user_token),
    )
    assert cancelled_entitlements.status_code == 200, cancelled_entitlements.text
    assert cancelled_entitlements.json()["active"] is False

    listing = await create_published_listing(
        client,
        user_token,
        title="Promoted Seller Book",
        price_amount_cents=25_000,
    )
    promotion_response = await client.post(
        "/api/v1/promotions",
        headers=auth(user_token),
        json={
            "amount_cents": 15000,
            "currency": "INR",
            "ends_at": (utc_now() + timedelta(days=7)).isoformat(),
            "listing_id": listing["id"],
            "starts_at": utc_now().isoformat(),
            "type": "featured",
        },
    )
    assert promotion_response.status_code == 201, promotion_response.text
    promotion = promotion_response.json()
    assert promotion["is_paid"] is True
    assert promotion["promotion_order_id"] is not None

    forbidden_coupon = await client.post(
        "/api/v1/coupons",
        headers=auth(user_token),
        json={
            "code": "ADMIN5",
            "discount_type": "fixed",
            "discount_value": 500,
            "valid_from": utc_now().isoformat(),
        },
    )
    assert forbidden_coupon.status_code == 403

    created_coupon = await client.post(
        "/api/v1/coupons",
        headers=auth(admin_token),
        json={
            "code": "ADMIN5",
            "discount_type": "fixed",
            "discount_value": 500,
            "valid_from": utc_now().isoformat(),
        },
    )
    assert created_coupon.status_code == 201, created_coupon.text
    assert created_coupon.json()["code"] == "ADMIN5"

    coupons_response = await client.get("/api/v1/coupons", headers=auth(admin_token))
    assert coupons_response.status_code == 200, coupons_response.text
    assert {coupon["code"] for coupon in coupons_response.json()} >= {"ADMIN5", "SAVE10"}

    coupon_response = await client.post(
        "/api/v1/coupons/validate",
        json={"code": "save10", "order_amount_cents": 20_000},
    )
    assert coupon_response.status_code == 200, coupon_response.text
    assert coupon_response.json() == {
        "discount_cents": 2_000,
        "message": "Coupon is valid.",
        "valid": True,
    }

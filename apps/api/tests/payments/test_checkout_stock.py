from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from helpers import auth, create_book, create_published_listing, listing_payload, upload_media
from oldpages_api.identity.models import User
from oldpages_api.identity.schemas import AuthenticatedRequestContext
from oldpages_api.payments.models import Order
from oldpages_api.payments.service import PaymentsService


async def users(
    client: AsyncClient, register_user: RegisterUser, suffix: str, buyers: int = 1
) -> tuple[dict[str, Any], list[str]]:
    seller = await register_user(
        client, email=f"seller-{suffix}@example.com", username=f"seller-{suffix}"
    )
    tokens = []
    for n in range(buyers):
        buyer = await register_user(
            client, email=f"buyer{n}-{suffix}@example.com", username=f"buyer{n}-{suffix}"
        )
        tokens.append(buyer["tokens"]["access_token"])
    return seller, tokens


async def cart_with(
    client: AsyncClient, token: str, seller_id: str, listing_id: str, quantity: int = 1
) -> tuple[str, int, str]:
    cart = await client.post("/api/v1/carts", headers=auth(token), json={"seller_id": seller_id})
    assert cart.status_code == 201, cart.text
    cart_id = cart.json()["id"]
    added = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=auth(token),
        json={"listing_id": listing_id, "quantity": quantity},
    )
    return cart_id, added.status_code, added.text


async def checkout(client: AsyncClient, token: str, cart_id: str, key: str) -> Any:
    return await client.post(
        f"/api/v1/carts/{cart_id}/checkout",
        headers=auth(token),
        json={"fulfillment_method": "shipping", "idempotency_key": key},
    )


async def stock(client: AsyncClient, listing_id: str) -> tuple[str, int]:
    listing = (await client.get(f"/api/v1/listings/{listing_id}")).json()
    return listing["status"], listing["inventory"]["quantity_available"]


@pytest.mark.asyncio
async def test_the_last_copy_can_only_be_checked_out_once(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    seller, (first, second) = await users(client, register_user, "last-copy", buyers=2)
    seller_token = seller["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Last Copy")
    first_cart, *_ = await cart_with(client, first, seller["user"]["id"], listing["id"])
    second_cart, *_ = await cart_with(client, second, seller["user"]["id"], listing["id"])

    won = await checkout(client, first, first_cart, "first")
    lost = await checkout(client, second, second_cart, "second")

    assert won.status_code == 200, won.text
    assert won.json()["items"][0]["title_snapshot"] == "Last Copy"
    assert lost.status_code == 409, lost.text
    assert await stock(client, listing["id"]) == ("reserved", 0)
    # The losing cart is still usable once the book is back.
    cancelled = await client.post(
        f"/api/v1/orders/{won.json()['id']}/cancel",
        headers=auth(first),
        json={"reason": "Changed my mind"},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert await stock(client, listing["id"]) == ("active", 1)
    retried = await checkout(client, second, second_cart, "second-again")
    assert retried.status_code == 200, retried.text
    assert await stock(client, listing["id"]) == ("reserved", 0)


@pytest.mark.asyncio
async def test_a_cart_cannot_hold_more_copies_than_are_listed(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    seller, (buyer,) = await users(client, register_user, "too-many")
    listing = await create_published_listing(
        client, seller["tokens"]["access_token"], title="One Copy"
    )

    _, status, _ = await cart_with(client, buyer, seller["user"]["id"], listing["id"], quantity=2)
    assert status == 422
    cart_id, status, _ = await cart_with(client, buyer, seller["user"]["id"], listing["id"])
    assert status == 200
    again = await client.post(
        f"/api/v1/carts/{cart_id}/items",
        headers=auth(buyer),
        json={"listing_id": listing["id"], "quantity": 1},
    )
    assert again.status_code == 422, again.text  # 1 already in the cart + 1 more


@pytest.mark.asyncio
@pytest.mark.parametrize("modes", [["donate"], ["exchange"]])
async def test_books_that_are_not_for_sale_stay_out_of_the_cart(
    client: AsyncClient, register_user: RegisterUser, modes: list[str]
) -> None:
    seller, (buyer,) = await users(client, register_user, f"not-sale-{modes[0]}")
    seller_token = seller["tokens"]["access_token"]
    book = await create_book(client, seller_token, title=f"Free {modes[0]}")
    media = await upload_media(client, seller_token)
    payload = listing_payload(book_id=book["id"], image_id=media["id"])
    payload["listing_modes"] = modes
    payload["price_amount_cents"] = None
    created = await client.post("/api/v1/listings", headers=auth(seller_token), json=payload)
    assert created.status_code == 201, created.text
    published = await client.post(
        f"/api/v1/listings/{created.json()['id']}/publish", headers=auth(seller_token)
    )
    assert published.status_code == 200, published.text

    _, status, text = await cart_with(client, buyer, seller["user"]["id"], created.json()["id"])
    assert status == 422, text


@pytest.mark.asyncio
async def test_repeated_checkouts_make_one_order(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller, (buyer,) = await users(client, register_user, "double-click")
    listing = await create_published_listing(
        client, seller["tokens"]["access_token"], title="Double Click"
    )
    cart_id, *_ = await cart_with(client, buyer, seller["user"]["id"], listing["id"])

    # Sequential: the test database shares one connection, so it can't run checkouts in
    # parallel. Parallel ones are covered by the cart claim and uq_orders_cart_id in Postgres.
    responses = [await checkout(client, buyer, cart_id, "dc") for _ in range(3)]

    assert [r.status_code for r in responses] == [200, 200, 200], [r.text for r in responses]
    assert len({r.json()["id"] for r in responses}) == 1
    async with session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(Order)) == 1
    assert await stock(client, listing["id"]) == ("reserved", 0)


@pytest.mark.asyncio
async def test_an_offer_makes_one_order_priced_per_copy(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller, (buyer,) = await users(client, register_user, "offer-order")
    seller_token = seller["tokens"]["access_token"]
    book = await create_book(client, seller_token, title="Two Copies")
    media = await upload_media(client, seller_token)
    payload = listing_payload(book_id=book["id"], image_id=media["id"])
    payload["quantity"] = 2
    created = await client.post("/api/v1/listings", headers=auth(seller_token), json=payload)
    listing_id = created.json()["id"]
    await client.post(f"/api/v1/listings/{listing_id}/publish", headers=auth(seller_token))
    offer = await client.post(
        "/api/v1/offers",
        headers=auth(buyer),
        json={
            "amount_cents": 60_000,
            "fulfillment_method": "pickup",
            "listing_id": listing_id,
            "quantity": 2,
        },
    )
    assert offer.status_code == 201, offer.text
    accepted = await client.post(
        f"/api/v1/offers/{offer.json()['id']}/accept", headers=auth(seller_token), json={}
    )
    assert accepted.status_code == 200, accepted.text

    async with session_factory() as session:
        seller_user = await session.scalar(
            select(User).where(User.public_id == seller["user"]["id"])
        )
        service = PaymentsService(session)
        context = AuthenticatedRequestContext()
        first = await service.create_order_from_offer(
            offer.json()["id"], cast("User", seller_user), context
        )
        second = await service.create_order_from_offer(
            offer.json()["id"], cast("User", seller_user), context
        )

    assert first.id == second.id
    assert first.items[0].quantity == 2
    assert first.items[0].unit_price_cents == 30_000
    assert first.subtotal_cents == 60_000

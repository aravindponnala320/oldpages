from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.core.config import Settings
from oldpages_api.main import create_app
from oldpages_api.notifications.models import NotificationDelivery
from oldpages_api.shared.db.database import get_session


@pytest.mark.asyncio
async def test_chat_request_accept_send_message_and_notification_delivery_is_async(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    seller = await register_user(client, email="seller@example.com", username="seller")
    buyer = await register_user(client, email="buyer@example.com", username="buyer")
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Chat Book")

    request_response = await client.post(
        "/api/v1/chat-requests",
        headers=auth(buyer_token),
        json={"listing_id": listing["id"], "message": "Is this still available?"},
    )
    assert request_response.status_code == 201, request_response.text
    assert request_response.json()["status"] == "pending"

    accept_response = await client.post(
        f"/api/v1/chat-requests/{request_response.json()['id']}/accept",
        headers=auth(seller_token),
        json={"message": "Yes."},
    )
    assert accept_response.status_code == 200, accept_response.text
    conversation_id = accept_response.json()["conversation_id"]
    assert conversation_id is not None

    message_response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(buyer_token),
        json={"body": "Great, I can pick it up today.", "client_message_id": "buyer-msg-1"},
    )
    assert message_response.status_code == 201, message_response.text
    assert message_response.json()["client_message_id"] == "buyer-msg-1"

    seller_notifications = await client.get("/api/v1/notifications", headers=auth(seller_token))
    assert seller_notifications.status_code == 200
    notification_types = [item["type"] for item in seller_notifications.json()["items"]]
    assert "chat_request" in notification_types
    assert "message" in notification_types

    async with session_factory() as session:
        deliveries = (
            await session.execute(select(NotificationDelivery).order_by(NotificationDelivery.id))
        ).scalars()
        delivery_rows = list(deliveries)
    assert delivery_rows
    assert {delivery.status for delivery in delivery_rows} == {"pending"}


@pytest.mark.asyncio
async def test_unauthorized_users_cannot_read_conversations(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller2@example.com", username="seller2")
    buyer = await register_user(client, email="buyer2@example.com", username="buyer2")
    stranger = await register_user(client, email="stranger@example.com", username="stranger")
    conversation_id = await accepted_conversation(
        client,
        seller["tokens"]["access_token"],
        buyer["tokens"]["access_token"],
        title="Private Chat Book",
    )

    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(stranger["tokens"]["access_token"]),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_blocked_users_cannot_send_chat_requests(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller3@example.com", username="seller3")
    buyer = await register_user(client, email="buyer3@example.com", username="buyer3")
    seller_token = seller["tokens"]["access_token"]
    buyer_token = buyer["tokens"]["access_token"]
    listing = await create_published_listing(client, seller_token, title="Blocked Chat Book")

    block_response = await client.post(
        f"/api/v1/users/{buyer['user']['id']}/block",
        headers=auth(seller_token),
        json={"reason": "No contact"},
    )
    assert block_response.status_code == 201, block_response.text

    request_response = await client.post(
        "/api/v1/chat-requests",
        headers=auth(buyer_token),
        json={"listing_id": listing["id"], "message": "Can we chat?"},
    )

    assert request_response.status_code == 403


@pytest.mark.asyncio
async def test_duplicate_client_message_ids_do_not_create_duplicate_messages(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="seller4@example.com", username="seller4")
    buyer = await register_user(client, email="buyer4@example.com", username="buyer4")
    conversation_id = await accepted_conversation(
        client,
        seller["tokens"]["access_token"],
        buyer["tokens"]["access_token"],
        title="Idempotent Chat Book",
    )
    payload = {"body": "Same client message.", "client_message_id": "duplicate-1"}

    first = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(buyer["tokens"]["access_token"]),
        json=payload,
    )
    second = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(buyer["tokens"]["access_token"]),
        json=payload,
    )
    messages = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(seller["tokens"]["access_token"]),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] == second.json()["id"]
    assert len(messages.json()["items"]) == 1


def test_websocket_reconnect_replays_messages_after_last_seen(
    test_settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    app = create_app(test_settings)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as sync_client:
        seller = register_sync(sync_client, email="seller5@example.com", username="seller5")
        buyer = register_sync(sync_client, email="buyer5@example.com", username="buyer5")
        conversation_id = accepted_conversation_sync(
            sync_client,
            seller["tokens"]["access_token"],
            buyer["tokens"]["access_token"],
            title="WebSocket Chat Book",
        )
        first = send_message_sync(
            sync_client,
            conversation_id,
            buyer["tokens"]["access_token"],
            "ws-1",
            "First message.",
        )
        second = send_message_sync(
            sync_client,
            conversation_id,
            buyer["tokens"]["access_token"],
            "ws-2",
            "Second message.",
        )

        with sync_client.websocket_connect(
            f"/ws/conversations?access_token={seller['tokens']['access_token']}"
            f"&last_message_id={first['id']}"
        ) as websocket:
            connected = websocket.receive_json()
            replay = websocket.receive_json()
            websocket.send_json({"type": "close"})

        assert connected["type"] == "connected"
        assert replay["type"] == "message.created"
        assert replay["message"]["id"] == second["id"]


async def accepted_conversation(
    client: AsyncClient,
    seller_token: str,
    buyer_token: str,
    *,
    title: str,
) -> str:
    listing = await create_published_listing(client, seller_token, title=title)
    request_response = await client.post(
        "/api/v1/chat-requests",
        headers=auth(buyer_token),
        json={"listing_id": listing["id"], "message": "Can we chat?"},
    )
    assert request_response.status_code == 201, request_response.text
    accept_response = await client.post(
        f"/api/v1/chat-requests/{request_response.json()['id']}/accept",
        headers=auth(seller_token),
        json={},
    )
    assert accept_response.status_code == 200, accept_response.text
    conversation_id = accept_response.json()["conversation_id"]
    assert conversation_id is not None
    return cast("str", conversation_id)


async def create_published_listing(
    client: AsyncClient,
    token: str,
    *,
    title: str,
) -> dict[str, Any]:
    book = await create_book(client, token, title=title)
    media = await upload_media(client, token)
    create_response = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(book_id=book["id"], image_id=media["id"]),
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
            "authors": [{"name": "Chat Author"}],
            "description": "A catalog entry for chat tests.",
            "format": "paperback",
            "language": "en",
            "page_count": 250,
            "publisher": {"name": "Chat Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def upload_media(client: AsyncClient, token: str) -> dict[str, Any]:
    upload_response = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": "chat.jpg"},
    )
    assert upload_response.status_code == 200, upload_response.text
    complete_response = await client.post(
        f"/api/v1/media/{upload_response.json()['id']}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete_response.status_code == 200, complete_response.text
    return cast("dict[str, Any]", complete_response.json())


def accepted_conversation_sync(
    client: TestClient,
    seller_token: str,
    buyer_token: str,
    *,
    title: str,
) -> str:
    listing = create_published_listing_sync(client, seller_token, title=title)
    request_response = client.post(
        "/api/v1/chat-requests",
        headers=auth(buyer_token),
        json={"listing_id": listing["id"], "message": "Can we chat?"},
    )
    assert request_response.status_code == 201, request_response.text
    accept_response = client.post(
        f"/api/v1/chat-requests/{request_response.json()['id']}/accept",
        headers=auth(seller_token),
        json={},
    )
    assert accept_response.status_code == 200, accept_response.text
    return cast("str", accept_response.json()["conversation_id"])


def create_published_listing_sync(
    client: TestClient,
    token: str,
    *,
    title: str,
) -> dict[str, Any]:
    book = create_book_sync(client, token, title=title)
    media = upload_media_sync(client, token)
    create_response = client.post(
        "/api/v1/listings",
        headers=auth(token),
        json=listing_payload(book_id=book["id"], image_id=media["id"]),
    )
    assert create_response.status_code == 201, create_response.text
    publish_response = client.post(
        f"/api/v1/listings/{create_response.json()['id']}/publish",
        headers=auth(token),
    )
    assert publish_response.status_code == 200, publish_response.text
    return cast("dict[str, Any]", publish_response.json())


def register_sync(client: TestClient, *, email: str, username: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "display_name": username.title(),
            "email": email,
            "password": "correct horse battery staple",
            "privacy_accepted": True,
            "terms_accepted": True,
            "username": username,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def create_book_sync(client: TestClient, token: str, *, title: str) -> dict[str, Any]:
    response = client.post(
        "/api/v1/books",
        headers=auth(token),
        json={
            "authors": [{"name": "Chat Author"}],
            "description": "A catalog entry for websocket chat tests.",
            "format": "paperback",
            "language": "en",
            "page_count": 250,
            "publisher": {"name": "Chat Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def upload_media_sync(client: TestClient, token: str) -> dict[str, Any]:
    upload_response = client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": "chat.jpg"},
    )
    assert upload_response.status_code == 200, upload_response.text
    complete_response = client.post(
        f"/api/v1/media/{upload_response.json()['id']}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete_response.status_code == 200, complete_response.text
    return cast("dict[str, Any]", complete_response.json())


def send_message_sync(
    client: TestClient,
    conversation_id: str,
    token: str,
    client_message_id: str,
    body: str,
) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=auth(token),
        json={"body": body, "client_message_id": client_message_id},
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


def listing_payload(*, book_id: str, image_id: str) -> dict[str, Any]:
    return {
        "book_id": book_id,
        "condition": {
            "condition": "good",
            "damage_details": "Light shelf wear.",
            "highlighting_percent": 5,
        },
        "delivery_methods": [{"method": "pickup"}],
        "description": "A clean copy for a chat flow test.",
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
        "quantity": 1,
    }


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

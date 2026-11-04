from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.identity.models import UserProfile


@pytest.mark.asyncio
async def test_secret_communities_are_not_discoverable_and_private_content_is_protected(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(
        client,
        email="secret-owner@example.com",
        username="secret-owner",
    )
    other = await register_user(client, email="secret-other@example.com", username="secret-other")
    owner_token = owner["tokens"]["access_token"]
    secret = await create_community(
        client,
        owner_token,
        name="Hidden Readers",
        slug="hidden-readers",
        visibility="secret",
    )
    private = await create_community(
        client,
        owner_token,
        name="Private Readers",
        slug="private-readers",
        visibility="private",
    )

    discovery = await client.get("/api/v1/communities")
    secret_get = await client.get(f"/api/v1/communities/{secret['id']}")
    private_feed = await client.get(
        f"/api/v1/communities/{private['id']}/feed",
        headers=auth(other["tokens"]["access_token"]),
    )

    assert discovery.status_code == 200
    assert [item["id"] for item in discovery.json()["items"]] == [private["id"]]
    assert secret_get.status_code == 403
    assert private_feed.status_code == 403


@pytest.mark.asyncio
async def test_private_join_approval_allows_posts_comments_and_reactions(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner = await register_user(client, email="private-owner@example.com", username="private-own")
    member = await register_user(client, email="private-member@example.com", username="private-mem")
    owner_token = owner["tokens"]["access_token"]
    member_token = member["tokens"]["access_token"]
    community = await create_community(
        client,
        owner_token,
        name="Approval Readers",
        slug="approval-readers",
        visibility="private",
    )

    join = await client.post(
        f"/api/v1/communities/{community['id']}/join",
        headers=auth(member_token),
        json={"answers": {"reason": "I read locally."}},
    )
    blocked_post = await client.post(
        f"/api/v1/communities/{community['id']}/posts",
        headers=auth(member_token),
        json={"body": "Can I post yet?"},
    )
    approve = await client.post(
        f"/api/v1/communities/{community['id']}/approve-member",
        headers=auth(owner_token),
        json={"role": "member", "user_id": member["user"]["id"]},
    )
    post = await client.post(
        f"/api/v1/communities/{community['id']}/posts",
        headers=auth(member_token),
        json={"body": "First approved post.", "title": "Hello"},
    )
    comment = await client.post(
        f"/api/v1/posts/{post.json()['id']}/comments",
        headers=auth(owner_token),
        json={"body": "Welcome."},
    )
    reaction = await client.post(
        f"/api/v1/posts/{post.json()['id']}/reactions",
        headers=auth(member_token),
        json={"reaction_type": "love"},
    )
    feed = await client.get(
        f"/api/v1/communities/{community['id']}/feed",
        headers=auth(member_token),
    )

    assert join.status_code == 200, join.text
    assert join.json()["status"] == "pending"
    assert blocked_post.status_code == 403
    assert approve.status_code == 200, approve.text
    assert approve.json()["status"] == "active"
    assert post.status_code == 200, post.text
    assert comment.status_code == 200, comment.text
    assert reaction.status_code == 200, reaction.text
    assert feed.status_code == 200, feed.text
    assert feed.json()["items"][0]["id"] == post.json()["id"]
    assert feed.json()["items"][0]["comment_count"] == 1
    assert feed.json()["items"][0]["reaction_counts"] == {"love": 1}
    assert feed.json()["items"][0]["viewer_reaction"] == "love"


@pytest.mark.asyncio
async def test_moderator_scope_is_limited_to_assigned_community(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    owner_a = await register_user(client, email="owner-a@example.com", username="owner-a")
    owner_b = await register_user(client, email="owner-b@example.com", username="owner-b")
    requester = await register_user(client, email="requester@example.com", username="requester")
    community_a = await create_community(
        client,
        owner_a["tokens"]["access_token"],
        name="Community A",
        slug="community-a",
        visibility="private",
    )
    community_b = await create_community(
        client,
        owner_b["tokens"]["access_token"],
        name="Community B",
        slug="community-b",
        visibility="private",
    )
    join = await client.post(
        f"/api/v1/communities/{community_b['id']}/join",
        headers=auth(requester["tokens"]["access_token"]),
        json={"answers": {}},
    )

    wrong_owner = await client.post(
        f"/api/v1/communities/{community_b['id']}/approve-member",
        headers=auth(owner_a["tokens"]["access_token"]),
        json={"role": "member", "user_id": requester["user"]["id"]},
    )
    right_owner = await client.post(
        f"/api/v1/communities/{community_b['id']}/approve-member",
        headers=auth(owner_b["tokens"]["access_token"]),
        json={"role": "member", "user_id": requester["user"]["id"]},
    )

    assert community_a["viewer_membership_status"] == "active"
    assert join.status_code == 200
    assert wrong_owner.status_code == 403
    assert right_owner.status_code == 200, right_owner.text
    assert right_owner.json()["status"] == "active"


@pytest.mark.asyncio
async def test_institution_verified_community_requires_matching_profile_institution(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    owner = await register_user(client, email="inst-owner@example.com", username="inst-owner")
    matching = await register_user(client, email="inst-good@example.com", username="inst-good")
    mismatch = await register_user(client, email="inst-bad@example.com", username="inst-bad")
    await set_institution(session_factory, matching["user"]["id"], "Fergusson College")
    await set_institution(session_factory, mismatch["user"]["id"], "Different College")
    community = await create_community(
        client,
        owner["tokens"]["access_token"],
        institution="Fergusson College",
        name="Fergusson Readers",
        slug="fergusson-readers",
        visibility="institution_verified",
    )

    accepted = await client.post(
        f"/api/v1/communities/{community['id']}/join",
        headers=auth(matching["tokens"]["access_token"]),
        json={"answers": {}},
    )
    rejected = await client.post(
        f"/api/v1/communities/{community['id']}/join",
        headers=auth(mismatch["tokens"]["access_token"]),
        json={"answers": {}},
    )

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "active"
    assert rejected.status_code == 403


@pytest.mark.asyncio
async def test_community_marketplace_filters_active_listings_by_scope(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    seller = await register_user(client, email="market-seller@example.com", username="market-s")
    seller_token = seller["tokens"]["access_token"]
    pune_book = await create_book(client, seller_token, title="Pune Book")
    mumbai_book = await create_book(client, seller_token, title="Mumbai Book")
    pune_listing = await create_published_listing(
        client,
        seller_token,
        pune_book["id"],
        city="Pune",
    )
    await create_published_listing(client, seller_token, mumbai_book["id"], city="Mumbai")
    community = await create_community(
        client,
        seller_token,
        city="Pune",
        country="IN",
        name="Pune Marketplace",
        slug="pune-marketplace",
        visibility="public",
    )

    marketplace = await client.get(f"/api/v1/communities/{community['id']}/marketplace")

    assert marketplace.status_code == 200, marketplace.text
    assert [item["id"] for item in marketplace.json()["items"]] == [pune_listing["id"]]


async def create_community(
    client: AsyncClient,
    token: str,
    *,
    city: str | None = None,
    country: str | None = None,
    institution: str | None = None,
    name: str,
    slug: str,
    visibility: str,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/communities",
        headers=auth(token),
        json={
            "city": city,
            "community_type": "city" if city else "general",
            "country": country,
            "institution": institution,
            "name": name,
            "slug": slug,
            "visibility": visibility,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def set_institution(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: str,
    institution: str,
) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(UserProfile).where(UserProfile.user.has(public_id=user_id))
        )
        profile = result.scalar_one()
        profile.institution = institution
        await session.commit()


async def create_book(client: AsyncClient, token: str, *, title: str) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/books",
        headers=auth(token),
        json={
            "authors": [{"name": "Community Author"}],
            "description": "A catalog entry for community tests.",
            "format": "paperback",
            "language": "en",
            "page_count": 250,
            "publisher": {"name": "Community Publisher"},
            "title": title,
        },
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def create_published_listing(
    client: AsyncClient,
    token: str,
    book_id: str,
    *,
    city: str,
) -> dict[str, Any]:
    media = await upload_media(client, token, filename=f"{city.lower()}-listing.jpg")
    create = await client.post(
        "/api/v1/listings",
        headers=auth(token),
        json={
            "book_id": book_id,
            "condition": {
                "condition": "good",
                "damage_details": "Light shelf wear.",
                "highlighting_percent": 5,
            },
            "delivery_methods": [{"method": "pickup"}],
            "description": "A community marketplace listing with enough detail to publish.",
            "images": [{"alt_text": "Actual book cover", "media_id": media["id"]}],
            "listing_modes": ["sell"],
            "location": {
                "campus_pickup": True,
                "city": city,
                "country": "IN",
                "exact_latitude": "18.520430",
                "exact_longitude": "73.856744",
                "neighborhood": "Deccan",
                "pickup_notes_private": "Meet at the library gate.",
                "public_area": f"{city} public pickup",
                "state": "Maharashtra",
            },
            "price_amount_cents": 45000,
            "quantity": 1,
        },
    )
    assert create.status_code == 201, create.text
    publish = await client.post(
        f"/api/v1/listings/{create.json()['id']}/publish",
        headers=auth(token),
    )
    assert publish.status_code == 200, publish.text
    return cast("dict[str, Any]", publish.json())


async def upload_media(client: AsyncClient, token: str, *, filename: str) -> dict[str, Any]:
    upload = await client.post(
        "/api/v1/media/upload-url",
        headers=auth(token),
        json={"byte_size": 512_000, "content_type": "image/jpeg", "filename": filename},
    )
    assert upload.status_code == 200, upload.text
    complete = await client.post(
        f"/api/v1/media/{upload.json()['id']}/complete",
        headers=auth(token),
        json={"byte_size": 512_000},
    )
    assert complete.status_code == 200, complete.text
    return cast("dict[str, Any]", complete.json())


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

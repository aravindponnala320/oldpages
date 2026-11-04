from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.core.config import Settings
from oldpages_api.identity.models import User
from oldpages_api.identity.repository import IdentityRepository
from oldpages_api.identity.service import IdentityService


@pytest.mark.asyncio
async def test_public_profile_hides_private_fields(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    access_token = registered["tokens"]["access_token"]
    user_id = registered["user"]["id"]

    update_response = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "approximate_location": "Pune",
            "favorite_books": ["The Guide"],
            "hide_institution": True,
            "hide_location": True,
            "institution": "Fergusson College",
            "privacy_level": "private",
        },
    )
    assert update_response.status_code == 200

    public_response = await client.get(f"/api/v1/users/{user_id}")
    assert public_response.status_code == 200
    body = public_response.json()

    assert "email" not in body
    assert "favorite_books" not in body
    assert body["approximate_location"] is None
    assert body["institution"] is None
    assert body["privacy_level"] == "private"


@pytest.mark.asyncio
async def test_sessions_can_be_listed_and_revoked(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    access_token = registered["tokens"]["access_token"]

    sessions_response = await client.get(
        "/api/v1/users/me/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert len(sessions) == 1
    assert sessions[0]["current"] is True

    revoke_response = await client.delete(
        f"/api/v1/users/me/sessions/{sessions[0]['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoke_response.status_code == 204

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_blocked_users_cannot_initiate_chat(
    client: AsyncClient,
    register_user: RegisterUser,
    session_factory: async_sessionmaker[AsyncSession],
    test_settings: Settings,
) -> None:
    first = await register_user(
        client,
        email="first@example.com",
        display_name="First",
        username="first",
    )
    second = await register_user(
        client,
        email="second@example.com",
        display_name="Second",
        username="second",
    )

    block_response = await client.post(
        f"/api/v1/users/{second['user']['id']}/block",
        headers={"Authorization": f"Bearer {first['tokens']['access_token']}"},
        json={"reason": "No contact"},
    )
    assert block_response.status_code == 201

    async with session_factory() as session:
        repo = IdentityRepository(session)
        first_user = await repo.get_user_by_public_id(str(first["user"]["id"]))
        second_user = await repo.get_user_by_public_id(str(second["user"]["id"]))
        assert isinstance(first_user, User)
        assert isinstance(second_user, User)
        can_chat = await IdentityService(session, test_settings).can_initiate_chat(
            first_user.id,
            second_user.id,
        )

    assert can_chat is False

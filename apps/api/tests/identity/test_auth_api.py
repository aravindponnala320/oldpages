from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from conftest import RegisterUser
from oldpages_api.identity.models import ConsentRecord
from oldpages_api.identity.service import TERMS_VERSION


@pytest.mark.asyncio
async def test_register_verify_email_and_get_me(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered: dict[str, Any] = await register_user(client)
    access_token = registered["tokens"]["access_token"]
    verification_token = registered["email_verification"]["token"]

    verify_response = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": verification_token},
    )
    assert verify_response.status_code == 204

    me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    body = me_response.json()
    assert body["email"] == "reader@example.com"
    assert body["email_verified"] is True
    assert body["privacy"]["hide_location"] is True


@pytest.mark.asyncio
async def test_refresh_token_rotation_detects_reuse(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    original_refresh = registered["tokens"]["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh},
    )
    assert refresh_response.status_code == 200
    rotated_refresh = refresh_response.json()["tokens"]["refresh_token"]
    assert rotated_refresh != original_refresh

    reuse_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh},
    )
    assert reuse_response.status_code == 401
    assert reuse_response.json()["type"] == "https://oldpages.in/problems/refresh-token-reuse"


@pytest.mark.asyncio
async def test_forgot_and_reset_password(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    await register_user(client)

    forgot_response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reader@example.com"},
    )
    assert forgot_response.status_code == 200
    reset_token = forgot_response.json()["development_token"]["token"]

    reset_response = await client.post(
        "/api/v1/auth/reset-password",
        json={"new_password": "new correct horse battery", "token": reset_token},
    )
    assert reset_response.status_code == 204

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reader@example.com", "password": "correct horse battery staple"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reader@example.com", "password": "new correct horse battery"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_oauth_links_verified_password_account(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)
    await client.post(
        "/api/v1/auth/verify-email",
        json={"token": registered["email_verification"]["token"]},
    )

    response = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "dev:google:google-reader-1:reader@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == registered["user"]["id"]
    password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reader@example.com", "password": "correct horse battery staple"},
    )
    assert password_login.status_code == 200


@pytest.mark.asyncio
async def test_oauth_link_to_unverified_account_drops_password_and_sessions(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    registered = await register_user(client)

    response = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "dev:google:google-reader-1:reader@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == registered["user"]["id"]
    assert response.json()["user"]["email_verified"] is True
    password_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reader@example.com", "password": "correct horse battery staple"},
    )
    assert password_login.status_code == 401
    old_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered["tokens"]["refresh_token"]},
    )
    assert old_refresh.status_code == 401


@pytest.mark.asyncio
async def test_oauth_rejects_second_account_from_same_provider(
    client: AsyncClient,
    register_user: RegisterUser,
) -> None:
    await register_user(client)
    await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "dev:google:google-reader-1:reader@example.com"},
    )

    response = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "dev:google:google-reader-2:reader@example.com"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_oauth_creates_new_development_account(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post(
        "/api/v1/auth/oauth/google",
        json={"id_token": "dev:google:google-reader-2:oauth@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "oauth@example.com"
    assert response.json()["user"]["email_verified"] is True
    async with session_factory() as session:
        consents = (await session.execute(select(ConsentRecord))).scalars().all()
    assert [c.terms_version for c in consents] == [TERMS_VERSION]

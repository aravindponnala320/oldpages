from __future__ import annotations

from typing import Any, cast

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from oldpages_api.core.config import Settings

EMAIL = "reader@example.com"
NEW_PASSWORD = "a brand new passphrase"


class CountingRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> None:  # noqa: ARG002
        return None


async def request_reset(client: AsyncClient, email: str = EMAIL) -> dict[str, Any]:
    response = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200, response.text
    return cast("dict[str, Any]", response.json())


async def reset(client: AsyncClient, token: str, password: str = NEW_PASSWORD) -> int:
    response = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": password}
    )
    return response.status_code


async def login(client: AsyncClient, password: str, email: str = EMAIL) -> int:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return response.status_code


@pytest.mark.asyncio
async def test_google_only_account_can_set_a_password(client: AsyncClient) -> None:
    signup = await client.post(
        "/api/v1/auth/oauth/google", json={"id_token": "dev:google:g-1:googler@example.com"}
    )
    assert signup.status_code == 200, signup.text
    assert await login(client, NEW_PASSWORD, "googler@example.com") == 401

    token = (await request_reset(client, "googler@example.com"))["development_token"]["token"]

    assert await reset(client, token) == 204
    assert await login(client, NEW_PASSWORD, "googler@example.com") == 200


@pytest.mark.asyncio
async def test_reset_verifies_the_email_and_signs_out_everywhere(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    registered = await register_user(client)  # email not verified yet
    old_refresh = registered["tokens"]["refresh_token"]
    token = (await request_reset(client, "  Reader@Example.COM "))["development_token"]["token"]

    assert await reset(client, token) == 204

    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 401
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": NEW_PASSWORD}
    )
    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login_response.json()['tokens']['access_token']}"},
    )
    assert me.json()["email_verified"] is True


@pytest.mark.asyncio
async def test_links_work_once_and_a_newer_link_replaces_older_ones(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    await register_user(client)
    first = (await request_reset(client))["development_token"]["token"]
    second = (await request_reset(client))["development_token"]["token"]

    assert await reset(client, first) == 401
    assert await reset(client, second) == 204
    assert await reset(client, second, "yet another passphrase") == 401
    assert await reset(client, "x" * 43) == 401


@pytest.mark.asyncio
async def test_short_passwords_are_refused(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    await register_user(client)
    token = (await request_reset(client))["development_token"]["token"]

    assert await reset(client, token, "short pass") == 422
    assert await reset(client, token) == 204  # the refused attempt didn't use the link up


@pytest.mark.asyncio
async def test_answer_never_reveals_whether_an_account_exists(
    client: AsyncClient, register_user: RegisterUser, test_settings: Settings
) -> None:
    await register_user(client)
    test_settings.expose_development_auth_tokens = False

    known = await request_reset(client)
    unknown = await request_reset(client, "nobody@example.com")

    assert known == unknown == {"accepted": True, "development_token": None}


@pytest.mark.asyncio
async def test_repeated_requests_for_one_email_are_limited(
    client: AsyncClient,
    register_user: RegisterUser,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import oldpages_api.shared.cache.redis as redis_mod

    fake = CountingRedis()
    monkeypatch.setattr(redis_mod, "get_redis", lambda: fake)
    await register_user(client)
    test_settings.auth_rate_limit_enabled = True

    answers = [await request_reset(client) for _ in range(4)]

    assert all(a["accepted"] for a in answers)
    assert [a["development_token"] is not None for a in answers] == [True, True, True, False]
    assert all(EMAIL not in key for key in fake.counts)  # keys are hashed

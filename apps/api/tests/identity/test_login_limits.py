from __future__ import annotations

import pytest
from httpx import AsyncClient

from conftest import RegisterUser
from oldpages_api.core.config import Settings

EMAIL = "reader@example.com"
PASSWORD = "correct horse battery staple"


class MemoryRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return str(self.counts[key]) if key in self.counts else None

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> None:  # noqa: ARG002
        return None


@pytest.fixture
def limits_on(test_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> MemoryRedis:
    import oldpages_api.shared.cache.redis as redis_mod

    fake = MemoryRedis()
    monkeypatch.setattr(redis_mod, "get_redis", lambda: fake)
    test_settings.auth_rate_limit_enabled = True
    test_settings.login_failures_per_email = 3
    return fake


async def login(client: AsyncClient, password: str) -> int:
    response = await client.post("/api/v1/auth/login", json={"email": EMAIL, "password": password})
    return response.status_code


@pytest.mark.asyncio
async def test_repeated_wrong_passwords_lock_the_email(
    client: AsyncClient, register_user: RegisterUser, limits_on: MemoryRedis
) -> None:
    await register_user(client)

    assert await login(client, PASSWORD) == 200  # successes don't count
    assert [await login(client, "wrong guess") for _ in range(3)] == [401, 401, 401]
    assert await login(client, PASSWORD) == 429  # even the right password waits now
    assert all(EMAIL not in key for key in limits_on.counts)


@pytest.mark.asyncio
async def test_limits_do_nothing_when_switched_off(
    client: AsyncClient, register_user: RegisterUser
) -> None:
    await register_user(client)

    assert [await login(client, "wrong guess") for _ in range(12)] == [401] * 12
    assert await login(client, PASSWORD) == 200

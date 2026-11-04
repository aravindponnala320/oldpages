from __future__ import annotations

import pytest
from httpx import AsyncClient

from oldpages_api.health import router as health_router


async def _ok() -> None:
    return None


async def _fail() -> None:
    raise RuntimeError("dependency unavailable")


@pytest.mark.asyncio
async def test_live_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "health-test"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "health-test"
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_health_returns_ok_when_dependencies_pass(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health_router, "check_database", _ok)
    monkeypatch.setattr(health_router, "check_redis", _ok)

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["components"]["database"]["status"] == "ok"
    assert response.json()["components"]["redis"]["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_health_returns_503_when_dependency_fails(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health_router, "check_database", _ok)
    monkeypatch.setattr(health_router, "check_redis", _fail)

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["components"]["redis"]["status"] == "error"

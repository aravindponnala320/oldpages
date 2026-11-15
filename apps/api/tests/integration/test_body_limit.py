from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_oversized_bodies_are_refused_before_parsing(client: AsyncClient) -> None:
    big = b'{"email": "' + b"a" * 1_100_000 + b'"}'
    response = await client.post(
        "/api/v1/auth/login", content=big, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["title"] == "Request Too Large"


@pytest.mark.asyncio
async def test_oversized_streamed_bodies_are_refused(client: AsyncClient) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        for _ in range(12):
            yield b" " * 100_000

    response = await client.post(
        "/api/v1/auth/login", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_normal_requests_pass(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "x" * 12}
    )
    assert response.status_code != 413

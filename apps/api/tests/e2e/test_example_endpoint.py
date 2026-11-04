from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_example_endpoint_returns_contract_and_request_id(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/foundation/example",
        headers={"X-Request-ID": "example-e2e"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "example-e2e"
    assert response.json() == {
        "message": "OldPages API foundation is running.",
        "request_id": "example-e2e",
        "service": "oldpages-api",
        "version": "0.0.0",
    }

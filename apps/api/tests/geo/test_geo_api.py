from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient

from oldpages_api.geo import http as geo_http


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:  # noqa: ARG002
        self._store[key] = value


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")


class FakeHttpClient:
    def __init__(self, mapping: dict[str, Any]) -> None:
        # Values may be raw payloads or FakeResponse instances (e.g. to inject 404s).
        self.mapping = mapping
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def get(self, url: str, params: dict[str, Any], headers: dict[str, str], timeout: float) -> FakeResponse:  # noqa: ARG002
        self.calls.append((url, params))
        value = self.mapping.get(url)
        if isinstance(value, FakeResponse):
            return value
        if value is None:
            return FakeResponse(None, status_code=404)
        return FakeResponse(value)


@pytest.fixture(autouse=True)
def _reset_geo_http() -> AsyncIterator[None]:
    geo_http.set_http_client(None)
    yield
    geo_http.set_http_client(None)


@pytest.fixture
def patch_redis(monkeypatch: pytest.MonkeyPatch) -> FakeRedis:
    import oldpages_api.geo.dependencies as geo_deps
    import oldpages_api.shared.cache.redis as redis_mod

    fake = FakeRedis()
    monkeypatch.setattr(redis_mod, "get_redis", lambda: fake)
    monkeypatch.setattr(geo_deps, "get_redis", lambda: fake)
    return fake


async def test_detect_returns_unknown_when_no_geoip_db(client: AsyncClient) -> None:
    response = await client.get("/api/v1/geo/detect")
    assert response.status_code == 200
    assert response.json() == {"location": None, "source": "unknown"}


async def test_geo_search_hits_nominatim_and_normalises_addresses(
    client: AsyncClient, patch_redis: FakeRedis
) -> None:
    payload = [
        {
            "display_name": "Hyderabad, Telangana, India",
            "lat": "17.3850",
            "lon": "78.4867",
            "type": "city",
            "address": {
                "city": "Hyderabad",
                "state": "Telangana",
                "country": "India",
                "country_code": "in",
                "postcode": "500001",
            },
        }
    ]
    fake_http = FakeHttpClient({"https://nominatim.openstreetmap.org/search": payload})
    geo_http.set_http_client(fake_http)

    response = await client.get("/api/v1/geo/search?q=Hyderabad")
    assert response.status_code == 200, response.text
    first = response.json()["items"][0]
    assert first["city"] == "Hyderabad"
    assert first["country_code"] == "IN"
    assert first["latitude"] == pytest.approx(17.3850)
    assert len(fake_http.calls) == 1

    # Second call should be served from Redis cache — no new upstream request.
    response = await client.get("/api/v1/geo/search?q=Hyderabad")
    assert response.status_code == 200
    assert len(fake_http.calls) == 1


async def test_active_location_sets_and_reads_back_cookie(client: AsyncClient) -> None:
    payload = {
        "location": {
            "latitude": 17.385,
            "longitude": 78.4867,
            "city": "Hyderabad",
            "country_code": "IN",
            "radius_km": 25,
        }
    }
    response = await client.put("/api/v1/me/location/active", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["active"]["city"] == "Hyderabad"
    assert body["source"] == "manual"

    cookie = client.cookies.get("op_loc")
    assert cookie
    decoded = json.loads(base64.urlsafe_b64decode(cookie + "=" * (-len(cookie) % 4)))
    assert decoded["city"] == "Hyderabad"

    follow_up = await client.get("/api/v1/me/location")
    assert follow_up.status_code == 200
    assert follow_up.json()["active"]["city"] == "Hyderabad"


async def test_persist_as_home_is_silent_no_op_when_anonymous(client: AsyncClient) -> None:
    response = await client.put(
        "/api/v1/me/location/active",
        json={
            "location": {"latitude": 12.9716, "longitude": 77.5946, "city": "Bengaluru"},
            "persist_as_home": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["home"] is None


async def test_home_location_persists_and_becomes_the_active_fallback(
    client: AsyncClient, register_user
) -> None:
    registration = await register_user(client)
    token = registration["tokens"]["access_token"]
    payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "city": "Bengaluru",
        "country_code": "IN",
        "radius_km": 40,
    }
    response = await client.put(
        "/api/v1/me/location/home",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    view = await client.get(
        "/api/v1/me/location", headers={"Authorization": f"Bearer {token}"}
    )
    assert view.status_code == 200
    body = view.json()
    assert body["home"]["city"] == "Bengaluru"
    assert body["active"]["city"] == "Bengaluru"
    assert body["source"] == "home"


async def test_pincode_lookup_india_uses_postalpincode(
    client: AsyncClient, patch_redis: FakeRedis
) -> None:
    postal_body = [
        {
            "Message": "Number of Post Office(s) found: 1",
            "Status": "Success",
            "PostOffice": [
                {
                    "Name": "Hyderabad G.P.O.",
                    "District": "Hyderabad",
                    "State": "Telangana",
                    "Country": "India",
                    "Pincode": "500001",
                }
            ],
        }
    ]
    zippo_body = {
        "post code": "500001",
        "country": "India",
        "country abbreviation": "IN",
        "places": [
            {
                "place name": "Hyderabad",
                "state": "Telangana",
                "latitude": "17.3850",
                "longitude": "78.4867",
            }
        ],
    }
    fake_http = FakeHttpClient(
        {
            "https://api.postalpincode.in/pincode/500001": postal_body,
            "https://api.zippopotam.us/in/500001": zippo_body,
        }
    )
    geo_http.set_http_client(fake_http)

    response = await client.get("/api/v1/geo/pincode/500001?cc=IN")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["city"] == "Hyderabad"
    assert body["state"] == "Telangana"
    assert body["country_code"] == "IN"
    assert body["postal_code"] == "500001"
    assert body["latitude"] == pytest.approx(17.385)
    assert body["longitude"] == pytest.approx(78.4867)


async def test_pincode_lookup_us_uses_zippopotam(
    client: AsyncClient, patch_redis: FakeRedis
) -> None:
    fake_http = FakeHttpClient(
        {
            "https://api.zippopotam.us/us/94103": {
                "post code": "94103",
                "country": "United States",
                "country abbreviation": "US",
                "places": [
                    {
                        "place name": "San Francisco",
                        "state": "California",
                        "state abbreviation": "CA",
                        "latitude": "37.7749",
                        "longitude": "-122.4194",
                    }
                ],
            }
        }
    )
    geo_http.set_http_client(fake_http)

    response = await client.get("/api/v1/geo/pincode/94103?cc=US")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["city"] == "San Francisco"
    assert body["state"] == "California"
    assert body["country_code"] == "US"
    assert body["latitude"] == pytest.approx(37.7749)


async def test_pincode_lookup_uses_cache_on_repeat(
    client: AsyncClient, patch_redis: FakeRedis
) -> None:
    fake_http = FakeHttpClient(
        {
            "https://api.zippopotam.us/us/94103": {
                "post code": "94103",
                "country": "United States",
                "places": [
                    {
                        "place name": "San Francisco",
                        "state": "California",
                        "latitude": "37.7749",
                        "longitude": "-122.4194",
                    }
                ],
            }
        }
    )
    geo_http.set_http_client(fake_http)

    r1 = await client.get("/api/v1/geo/pincode/94103?cc=US")
    r2 = await client.get("/api/v1/geo/pincode/94103?cc=US")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["city"] == r2.json()["city"] == "San Francisco"
    # Only one upstream call — second is served from Redis.
    assert len(fake_http.calls) == 1


async def test_pincode_lookup_not_found_returns_null(
    client: AsyncClient, patch_redis: FakeRedis
) -> None:
    fake_http = FakeHttpClient({})  # 404 for every URL
    geo_http.set_http_client(fake_http)

    response = await client.get("/api/v1/geo/pincode/00000?cc=US")
    assert response.status_code == 200
    assert response.json() is None


async def test_search_endpoint_accepts_x_user_location_header(client: AsyncClient) -> None:
    header_payload = {
        "latitude": 17.385,
        "longitude": 78.4867,
        "city": "Hyderabad",
        "radius_km": 15,
    }
    encoded = (
        base64.urlsafe_b64encode(json.dumps(header_payload).encode()).decode().rstrip("=")
    )
    # Just check we don't 500 — actual filtering is exercised elsewhere.
    response = await client.get(
        "/api/v1/search/listings", headers={"X-User-Location": encoded}
    )
    assert response.status_code == 200

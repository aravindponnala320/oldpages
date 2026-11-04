"""Nominatim (OpenStreetMap) proxy with Redis caching."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from redis.asyncio import Redis

from oldpages_api.core.config import Settings
from oldpages_api.geo.schemas import GeoSearchItem, LocationPayload

logger = logging.getLogger(__name__)

_SEARCH_KEY = "geo:nominatim:search:v1:"
_REVERSE_KEY = "geo:nominatim:reverse:v1:"


def _hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


async def _cached_get(
    client: Any, redis: Redis, url: str, params: dict[str, Any], settings: Settings, key: str
) -> Any:
    hit = await redis.get(key)
    if hit is not None:
        try:
            return json.loads(hit)
        except json.JSONDecodeError:
            pass
    headers = {
        "User-Agent": settings.nominatim_user_agent,
        "Accept": "application/json",
    }
    response = await client.get(
        url, params=params, headers=headers, timeout=settings.nominatim_timeout_seconds
    )
    response.raise_for_status()
    body = response.json()
    await redis.setex(key, settings.geo_cache_ttl_seconds, json.dumps(body))
    return body


def _pick(address: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = address.get(key)
        if value:
            return str(value)
    return None


def _to_item(entry: dict[str, Any]) -> GeoSearchItem | None:
    try:
        latitude = float(entry["lat"])
        longitude = float(entry["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    address = entry.get("address") or {}
    country_code = address.get("country_code")
    return GeoSearchItem(
        display_name=str(entry.get("display_name") or ""),
        latitude=latitude,
        longitude=longitude,
        city=_pick(address, ("city", "town", "village", "hamlet", "municipality", "suburb")),
        state=_pick(address, ("state", "region", "province")),
        country=address.get("country"),
        country_code=country_code.upper() if country_code else None,
        postal_code=address.get("postcode"),
        type=entry.get("type") or entry.get("class"),
    )


async def search(
    query: str,
    settings: Settings,
    redis: Redis,
    http_client: Any,
    limit: int = 8,
    country_codes: str | None = None,
) -> list[GeoSearchItem]:
    query = query.strip()
    if len(query) < 2:
        return []
    params: dict[str, Any] = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
        "accept-language": "en",
    }
    if country_codes:
        params["countrycodes"] = country_codes
    key = _SEARCH_KEY + _hash(params)
    url = settings.nominatim_base_url.rstrip("/") + "/search"
    try:
        body = await _cached_get(http_client, redis, url, params, settings, key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nominatim search failed: %s", exc)
        return []
    if not isinstance(body, list):
        return []
    items = []
    for entry in body:
        item = _to_item(entry)
        if item is not None:
            items.append(item)
    return items


async def reverse(
    latitude: float,
    longitude: float,
    settings: Settings,
    redis: Redis,
    http_client: Any,
) -> LocationPayload | None:
    params = {
        "lat": round(latitude, 4),  # ~11m precision; also improves cache hit rate
        "lon": round(longitude, 4),
        "format": "jsonv2",
        "addressdetails": 1,
        "zoom": 12,
    }
    key = _REVERSE_KEY + _hash(params)
    url = settings.nominatim_base_url.rstrip("/") + "/reverse"
    try:
        body = await _cached_get(http_client, redis, url, params, settings, key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nominatim reverse failed: %s", exc)
        return None
    if not isinstance(body, dict):
        return None
    item = _to_item(body)
    if item is None:
        return None
    return LocationPayload(
        latitude=latitude,
        longitude=longitude,
        city=item.city,
        state=item.state,
        country=item.country,
        country_code=item.country_code,
        postal_code=item.postal_code,
        display_name=item.display_name,
        radius_km=settings.geo_default_radius_km,
    )

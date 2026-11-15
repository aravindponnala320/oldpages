"""Nominatim (OpenStreetMap) proxy with Redis caching."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any

from redis.asyncio import Redis

from oldpages_api.core.config import Settings
from oldpages_api.geo import places
from oldpages_api.geo.schemas import GeoSearchItem, LocationPayload

logger = logging.getLogger(__name__)

_SEARCH_KEY = "geo:nominatim:search:v2:"
_REVERSE_KEY = "geo:nominatim:reverse:v3:"


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


_WARD_PREFIX = re.compile(r"^(ward|zone|circle)\s*(no\.?\s*)?\d+\s*[-,:]?\s*", re.IGNORECASE)

# Area-level features only: towns, suburbs, wards, postcodes and the railway
# stations people use as landmarks. Bus stops, shops, rivers, buildings and
# housing societies are noise.
_KEEP_CATEGORIES = {"place", "boundary"}
_KEEP_EXTRA = {("railway", "station")}
_SETTLEMENT_TYPES = {"city", "town", "village", "hamlet", "municipality"}
_CITY_KEYS = ("city", "town", "municipality", "village", "hamlet")
_LOCALITY_KEYS = ("suburb", "neighbourhood", "quarter", "residential", "city_block")


def _pick(address: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = address.get(key)
        if value:
            return str(value)
    return None


_CITY_SUFFIX = re.compile(
    r"\s+(municipal corporation|city corporation|corporation"
    r"|subdistrict|tehsil|taluka|taluk|mandal|county)$",
    re.IGNORECASE,
)
_ADMIN_UNIT = re.compile(r"\b(ward|zone|corporation|municipal)\b", re.IGNORECASE)


def _clean_locality(value: str | None) -> str | None:
    if not value:
        return None
    # "Downtown Toronto (CN Tower / King and Spadina / …)" -> "Downtown Toronto"
    value = _WARD_PREFIX.sub("", re.sub(r"\s*\(.*\)\s*$", "", value)).strip()
    # "K/W Ward", "Mumbai Zone 3": civic units nobody uses as an address.
    return None if not value or _ADMIN_UNIT.search(value) else value


def _locality(address: dict[str, Any]) -> str | None:
    for key in _LOCALITY_KEYS:
        value = _clean_locality(address.get(key))
        if value:
            return value
    return None


def label(*parts: str | None) -> str:
    """Join place parts, skipping blanks and repeats ("Delhi, Delhi" -> "Delhi")."""
    seen: list[str] = []
    for part in parts:
        if part and part.lower() not in (s.lower() for s in seen):
            seen.append(part)
    return ", ".join(seen)


def _is_area(entry: dict[str, Any]) -> bool:
    category = entry.get("category") or entry.get("class")
    return category in _KEEP_CATEGORIES or (category, entry.get("type")) in _KEEP_EXTRA


def _to_item(entry: dict[str, Any]) -> GeoSearchItem | None:
    try:
        latitude = float(entry["lat"])
        longitude = float(entry["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    address = entry.get("address") or {}
    country_code = (address.get("country_code") or "").upper() or None
    names = entry.get("namedetails") or {}
    name = names.get("name:en") or entry.get("name") or None
    addresstype = entry.get("addresstype") or entry.get("type")

    city = _pick(address, _CITY_KEYS)
    locality = _locality(address)
    if addresstype in _SETTLEMENT_TYPES and name:
        city, locality = name, None
    elif (
        name
        and _is_area(entry)
        and addresstype not in {"postcode", "state", "country"}
        and name != city
        and not str(name).isdigit()
        and _clean_locality(str(name))
    ):
        # The matched feature is itself the area ("Andheri" station, "Gachibowli" suburb).
        locality = _clean_locality(str(name))
    if not city and country_code == "IN":
        # OSM often tags only the subdistrict ("Pune City Subdistrict"); name the town instead.
        near = places.nearest(latitude, longitude)
        city = near.name if near else None
    if not city:
        city = _pick(address, ("county", "state_district")) or (None if locality else name)
    if city:
        city = _CITY_SUFFIX.sub("", city) or city  # "Jaipur Municipal Corporation" -> "Jaipur"
    state = _pick(address, ("state", "region", "province"))
    if country_code == "IN":
        state = places.canonical_state(state)
        city = places.canonical_city(city, state)
    if (
        locality
        and city
        and (locality.lower() == city.lower() or places.canonical_city(locality, state) == city)
    ):
        locality = None
    country = address.get("country")
    return GeoSearchItem(
        display_name=label(locality, city, state, country) or str(entry.get("display_name") or ""),
        latitude=latitude,
        longitude=longitude,
        locality=locality,
        city=city,
        state=state,
        country=country,
        country_code=country_code,
        postal_code=address.get("postcode"),
        type=addresstype,
    )


def _items(body: Any, areas_only: bool) -> list[GeoSearchItem]:
    if not isinstance(body, list):
        return []
    items: list[GeoSearchItem] = []
    seen: set[tuple[str, str, str]] = set()
    labels: set[str] = set()
    for entry in body:
        if areas_only and not _is_area(entry):
            continue
        item = _to_item(entry)
        if item is None:
            continue
        key = ((item.locality or "").lower(), (item.city or "").lower(), (item.state or "").lower())
        if key in seen or item.display_name.lower() in labels:
            continue
        seen.add(key)
        labels.add(item.display_name.lower())
        items.append(item)
    return items


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
        # Over-fetch: noise (bus stops, rivers) and duplicates are filtered out below.
        "limit": min(limit * 2, 40),
        "namedetails": 1,
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
    return _items(body, areas_only=True)[:limit]


async def postcode(
    code: str,
    country_code: str,
    settings: Settings,
    redis: Redis,
    http_client: Any,
) -> GeoSearchItem | None:
    """Centroid of a postal code area (structured search, far more exact than a city centre)."""
    params: dict[str, Any] = {
        "postalcode": code,
        "countrycodes": country_code.lower(),
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 1,
        "accept-language": "en",
    }
    key = _SEARCH_KEY + _hash(params)
    url = settings.nominatim_base_url.rstrip("/") + "/search"
    try:
        body = await _cached_get(http_client, redis, url, params, settings, key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nominatim postcode search failed: %s", exc)
        return None
    items = _items(body, areas_only=False)
    return items[0] if items else None


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
        "zoom": 16,  # street level; only the area fields of the address are used
        "accept-language": "en",
    }
    key = _REVERSE_KEY + _hash(params)
    url = settings.nominatim_base_url.rstrip("/") + "/reverse"
    try:
        body = await _cached_get(http_client, redis, url, params, settings, key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nominatim reverse failed: %s", exc)
        return None
    if not isinstance(body, dict) or "lat" not in body:
        return None
    item = _to_item(body)
    if item is None:
        return None
    return LocationPayload(
        latitude=latitude,
        longitude=longitude,
        locality=item.locality,
        city=item.city,
        state=item.state,
        country=item.country,
        country_code=item.country_code,
        postal_code=item.postal_code,
        display_name=item.display_name,
        radius_km=settings.geo_default_radius_km,
    )

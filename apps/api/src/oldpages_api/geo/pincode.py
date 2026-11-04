"""Pincode / ZIP lookup — India via postalpincode.in, everywhere else via Zippopotam.

Both APIs are free, key-less, open-data services. Results are Redis-cached for
7 days (via settings.geo_cache_ttl_seconds) since postal codes don't move.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from redis.asyncio import Redis

from oldpages_api.core.config import Settings
from oldpages_api.geo import nominatim
from oldpages_api.geo.schemas import LocationPayload

logger = logging.getLogger(__name__)

_CACHE_KEY = "geo:pincode:v1:"
_POSTALPIN_IN = "https://api.postalpincode.in/pincode"
_ZIPPOPOTAM = "https://api.zippopotam.us"


def _clean(pincode: str) -> str:
    return re.sub(r"[\s-]+", "", pincode).strip().upper()


async def _cached(
    redis: Redis, key: str, settings: Settings, loader: Any
) -> LocationPayload | None:
    hit = await redis.get(key)
    if hit is not None:
        try:
            data = json.loads(hit)
        except json.JSONDecodeError:
            data = None
        if data is None:
            return None
        try:
            return LocationPayload(**data)
        except Exception:  # noqa: BLE001
            return None

    payload = await loader()
    if payload is None:
        # Cache the "not found" for 1h so we don't hammer the upstream on typos.
        await redis.setex(key, min(3600, settings.geo_cache_ttl_seconds), "null")
        return None
    await redis.setex(
        key,
        settings.geo_cache_ttl_seconds,
        json.dumps(payload.model_dump(exclude_none=True)),
    )
    return payload


async def _india_lookup(
    pincode: str, settings: Settings, http_client: Any, redis: Any
) -> LocationPayload | None:
    """India: postalpincode.in for authoritative district/state, Nominatim for coords."""
    url = f"{_POSTALPIN_IN}/{pincode}"
    try:
        response = await http_client.get(
            url,
            params={},
            headers={"Accept": "application/json", "User-Agent": settings.nominatim_user_agent},
            timeout=settings.nominatim_timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("postalpincode.in failed for %s: %s", pincode, exc)
        # Fall through to Zippopotam so we still return *something*.
        return await _zippopotam_lookup("IN", pincode, settings, http_client)
    if not isinstance(body, list) or not body:
        return await _zippopotam_lookup("IN", pincode, settings, http_client)
    _ = redis  # (silence linter when the fallback path is taken)
    envelope = body[0]
    if envelope.get("Status") != "Success":
        return None
    offices = envelope.get("PostOffice") or []
    if not offices:
        return None
    office = offices[0]  # Any office in the pincode gives the same district/state.
    city = office.get("District") or office.get("Block") or office.get("Name")
    state = office.get("State")
    country = office.get("Country") or "India"

    # Get accurate coordinates by geocoding the canonical city name via Nominatim.
    # Zippopotam has patchy India coverage (e.g. PIN 500001 returns a centroid
    # ~85km from the real city center), which breaks the radius filter.
    latitude, longitude = await _geocode_city_or_fallback(
        pincode, city, state, settings, http_client, redis
    )

    return LocationPayload(
        latitude=latitude,
        longitude=longitude,
        city=city,
        state=state,
        country=country,
        country_code="IN",
        postal_code=pincode,
        display_name=f"{office.get('Name', pincode)}, {city}, {state}, {country}",
        radius_km=settings.geo_default_radius_km,
    )


async def _geocode_city_or_fallback(
    pincode: str,
    city: str | None,
    state: str | None,
    settings: Settings,
    http_client: Any,
    redis: Any = None,
) -> tuple[float, float]:
    """Return (lat, lng) for the given city, falling back to Zippopotam / (0,0)."""
    # Prefer Nominatim search on "city, state, IN" — most accurate for canonical
    # city centers. Requires a Redis client for its internal cache.
    if city and redis is not None:
        query = ", ".join(p for p in (city, state, "India") if p)
        try:
            results = await nominatim.search(
                query, settings, redis, http_client, limit=1, country_codes="in"
            )
            if results:
                return results[0].latitude, results[0].longitude
        except Exception:  # noqa: BLE001
            pass
    zippo = await _zippopotam_lookup("IN", pincode, settings, http_client)
    if zippo is not None:
        return zippo.latitude, zippo.longitude
    return 0.0, 0.0


async def _zippopotam_lookup(
    country_code: str, pincode: str, settings: Settings, http_client: Any
) -> LocationPayload | None:
    url = f"{_ZIPPOPOTAM}/{country_code.lower()}/{pincode}"
    try:
        response = await http_client.get(
            url,
            params={},
            headers={"Accept": "application/json", "User-Agent": settings.nominatim_user_agent},
            timeout=settings.nominatim_timeout_seconds,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        body = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("zippopotam failed for %s/%s: %s", country_code, pincode, exc)
        return None
    places = body.get("places") or []
    if not places:
        return None
    place = places[0]
    try:
        latitude = float(place["latitude"])
        longitude = float(place["longitude"])
    except (KeyError, TypeError, ValueError):
        latitude = 0.0
        longitude = 0.0
    country_name = body.get("country") or country_code.upper()
    state = place.get("state") or place.get("state abbreviation")
    city = place.get("place name")
    return LocationPayload(
        latitude=latitude,
        longitude=longitude,
        city=city,
        state=state,
        country=country_name,
        country_code=country_code.upper(),
        postal_code=pincode,
        display_name=f"{city}, {state}, {country_name}",
        radius_km=settings.geo_default_radius_km,
    )


async def lookup(
    pincode: str,
    country_code: str,
    settings: Settings,
    redis: Redis,
    http_client: Any,
) -> LocationPayload | None:
    cleaned = _clean(pincode)
    if not cleaned:
        return None
    cc = country_code.upper()
    cache_key = f"{_CACHE_KEY}{cc}:{cleaned}"

    async def loader() -> LocationPayload | None:
        if cc == "IN":
            return await _india_lookup(cleaned, settings, http_client, redis)
        return await _zippopotam_lookup(cc, cleaned, settings, http_client)

    return await _cached(redis, cache_key, settings, loader)

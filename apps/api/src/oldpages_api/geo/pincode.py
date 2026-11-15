"""Pincode / ZIP lookup — India via postalpincode.in + OSM, elsewhere via OSM then Zippopotam.

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
from oldpages_api.geo import nominatim, places
from oldpages_api.geo.schemas import GeoSearchItem, LocationPayload

logger = logging.getLogger(__name__)

_CACHE_KEY = "geo:pincode:v3:"
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

    payload: LocationPayload | None = await loader()
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


_OFFICE_SUFFIX = re.compile(r"\s*(\([^)]*\)|\b[SBH]\.?\s?O\.?|\bG\.?P\.?O\.?)\s*$", re.IGNORECASE)
_OFFICE_RANK = {"Head Post Office": 0, "Sub Post Office": 1}


def _office_name(office: dict[str, Any]) -> str | None:
    name = str(office.get("Name") or "").strip()
    while True:
        cleaned = _OFFICE_SUFFIX.sub("", name).strip()
        if cleaned == name:
            return cleaned or None
        name = cleaned


async def _india_post_offices(
    pincode: str, settings: Settings, http_client: Any
) -> list[dict[str, Any]] | None:
    """Post offices for a PIN; [] when India Post says the PIN doesn't exist, None on outage."""
    try:
        response = await http_client.get(
            f"{_POSTALPIN_IN}/{pincode}",
            params={},
            headers={"Accept": "application/json", "User-Agent": settings.nominatim_user_agent},
            timeout=settings.nominatim_timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("postalpincode.in failed for %s: %s", pincode, exc)
        return None
    if not isinstance(body, list) or not body or not isinstance(body[0], dict):
        return None
    envelope = body[0]
    if envelope.get("Status") != "Success":
        return []
    return [o for o in envelope.get("PostOffice") or [] if isinstance(o, dict)]


async def _india_lookup(
    pincode: str, settings: Settings, http_client: Any, redis: Any
) -> LocationPayload | None:
    """India: India Post for names, the OSM postcode area for coordinates.

    India Post's "District" is an administrative district ("K.V.Rangareddy" for
    Gachibowli), and its centroid can sit 35 km from the PIN, which breaks the
    radius filter. The OSM postcode centroid is accurate to the neighbourhood.
    """
    if not re.fullmatch(r"[1-9]\d{5}", pincode):
        return None
    offices = await _india_post_offices(pincode, settings, http_client)
    if offices == []:
        return None  # not a real PIN
    point = await nominatim.postcode(pincode, "IN", settings, redis, http_client)

    offices = sorted(
        offices or [],
        key=lambda o: (
            _OFFICE_RANK.get(o.get("BranchType", ""), 2),
            o.get("DeliveryStatus") != "Delivery",
        ),
    )
    office = offices[0] if offices else {}
    district = office.get("District")
    state = places.canonical_state(office.get("State") or (point.state if point else None))
    if point is not None and office and not _agrees(point, state, district):
        point = None  # OSM has some postcodes mis-tagged (160017 sits in Punjab, not Chandigarh)

    if point is not None:
        latitude, longitude = point.latitude, point.longitude
    elif office:
        coords = await _geocode_office(office, state, settings, http_client, redis)
        if coords is None:
            return await _zippopotam_lookup("IN", pincode, settings, http_client)
        latitude, longitude = coords
    else:
        return await _zippopotam_lookup("IN", pincode, settings, http_client)

    near = places.nearest(latitude, longitude)
    city = (
        (point.city if point else None)
        or (near.name if near else None)
        or places.canonical_city(district, state)
    )
    # Head offices are named after their area ("Andheri"); other offices are often
    # buildings ("Sech Bhawan"), so they only name the area when OSM can't.
    head_office = office.get("BranchType") == "Head Post Office"
    if head_office:
        locality = _office_name(office)
    elif point is not None:
        locality = point.locality
    else:
        locality = _office_name(office)
    if locality and places.canonical_city(locality, state) == city:
        locality = None  # "Gurgaon, Gurugram" is one place
    country = "India"
    return LocationPayload(
        latitude=latitude,
        longitude=longitude,
        locality=locality,
        city=city,
        state=state,
        country=country,
        country_code="IN",
        postal_code=pincode,
        display_name=nominatim.label(locality, city, state, country),
        radius_km=settings.geo_default_radius_km,
    )


def _agrees(point: GeoSearchItem, state: str | None, district: str | None) -> bool:
    """Whether OSM's postcode point is plausibly where India Post says the PIN is."""
    if state and point.state and places.canonical_state(point.state) != state:
        return False
    district_place = places.find(district, state)
    if district_place is not None:
        km = places.distance_km(
            point.latitude, point.longitude, district_place.latitude, district_place.longitude
        )
        return km <= 80
    return True


async def _geocode_office(
    office: dict[str, Any],
    state: str | None,
    settings: Settings,
    http_client: Any,
    redis: Any,
) -> tuple[float, float] | None:
    """Coordinates for a PIN that OSM has no postcode area for: the office's area, then its city."""
    name = _office_name(office)
    district = office.get("District")
    if name:
        query = nominatim.label(name, district, state, "India")
        results = await nominatim.search(
            query, settings, redis, http_client, limit=1, country_codes="in"
        )
        if results:
            return results[0].latitude, results[0].longitude
    place = places.find(district, state)
    if place is not None:
        return place.latitude, place.longitude
    return None


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
    matches = body.get("places") or []
    if not matches:
        return None
    place = matches[0]
    try:
        latitude = float(place["latitude"])
        longitude = float(place["longitude"])
    except (KeyError, TypeError, ValueError):
        return None  # a location without coordinates can't drive the radius filter
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
        display_name=nominatim.label(city, state, country_name),
        radius_km=settings.geo_default_radius_km,
    )


async def _world_lookup(
    code: str, country_code: str, settings: Settings, http_client: Any, redis: Any
) -> LocationPayload | None:
    """OSM covers full postcodes ("SW1A 1AA", Singapore's 6 digits) that Zippopotam lacks."""
    point = await nominatim.postcode(code, country_code, settings, redis, http_client)
    if point is None:
        return await _zippopotam_lookup(country_code, _clean(code), settings, http_client)
    return LocationPayload(
        latitude=point.latitude,
        longitude=point.longitude,
        locality=point.locality,
        city=point.city,
        state=point.state,
        country=point.country,
        country_code=country_code,
        postal_code=code.upper(),
        display_name=point.display_name,
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
        return await _world_lookup(pincode.strip(), cc, settings, http_client, redis)

    return await _cached(redis, cache_key, settings, loader)

"""GeoLite2 (MaxMind) IP -> city lookup, with graceful fallback when the DB isn't installed."""

from __future__ import annotations

import ipaddress
import logging
from functools import lru_cache
from typing import Any

from oldpages_api.core.config import Settings
from oldpages_api.geo.schemas import LocationPayload

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _reader(mmdb_path: str) -> Any | None:
    try:
        import geoip2.database  # type: ignore[import-not-found]
    except ImportError:
        logger.info("geoip2 not installed; IP geolocation disabled")
        return None
    try:
        return geoip2.database.Reader(mmdb_path)
    except FileNotFoundError:
        logger.warning("GeoLite2 MMDB not found at %s; IP geolocation disabled", mmdb_path)
        return None


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)


def extract_client_ip(headers: dict[str, str] | Any, fallback: str | None) -> str | None:
    """Prefer the first public IP from X-Forwarded-For, else the direct client IP."""
    getter = headers.get if hasattr(headers, "get") else (lambda k: headers.get(k))  # type: ignore[union-attr]
    xff = getter("x-forwarded-for") or getter("X-Forwarded-For")
    if xff:
        for candidate in (piece.strip() for piece in xff.split(",")):
            if _is_public_ip(candidate):
                return candidate
    real_ip = getter("x-real-ip") or getter("X-Real-IP")
    if real_ip and _is_public_ip(real_ip):
        return real_ip
    if fallback and _is_public_ip(fallback):
        return fallback
    return None


def lookup(ip: str | None, settings: Settings) -> LocationPayload | None:
    if not ip or not settings.geoip_mmdb_path:
        return None
    reader = _reader(settings.geoip_mmdb_path)
    if reader is None:
        return None
    try:
        response = reader.city(ip)
    except Exception as exc:  # noqa: BLE001 - upstream lib defines many error types
        logger.debug("GeoLite2 lookup failed for %s: %s", ip, exc)
        return None

    location = response.location
    if location.latitude is None or location.longitude is None:
        return None
    return LocationPayload(
        latitude=float(location.latitude),
        longitude=float(location.longitude),
        city=response.city.name,
        state=(response.subdivisions.most_specific.name if response.subdivisions else None),
        country=response.country.name,
        country_code=response.country.iso_code,
        postal_code=response.postal.code if response.postal else None,
        radius_km=settings.geo_default_radius_km,
    )

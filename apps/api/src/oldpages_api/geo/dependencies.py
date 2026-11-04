"""FastAPI dependencies for the geo module."""

from __future__ import annotations

import base64
import json
import logging
from typing import Annotated, Any

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.core.config import Settings, get_settings
from oldpages_api.geo import http as geo_http
from oldpages_api.geo.schemas import LocationPayload
from oldpages_api.geo.service import GeoService
from oldpages_api.shared.cache.redis import get_redis
from oldpages_api.shared.db.database import get_session

logger = logging.getLogger(__name__)


def _decode_location_cookie(raw: str | None) -> LocationPayload | None:
    if not raw:
        return None
    try:
        padded = raw + "=" * (-len(raw) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        return LocationPayload(**payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to decode active-location cookie: %s", exc)
        return None


def encode_location_cookie(location: LocationPayload) -> str:
    raw = json.dumps(location.model_dump(exclude_none=True), separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def get_active_location(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    x_user_location: Annotated[str | None, Header(alias="X-User-Location")] = None,
) -> LocationPayload | None:
    """Read the session's active location from header (preferred) or cookie."""
    if x_user_location:
        payload = _decode_location_cookie(x_user_location)
        if payload is not None:
            return payload
    return _decode_location_cookie(request.cookies.get(settings.geo_active_cookie_name))


def get_geo_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GeoService:
    return GeoService(
        session=session,
        settings=settings,
        redis=get_redis(),
        http_client=geo_http.get_http_client(),
    )


ActiveLocationDep = Annotated[LocationPayload | None, Depends(get_active_location)]
GeoServiceDep = Annotated[GeoService, Depends(get_geo_service)]


def client_ip(request: Request) -> str | None:
    from oldpages_api.geo.ip import extract_client_ip

    fallback = request.client.host if request.client else None
    return extract_client_ip(dict(request.headers), fallback)


ClientIpDep = Annotated[str | None, Depends(client_ip)]

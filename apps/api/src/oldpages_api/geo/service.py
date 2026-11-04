from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oldpages_api.core.config import Settings
from oldpages_api.geo import ip as ip_lookup
from oldpages_api.geo import nominatim
from oldpages_api.geo import pincode as pincode_lookup
from oldpages_api.geo.schemas import (
    ActiveLocationResponse,
    DetectLocationResponse,
    GeoSearchResponse,
    LocationPayload,
    LocationSource,
)
from oldpages_api.identity.models import User, UserPreference

HOME_KEY = "home_location"


class GeoService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        redis: Any,
        http_client: Any,
    ) -> None:
        self.session = session
        self.settings = settings
        self.redis = redis
        self.http_client = http_client

    async def detect(self, client_ip: str | None) -> DetectLocationResponse:
        loc = ip_lookup.lookup(client_ip, self.settings)
        if loc is None:
            return DetectLocationResponse(location=None, source="unknown")
        return DetectLocationResponse(location=loc, source="ip")

    async def search(self, query: str, limit: int, country_codes: str | None) -> GeoSearchResponse:
        items = await nominatim.search(
            query,
            self.settings,
            self.redis,
            self.http_client,
            limit=limit,
            country_codes=country_codes,
        )
        return GeoSearchResponse(items=items)

    async def reverse(self, latitude: float, longitude: float) -> LocationPayload | None:
        return await nominatim.reverse(
            latitude, longitude, self.settings, self.redis, self.http_client
        )

    async def lookup_pincode(
        self, pincode: str, country_code: str
    ) -> LocationPayload | None:
        return await pincode_lookup.lookup(
            pincode, country_code, self.settings, self.redis, self.http_client
        )

    async def get_home(self, user: User) -> LocationPayload | None:
        prefs = await self._prefs(user)
        if prefs is None:
            return None
        raw = prefs.metadata_json.get(HOME_KEY) if isinstance(prefs.metadata_json, dict) else None
        if not raw:
            return None
        try:
            return LocationPayload(**raw)
        except Exception:  # noqa: BLE001
            return None

    async def set_home(self, user: User, location: LocationPayload) -> LocationPayload:
        prefs = await self._prefs(user)
        if prefs is None:
            prefs = UserPreference(user_id=user.id, metadata_json={})
            self.session.add(prefs)
            await self.session.flush()
        meta = dict(prefs.metadata_json) if isinstance(prefs.metadata_json, dict) else {}
        meta[HOME_KEY] = location.model_dump(exclude_none=True)
        prefs.metadata_json = meta
        await self.session.commit()
        return location

    async def active_response(
        self, user: User | None, active: LocationPayload | None
    ) -> ActiveLocationResponse:
        home = await self.get_home(user) if user is not None else None
        resolved = active or home
        source: LocationSource = "unknown"
        if active is not None:
            source = "manual"
        elif home is not None:
            source = "home"
        return ActiveLocationResponse(active=resolved, home=home, source=source)

    async def _prefs(self, user: User) -> UserPreference | None:
        result = await self.session.execute(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        return result.scalar_one_or_none()

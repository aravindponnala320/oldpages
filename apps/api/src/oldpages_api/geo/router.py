from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from oldpages_api.core.config import Settings, get_settings
from oldpages_api.geo.dependencies import (
    ActiveLocationDep,
    ClientIpDep,
    GeoServiceDep,
    encode_location_cookie,
)
from oldpages_api.geo.schemas import (
    ActiveLocationResponse,
    DetectLocationResponse,
    GeoSearchResponse,
    LocationPayload,
    SetActiveLocationRequest,
)
from oldpages_api.identity.dependencies import (
    CurrentPrincipal,
    get_current_principal,
    get_optional_principal,
)

geo_router = APIRouter(prefix="/geo", tags=["geo"])
me_location_router = APIRouter(prefix="/me/location", tags=["geo"])

PrincipalDep = Annotated[CurrentPrincipal, Depends(get_current_principal)]
OptionalPrincipalDep = Annotated[CurrentPrincipal | None, Depends(get_optional_principal)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@geo_router.get("/detect", response_model=DetectLocationResponse)
async def detect_location(
    service: GeoServiceDep,
    ip: ClientIpDep,
) -> DetectLocationResponse:
    return await service.detect(ip)


@geo_router.get("/search", response_model=GeoSearchResponse)
async def search_places(
    service: GeoServiceDep,
    q: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=8, ge=1, le=20),
    country_codes: str | None = Query(default=None, max_length=80, alias="cc"),
) -> GeoSearchResponse:
    return await service.search(q, limit, country_codes)


@geo_router.get("/reverse", response_model=LocationPayload | None)
async def reverse_geocode(
    service: GeoServiceDep,
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> LocationPayload | None:
    return await service.reverse(latitude, longitude)


@geo_router.get("/pincode/{pincode}", response_model=LocationPayload | None)
async def lookup_pincode(
    pincode: str,
    service: GeoServiceDep,
    country: str = Query(default="IN", min_length=2, max_length=2, alias="cc"),
) -> LocationPayload | None:
    return await service.lookup_pincode(pincode, country)


@me_location_router.get("", response_model=ActiveLocationResponse)
async def get_my_location(
    service: GeoServiceDep,
    principal: OptionalPrincipalDep,
    active: ActiveLocationDep,
) -> ActiveLocationResponse:
    user = principal.user if principal is not None else None
    return await service.active_response(user, active)


@me_location_router.put("/home", response_model=LocationPayload)
async def set_home_location(
    payload: LocationPayload,
    service: GeoServiceDep,
    principal: PrincipalDep,
) -> LocationPayload:
    return await service.set_home(principal.user, payload)


@me_location_router.put("/active", response_model=ActiveLocationResponse)
async def set_active_location(
    payload: SetActiveLocationRequest,
    response: Response,
    service: GeoServiceDep,
    principal: OptionalPrincipalDep,
    settings: SettingsDep,
) -> ActiveLocationResponse:
    cookie_value = encode_location_cookie(payload.location)
    response.set_cookie(
        key=settings.geo_active_cookie_name,
        value=cookie_value,
        max_age=settings.geo_active_cookie_max_age_days * 24 * 3600,
        httponly=False,  # frontend reads it to seed initial state
        samesite="lax",
        secure=settings.environment == "production",
        path="/",
    )
    user = principal.user if principal is not None else None
    if payload.persist_as_home and user is not None:
        await service.set_home(user, payload.location)
    active_resp = await service.active_response(user, payload.location)
    active_resp.source = "manual"
    return active_resp


@me_location_router.delete("/active", status_code=status.HTTP_204_NO_CONTENT)
async def clear_active_location(
    response: Response,
    settings: SettingsDep,
    _request: Request,
) -> Response:
    response.delete_cookie(settings.geo_active_cookie_name, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

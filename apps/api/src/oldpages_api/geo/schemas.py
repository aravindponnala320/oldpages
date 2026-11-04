from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LocationSource = Literal["browser", "ip", "manual", "home", "default", "unknown"]


class LocationPayload(BaseModel):
    """A resolved user location (either detected or manually selected)."""

    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    country_code: str | None = Field(default=None, max_length=2)
    postal_code: str | None = Field(default=None, max_length=20)
    display_name: str | None = Field(default=None, max_length=500)
    radius_km: float | None = Field(default=None, gt=0, le=500)

    @field_validator("country_code")
    @classmethod
    def upper_country_code(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class DetectLocationResponse(BaseModel):
    location: LocationPayload | None = None
    source: LocationSource = "unknown"


class SetActiveLocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location: LocationPayload
    persist_as_home: bool = False


class ActiveLocationResponse(BaseModel):
    active: LocationPayload | None = None
    home: LocationPayload | None = None
    source: LocationSource = "unknown"


class GeoSearchItem(BaseModel):
    display_name: str
    latitude: float
    longitude: float
    city: str | None = None
    state: str | None = None
    country: str | None = None
    country_code: str | None = None
    postal_code: str | None = None
    type: str | None = None


class GeoSearchResponse(BaseModel):
    items: list[GeoSearchItem]

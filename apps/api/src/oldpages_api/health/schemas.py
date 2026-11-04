from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class ComponentStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]
    detail: str | None = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    components: dict[str, ComponentStatus]
    environment: str
    service: str
    status: Literal["ok", "degraded"]
    version: str

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    request_id: str
    service: str
    version: str

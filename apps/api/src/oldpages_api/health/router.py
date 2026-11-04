from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from oldpages_api import __version__
from oldpages_api.health.schemas import ComponentStatus, HealthResponse
from oldpages_api.shared.cache.redis import check_redis
from oldpages_api.shared.db.database import check_database

router = APIRouter()


@router.get("/live", response_model=HealthResponse)
async def live(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        components={},
        environment=settings.environment,
        service="oldpages-api",
        status="ok",
        version=__version__,
    )


@router.get("/ready", response_model=HealthResponse)
async def ready(request: Request) -> JSONResponse | HealthResponse:
    settings = request.app.state.settings
    components: dict[str, ComponentStatus] = {}

    try:
        await check_database()
        components["database"] = ComponentStatus(status="ok")
    except Exception as exc:  # noqa: BLE001
        components["database"] = ComponentStatus(status="error", detail=str(exc))

    try:
        await check_redis()
        components["redis"] = ComponentStatus(status="ok")
    except Exception as exc:  # noqa: BLE001
        components["redis"] = ComponentStatus(status="error", detail=str(exc))

    response = HealthResponse(
        components=components,
        environment=settings.environment,
        service="oldpages-api",
        status="ok" if all(item.status == "ok" for item in components.values()) else "degraded",
        version=__version__,
    )

    if response.status != "ok":
        return JSONResponse(
            content=response.model_dump(mode="json"),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return response

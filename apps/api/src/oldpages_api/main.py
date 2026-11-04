from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from oldpages_api import __version__
from oldpages_api.api.router import api_router
from oldpages_api.chat.router import websocket_router
from oldpages_api.core.config import Settings, get_settings
from oldpages_api.core.exception_handlers import register_exception_handlers
from oldpages_api.core.middleware.request_id import RequestIdMiddleware
from oldpages_api.health.router import router as health_router
from oldpages_api.geo.http import close_http_client as close_geo_http
from oldpages_api.shared.cache.redis import close_redis
from oldpages_api.shared.db.database import dispose_database_engine
from oldpages_api.shared.observability.logging import configure_logging
from oldpages_api.shared.observability.tracing import configure_tracing

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = app_settings
        logger.info("api_starting", extra={"environment": app_settings.environment})
        yield
        await close_geo_http()
        await close_redis()
        await dispose_database_engine()
        logger.info("api_stopped")

    app = FastAPI(
        debug=app_settings.debug,
        description="OldPages.in modular monolith API foundation.",
        lifespan=lifespan,
        title=app_settings.app_name,
        version=__version__,
    )
    app.state.settings = app_settings

    app.add_middleware(RequestIdMiddleware, header_name=app_settings.request_id_header)
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_headers=["*"],
        allow_methods=["*"],
        allow_origins=app_settings.cors_origins,
    )

    register_exception_handlers(app)
    configure_tracing(app, app_settings)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(api_router, prefix=app_settings.api_v1_prefix)
    app.include_router(websocket_router)

    return app


app = create_app()

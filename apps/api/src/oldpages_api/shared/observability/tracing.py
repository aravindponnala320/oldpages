from __future__ import annotations

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from oldpages_api.core.config import Settings


def configure_tracing(app: FastAPI, settings: Settings) -> None:
    if settings.otel_enabled:
        FastAPIInstrumentor.instrument_app(app)

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from oldpages_api.core.errors import AppError
from oldpages_api.core.request_context import get_request_id

logger = logging.getLogger(__name__)


def problem_response(
    request: Request,
    *,
    detail: str,
    status_code: int,
    title: str,
    type_uri: str = "about:blank",
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "request_id": getattr(request.state, "request_id", get_request_id()),
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status_code, content=body)


def serializable_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        cleaned = dict(error)
        ctx = cleaned.get("ctx")
        if isinstance(ctx, dict):
            cleaned["ctx"] = {key: str(value) for key, value in ctx.items()}
        errors.append(cleaned)
    return errors


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return problem_response(
            request,
            detail=exc.detail,
            extra=exc.extra,
            status_code=exc.status_code,
            title=exc.title,
            type_uri=exc.type_uri,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = str(exc.detail) if exc.detail else "HTTP error"
        return problem_response(
            request,
            detail=detail,
            status_code=exc.status_code,
            title=detail,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return problem_response(
            request,
            detail="Request validation failed.",
            extra={"invalid_params": serializable_validation_errors(exc)},
            status_code=422,
            title="Unprocessable Entity",
            type_uri="https://oldpages.in/problems/validation-error",
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", extra={"path": request.url.path})
        return problem_response(
            request,
            detail="An unexpected error occurred.",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            type_uri="https://oldpages.in/problems/internal-server-error",
        )

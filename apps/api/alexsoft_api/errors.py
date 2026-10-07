"""RFC 9457 problem+json errors (contract: components.schemas.Problem)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_MEDIA_TYPE = "application/problem+json"
log = logging.getLogger("alexsoft_api")

_TITLES = {
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not found",
    409: "Conflict",
    422: "Validation error",
    429: "Daily quota exceeded",
    502: "Upstream unavailable",
    503: "Service unavailable",
}


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        detail: str | None = None,
        *,
        title: str | None = None,
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail or str(status))
        self.status = status
        self.detail = detail
        self.title = title or _TITLES.get(status, "Error")
        self.headers = headers or {}
        self.extra = extra or {}


def unauthorized(detail: str = "Missing or invalid token") -> ApiError:
    return ApiError(401, detail, headers={"WWW-Authenticate": "Bearer"})


def forbidden(detail: str = "Insufficient permissions") -> ApiError:
    return ApiError(403, detail)


def not_found(what: str) -> ApiError:
    return ApiError(404, f"{what} not found")


def _problem(request: Request, err: ApiError) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": err.title,
        "status": err.status,
        "detail": err.detail,
        "request_id": getattr(request.state, "request_id", None),
        **err.extra,
    }
    body = {k: v for k, v in body.items() if v is not None}
    return JSONResponse(body, status_code=err.status, media_type=PROBLEM_MEDIA_TYPE, headers=err.headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _problem(request, exc)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(p) for p in e.get("loc", []) if p != "body"), "message": str(e.get("msg", "invalid"))}
            for e in exc.errors()
        ]
        return _problem(request, ApiError(422, "Request validation failed", extra={"errors": errors}))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(request, ApiError(exc.status_code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error: %s", exc)
        return _problem(request, ApiError(500, "Unexpected server error", title="Internal error"))

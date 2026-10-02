"""RFC 9457 problem+json errors (contract: components.schemas.Problem)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_MEDIA_TYPE = "application/problem+json"

_TITLES = {
    "validation_error": "Validation error",
    "not_found": "Not found",
    "already_exists": "Already exists",
    "payload_too_large": "Payload too large",
    "guardrail_blocked": "Blocked by guardrails",
    "embedding_unavailable": "Embedding service unavailable",
    "vector_store_unavailable": "Vector store unavailable",
    "object_store_unavailable": "Object store unavailable",
    "llm_unavailable": "LLM unavailable",
    "internal_error": "Internal error",
    "unauthorized": "Unauthorized",
}


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        detail: str | None = None,
        *,
        title: str | None = None,
        errors: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(detail or code)
        self.status = status
        self.code = code
        self.detail = detail
        self.title = title or _TITLES.get(code, code)
        self.errors = errors


def not_found(what: str) -> ApiError:
    return ApiError(404, "not_found", f"{what} not found")


def upstream(code: str, detail: str) -> ApiError:
    status = 503 if code == "vector_store_unavailable" else 502
    return ApiError(status, code, detail)


def _problem(request: Request, err: ApiError) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": err.title,
        "status": err.status,
        "code": err.code,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", None),
    }
    if err.detail:
        body["detail"] = err.detail
    if err.errors:
        body["errors"] = err.errors
    body = {k: v for k, v in body.items() if v is not None}
    headers = {}
    if err.status == 401:
        headers["WWW-Authenticate"] = "ApiKey"
    return JSONResponse(body, status_code=err.status, media_type=PROBLEM_MEDIA_TYPE, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return _problem(request, exc)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(p) for p in e.get("loc", []) if p != "body"),
                "message": str(e.get("msg", "invalid")),
            }
            for e in exc.errors()
        ]
        return _problem(
            request,
            ApiError(422, "validation_error", "Request validation failed", errors=errors),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {401: "unauthorized", 404: "not_found"}.get(exc.status_code, "internal_error")
        return _problem(request, ApiError(exc.status_code, code, str(exc.detail)))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        import logging

        logging.getLogger("alexsoft_rag").exception("unhandled error: %s", exc)
        return _problem(request, ApiError(500, "internal_error", "Unexpected server error"))

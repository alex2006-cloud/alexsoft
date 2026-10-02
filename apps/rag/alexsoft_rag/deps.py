"""FastAPI dependencies: service container access and X-API-Key auth (stage 5)."""

from __future__ import annotations

import secrets

from fastapi import Header, Request

from .errors import ApiError
from .services import Services


def get_services(request: Request) -> Services:
    return request.app.state.services


async def require_api_key(
    request: Request, x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> None:
    expected = request.app.state.services.settings.rag_api_key
    # Fail closed: an empty RAG_API_KEY must never mean "open".
    if not expected or not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise ApiError(401, "unauthorized", "Missing or invalid X-API-Key")

"""Authentik admin API client: list / (de)activate users. Used only by the admin endpoints."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .errors import ApiError, not_found

log = logging.getLogger("alexsoft_api")


class AuthentikClient:
    def __init__(self, api_url: str, token: str, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=api_url, timeout=8.0, trust_env=False, transport=transport,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        self._has_token = bool(token)

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _user(u: dict[str, Any]) -> dict[str, Any]:
        groups = u.get("groups_obj") or []
        return {
            "id": u["pk"],
            "username": u.get("username", ""),
            "email": u.get("email", ""),
            "name": u.get("name", ""),
            "is_active": bool(u.get("is_active", True)),
            "groups": [g.get("name", "") for g in groups if isinstance(g, dict)],
            "date_joined": u.get("date_joined"),
            "last_login": u.get("last_login"),
        }

    async def _call(self, method: str, path: str, **kw: Any) -> httpx.Response:
        if not self._has_token:
            raise ApiError(502, "AUTHENTIK_BL_TOKEN is not configured")
        try:
            r = await self._client.request(method, path, **kw)
        except httpx.HTTPError as e:
            log.error("authentik unreachable: %s", e)
            raise ApiError(502, "Identity provider is unavailable") from e
        if r.status_code == 404:
            raise not_found("User")
        if r.status_code >= 400:
            log.error("authentik %s %s -> %s %s", method, path, r.status_code, r.text[:200])
            raise ApiError(502, "Identity provider rejected the request")
        return r

    async def list_users(self, *, limit: int, offset: int, search: str | None) -> tuple[list[dict], int]:
        params: dict[str, Any] = {
            "page_size": limit, "page": offset // limit + 1, "ordering": "username", "type": "internal",
            "include_groups": "true",
        }
        if search:
            params["search"] = search
        data = (await self._call("GET", "/core/users/", params=params)).json()
        total = int(data.get("pagination", {}).get("count", 0))
        return [self._user(u) for u in data.get("results", [])], total

    async def get_user_uuid(self, user_id: int) -> str:
        data = (await self._call("GET", f"/core/users/{user_id}/")).json()
        return str(data.get("uid") or data.get("uuid") or "")

    async def set_active(self, user_id: int, active: bool) -> dict:
        r = await self._call("PATCH", f"/core/users/{user_id}/", json={"is_active": active})
        return self._user(r.json())

    async def ping(self) -> bool:
        try:
            r = await self._client.get("/root/config/")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

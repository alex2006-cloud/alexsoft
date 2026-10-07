"""JWT validation against the Authentik JWKS, roles from the `groups` claim (ADR-0019).

Nginx does not validate JWT; this module is the authority.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx
import jwt
from fastapi import Depends, Request
from jwt.algorithms import RSAAlgorithm

from .config import Settings
from .errors import forbidden, unauthorized

log = logging.getLogger("alexsoft_api")

ALLOWED_ALGS = ["RS256", "RS384", "RS512", "ES256"]


class KeySource(Protocol):
    async def get_key(self, kid: str | None) -> Any: ...


class JwksKeySource:
    """Fetches the JWKS with httpx (no system proxy) and caches keys; refetches on unknown `kid`."""

    def __init__(self, url: str, *, ttl_s: float = 600.0, min_refetch_s: float = 10.0,
                 transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._url = url
        self._ttl = ttl_s
        self._min_refetch = min_refetch_s
        self._keys: dict[str, Any] = {}
        self._fetched_at = 0.0
        self._lock = asyncio.Lock()
        self._client = httpx.AsyncClient(timeout=5.0, trust_env=False, transport=transport)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _refresh(self) -> None:
        r = await self._client.get(self._url)
        r.raise_for_status()
        keys: dict[str, Any] = {}
        for jwk in r.json().get("keys", []):
            if jwk.get("use", "sig") != "sig":
                continue
            kty = jwk.get("kty")
            try:
                if kty == "RSA":
                    keys[jwk.get("kid", "")] = RSAAlgorithm.from_jwk(json.dumps(jwk))
                elif kty == "EC":
                    from jwt.algorithms import ECAlgorithm

                    keys[jwk.get("kid", "")] = ECAlgorithm.from_jwk(json.dumps(jwk))
            except Exception as e:  # skip a malformed key, keep the rest
                log.warning("skipping JWK kid=%s: %s", jwk.get("kid"), e)
        self._keys = keys
        self._fetched_at = time.monotonic()

    async def get_key(self, kid: str | None) -> Any:
        async with self._lock:
            age = time.monotonic() - self._fetched_at
            stale = (not self._keys) or age > self._ttl
            if stale:
                await self._refresh()
            key = self._keys.get(kid or "")
            if key is None and not stale and age > self._min_refetch:
                await self._refresh()  # key rotation
                key = self._keys.get(kid or "")
            if key is None and kid is None and len(self._keys) == 1:
                key = next(iter(self._keys.values()))
            return key

    async def ping(self) -> bool:
        try:
            async with self._lock:
                await self._refresh()
            return bool(self._keys)
        except Exception:
            return False


@dataclass
class Principal:
    sub: str
    username: str = ""
    email: str = ""
    name: str = ""
    groups: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def is_user(self) -> bool:
        return "user" in self.roles


def roles_from_groups(groups: list[str], settings: Settings) -> list[str]:
    roles: list[str] = []
    if settings.bl_group_admin in groups:
        roles = ["user", "admin"]  # admin includes user
    elif settings.bl_group_user in groups:
        roles = ["user"]
    return roles


class TokenVerifier:
    def __init__(self, settings: Settings, keys: KeySource) -> None:
        self._s = settings
        self._keys = keys

    async def verify(self, token: str) -> Principal:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            raise unauthorized("Malformed token") from None
        if header.get("alg") not in ALLOWED_ALGS:
            raise unauthorized("Unsupported token algorithm")
        try:
            key = await self._keys.get_key(header.get("kid"))
        except Exception as e:
            log.error("JWKS fetch failed: %s", e)
            raise unauthorized("Cannot verify token: identity provider unavailable") from None
        if key is None:
            raise unauthorized("Unknown signing key")
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=ALLOWED_ALGS,
                audience=self._s.oidc_client_id,
                issuer=self._s.issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
                leeway=10,
            )
        except jwt.ExpiredSignatureError:
            raise unauthorized("Token expired") from None
        except jwt.PyJWTError as e:
            log.info("token rejected: %s", e)
            raise unauthorized("Invalid token") from None

        raw_groups = claims.get("groups") or []
        groups = [str(g) for g in raw_groups] if isinstance(raw_groups, list) else []
        return Principal(
            sub=str(claims["sub"]),
            username=str(claims.get("preferred_username") or claims.get("nickname") or ""),
            email=str(claims.get("email") or ""),
            name=str(claims.get("name") or ""),
            groups=groups,
            roles=roles_from_groups(groups, self._s),
        )


def _bearer(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise unauthorized()
    return token.strip()


async def get_principal(request: Request) -> Principal:
    verifier: TokenVerifier = request.app.state.services.verifier
    principal = await verifier.verify(_bearer(request))
    request.state.principal = principal
    return principal


async def require_user(principal: Principal = Depends(get_principal)) -> Principal:
    if not principal.is_user:
        raise forbidden("User is not in a group with access (alexsoft-users)")
    return principal


async def require_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if not principal.is_admin:
        raise forbidden("Administrator role required")
    return principal

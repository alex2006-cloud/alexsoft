"""Service container wired once at startup (and replaced by fakes in tests)."""

from __future__ import annotations

from dataclasses import dataclass

from .agents import build_runners
from .auth import JwksKeySource, TokenVerifier
from .authentik import AuthentikClient
from .config import Settings
from .runs import RunService
from .store import Store
from .store.postgres import PgStore


@dataclass
class Services:
    settings: Settings
    store: Store
    verifier: TokenVerifier
    runs: RunService
    authentik: AuthentikClient
    keys: JwksKeySource | None = None


def build_services(settings: Settings) -> Services:
    store = PgStore(settings.database_dsn)
    keys = JwksKeySource(settings.jwks_url)
    return Services(
        settings=settings,
        store=store,
        verifier=TokenVerifier(settings, keys),
        runs=RunService(settings, store, build_runners(settings)),
        authentik=AuthentikClient(settings.authentik_api_url, settings.authentik_bl_token),
        keys=keys,
    )

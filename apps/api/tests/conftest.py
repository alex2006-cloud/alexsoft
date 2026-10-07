"""Test helpers: signed JWTs (RS256, in-process key), in-memory store, fake runners. No network, no Postgres."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from alexsoft_api.agents import AgentError, EchoRunner, Message, Meta, RunRequest, Step, seed_agents
from alexsoft_api.auth import TokenVerifier
from alexsoft_api.authentik import AuthentikClient
from alexsoft_api.config import Settings
from alexsoft_api.main import create_app
from alexsoft_api.runs import RunService
from alexsoft_api.services import Services
from alexsoft_api.store import MemoryStore

ISSUER = "http://auth.test/application/o/alexsoft-cabinet/"
CLIENT_ID = "alexsoft-cabinet"
KID = "test-key"


@pytest.fixture(scope="session")
def private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def other_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class StaticKeys:
    def __init__(self, key) -> None:
        self._pub = key.public_key()

    async def get_key(self, kid):
        return self._pub if kid == KID else None


class BoomRunner:
    async def run(self, req: RunRequest) -> AsyncIterator:
        yield Step("start")
        raise AgentError("Агент временно недоступен")


class SlowRunner:
    async def run(self, req: RunRequest) -> AsyncIterator:
        import asyncio

        await asyncio.sleep(5)
        yield Message("never")


class FixedRunner:
    """Pretends to be the langgraph runner: thread + trace + answer."""

    async def run(self, req: RunRequest) -> AsyncIterator:
        yield Meta(thread_id=req.thread_id or "t-1", trace_id="trace-xyz")
        yield Step("tool:calculator", "expression=2+2")
        yield Message("4")


def make_settings(**kw) -> Settings:
    base = dict(
        auth_public_url="http://auth.test", oidc_app_slug="alexsoft-cabinet", oidc_client_id=CLIENT_ID,
        bl_oidc_issuer=ISSUER, bl_daily_run_quota=3, bl_run_timeout_s=2.0, authentik_bl_token="tok",
        _env_file=None,
    )
    base.update(kw)
    return Settings(**base)


@pytest.fixture
def make_token(private_key):
    def _make(*, sub="u-1", groups=("alexsoft-users",), username="alice", exp_in=300, aud=CLIENT_ID,
              iss=ISSUER, key=None, kid=KID, **extra) -> str:
        now = int(time.time())
        claims = {"sub": sub, "iss": iss, "aud": aud, "iat": now, "exp": now + exp_in,
                  "preferred_username": username, "email": f"{username}@example.com", "name": username.title(),
                  "groups": list(groups), **extra}
        return jwt.encode(claims, key or private_key, algorithm="RS256", headers={"kid": kid})
    return _make


@pytest.fixture
def authentik_calls():
    return []


@pytest.fixture
async def services(private_key, authentik_calls) -> Services:
    settings = make_settings()
    store = MemoryStore()
    await store.seed_agents(seed_agents(settings))

    def handler(request: httpx.Request) -> httpx.Response:
        authentik_calls.append((request.method, request.url.path, request.url.query.decode()))
        if request.method == "GET" and request.url.path.endswith("/core/users/"):
            return httpx.Response(200, json={
                "pagination": {"count": 1},
                "results": [{"pk": 7, "username": "alice", "name": "Alice", "email": "a@x.io", "is_active": True,
                             "groups_obj": [{"name": "alexsoft-users"}], "last_login": None, "date_joined": None}],
            })
        if request.method == "GET" and request.url.path.endswith("/core/users/9/"):
            return httpx.Response(200, json={"pk": 9, "uid": "admin-1", "username": "root"})
        if request.method == "GET" and request.url.path.endswith("/core/users/7/"):
            return httpx.Response(200, json={"pk": 7, "uid": "u-alice", "username": "alice"})
        if request.method == "PATCH":
            return httpx.Response(200, json={"pk": 7, "username": "alice", "is_active": False, "groups_obj": []})
        return httpx.Response(404)

    runners = {"echo": EchoRunner(delay_s=0.01), "langgraph": FixedRunner()}
    return Services(
        settings=settings,
        store=store,
        verifier=TokenVerifier(settings, StaticKeys(private_key)),
        runs=RunService(settings, store, runners),
        authentik=AuthentikClient("http://authentik.test/api/v3", "tok", transport=httpx.MockTransport(handler)),
    )


@pytest.fixture
async def client(services: Services):
    app = create_app(services)
    app.state.services = services  # lifespan is not run by ASGITransport
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://bl.test") as c:
        yield c
    await services.runs.shutdown()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

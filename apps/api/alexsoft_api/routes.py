"""HTTP routes. Contract: artifacts/api/bl.openapi.yaml."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from .auth import Principal, get_principal, require_admin, require_user
from .errors import ApiError, forbidden, not_found
from .runs import day_start, utcnow
from .schemas import (
    Agent, AgentList, AgentUpdate, BlSettings, Health, Me, Run, RunCreate, RunPage, Stats, User, UserPage, UserUpdate,
)
from .services import Services

router = APIRouter()
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]


def svc(request: Request) -> Services:
    return request.app.state.services


def _agent(row: dict) -> Agent:
    return Agent.model_validate(row)


# ---------------------------------------------------------------- health
@router.get("/health/live", response_model=Health, tags=["Health"])
async def live() -> Health:
    return Health(status="ok")


@router.get("/health/ready", response_model=Health, tags=["Health"])
async def ready(request: Request) -> JSONResponse:
    s = svc(request)
    checks = {
        "postgres": "ok" if await s.store.ping() else "down",
        "jwks": "ok" if s.keys and await s.keys.ping() else "down",
    }
    ok = all(v == "ok" for v in checks.values())
    body = Health(status="ok" if ok else "degraded", checks=checks)
    return JSONResponse(body.model_dump(), status_code=200 if ok else 503)


# ---------------------------------------------------------------- me / agents
@router.get("/v1/me", response_model=Me, tags=["Me"])
async def get_me(request: Request, p: Principal = Depends(require_user)) -> Me:
    return Me(
        sub=p.sub, username=p.username, email=p.email, name=p.name, roles=p.roles, groups=p.groups,
        quota=await svc(request).runs.quota(p.sub),
    )


@router.get("/v1/agents", response_model=AgentList, tags=["Agents"])
async def list_agents(request: Request, _: Principal = Depends(require_user)) -> AgentList:
    rows = await svc(request).store.list_agents(only_enabled=True)
    return AgentList(items=[_agent(r) for r in rows])


# ---------------------------------------------------------------- runs
@router.post("/v1/agents/{agent_id}/runs", response_model=Run, status_code=202, tags=["Runs"])
async def create_run(agent_id: str, body: RunCreate, request: Request, response: Response,
                     p: Principal = Depends(require_user)) -> Run:
    run, remaining = await svc(request).runs.create(p, agent_id, body.input, body.thread_id)
    response.headers["X-Quota-Remaining"] = str(remaining)
    return Run.model_validate(run)


@router.get("/v1/runs", response_model=RunPage, tags=["Runs"])
async def list_runs(request: Request, limit: Limit = 50, offset: Offset = 0, agent_id: str | None = None,
                    p: Principal = Depends(require_user)) -> RunPage:
    items, total = await svc(request).store.list_runs(user_sub=p.sub, agent_id=agent_id, limit=limit, offset=offset)
    return RunPage(items=[Run.model_validate(r) for r in items], total=total)


async def _own_run(request: Request, run_id: UUID, p: Principal) -> dict:
    run = await svc(request).store.get_run(run_id)
    if run is None or (run["user_sub"] != p.sub and not p.is_admin):
        raise not_found("Run")  # do not reveal foreign runs
    return run


@router.get("/v1/runs/{run_id}", response_model=Run, tags=["Runs"])
async def get_run(run_id: UUID, request: Request, p: Principal = Depends(require_user)) -> Run:
    return Run.model_validate(await _own_run(request, run_id, p))


@router.get("/v1/runs/{run_id}/events", tags=["Runs"])
async def run_events(run_id: UUID, request: Request, p: Principal = Depends(require_user),
                     last_event_id: Annotated[int | None, Header(alias="Last-Event-ID")] = None) -> StreamingResponse:
    await _own_run(request, run_id, p)
    gen = svc(request).runs.stream(run_id, after_seq=last_event_id or 0)
    return StreamingResponse(
        gen, media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------- admin
@router.get("/v1/admin/users", response_model=UserPage, tags=["Admin"])
async def admin_users(request: Request, limit: Limit = 50, offset: Offset = 0, search: str | None = None,
                      _: Principal = Depends(require_admin)) -> UserPage:
    items, total = await svc(request).authentik.list_users(limit=limit, offset=offset, search=search)
    return UserPage(items=[User.model_validate(u) for u in items], total=total)


@router.patch("/v1/admin/users/{user_id}", response_model=User, tags=["Admin"])
async def admin_update_user(user_id: int, body: UserUpdate, request: Request,
                            p: Principal = Depends(require_admin)) -> User:
    a = svc(request).authentik
    if not body.is_active and await a.get_user_uuid(user_id) == p.sub:
        raise ApiError(409, "Нельзя деактивировать самого себя")
    return User.model_validate(await a.set_active(user_id, body.is_active))


@router.get("/v1/admin/runs", response_model=RunPage, tags=["Admin"])
async def admin_runs(request: Request, limit: Limit = 50, offset: Offset = 0, user_sub: str | None = None,
                     agent_id: str | None = None, status: str | None = None,
                     _: Principal = Depends(require_admin)) -> RunPage:
    if status not in (None, "queued", "running", "succeeded", "failed"):
        raise ApiError(422, "Unknown status")
    items, total = await svc(request).store.list_runs(
        user_sub=user_sub, agent_id=agent_id, status=status, limit=limit, offset=offset)
    return RunPage(items=[Run.model_validate(r) for r in items], total=total)


@router.get("/v1/admin/stats", response_model=Stats, tags=["Admin"])
async def admin_stats(request: Request, _: Principal = Depends(require_admin)) -> Stats:
    return Stats.model_validate(await svc(request).store.stats(day_start(utcnow())))


@router.get("/v1/admin/agents", response_model=AgentList, tags=["Admin"])
async def admin_agents(request: Request, _: Principal = Depends(require_admin)) -> AgentList:
    rows = await svc(request).store.list_agents(only_enabled=False)
    return AgentList(items=[_agent(r) for r in rows])


@router.patch("/v1/admin/agents/{agent_id}", response_model=Agent, tags=["Admin"])
async def admin_update_agent(agent_id: str, body: AgentUpdate, request: Request,
                             _: Principal = Depends(require_admin)) -> Agent:
    patch = body.model_dump(exclude_none=True)
    if not patch:
        raise ApiError(422, "Nothing to update")
    row = await svc(request).store.update_agent(agent_id, patch)
    if row is None:
        raise not_found("Agent")
    return _agent(row)


@router.get("/v1/admin/settings", response_model=BlSettings, tags=["Admin"])
async def admin_get_settings(request: Request, _: Principal = Depends(require_admin)) -> BlSettings:
    return BlSettings(daily_run_quota=await svc(request).runs.daily_limit())


@router.put("/v1/admin/settings", response_model=BlSettings, tags=["Admin"])
async def admin_put_settings(body: BlSettings, request: Request, _: Principal = Depends(require_admin)) -> BlSettings:
    await svc(request).runs.set_daily_limit(body.daily_run_quota)
    return body

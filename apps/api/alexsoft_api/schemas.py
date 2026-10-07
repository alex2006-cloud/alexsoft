"""Pydantic models; they mirror artifacts/api/bl.openapi.yaml."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

RunStatus = Literal["queued", "running", "succeeded", "failed"]
AgentKind = Literal["echo", "langgraph"]


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, str] = {}


class Quota(BaseModel):
    daily_limit: int
    used_today: int
    remaining: int
    resets_at: datetime


class Me(BaseModel):
    sub: str
    username: str = ""
    email: str = ""
    name: str = ""
    roles: list[str]
    groups: list[str]
    quota: Quota


class Agent(BaseModel):
    id: str
    title: str
    description: str
    kind: AgentKind
    enabled: bool
    input_hint: str | None = None


class AgentList(BaseModel):
    items: list[Agent]


class AgentUpdate(BaseModel):
    enabled: bool | None = None
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class RunCreate(BaseModel):
    input: str = Field(min_length=1)
    thread_id: str | None = Field(default=None, max_length=200)


class Run(BaseModel):
    id: UUID
    agent_id: str
    user_sub: str
    username: str | None = None
    status: RunStatus
    input: str
    output: str | None = None
    error: str | None = None
    thread_id: str | None = None
    trace_id: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RunPage(BaseModel):
    items: list[Run]
    total: int


class User(BaseModel):
    id: int
    username: str
    email: str = ""
    name: str = ""
    is_active: bool
    groups: list[str] = []
    date_joined: datetime | None = None
    last_login: datetime | None = None


class UserPage(BaseModel):
    items: list[User]
    total: int


class UserUpdate(BaseModel):
    is_active: bool


class AgentRuns(BaseModel):
    agent_id: str
    runs: int


class Stats(BaseModel):
    runs_total: int
    runs_today: int
    failed_today: int = 0
    active_users_today: int
    by_agent: list[AgentRuns]


class BlSettings(BaseModel):
    daily_run_quota: int = Field(ge=0, le=10000)


def jsonable(data: dict[str, Any]) -> dict[str, Any]:
    """Run -> plain dict for SSE `done` events."""
    return Run.model_validate(data).model_dump(mode="json")

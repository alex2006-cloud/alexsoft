"""In-memory Store for tests and offline development."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


class MemoryStore:
    def __init__(self) -> None:
        self._agents: dict[str, dict[str, Any]] = {}
        self._runs: dict[UUID, dict[str, Any]] = {}
        self._events: dict[UUID, list[dict[str, Any]]] = {}
        self._settings: dict[str, Any] = {}

    async def connect(self) -> None: ...
    async def close(self) -> None: ...
    async def ping(self) -> bool:
        return True

    # agents
    async def seed_agents(self, agents: list[dict[str, Any]]) -> None:
        for a in agents:
            self._agents.setdefault(a["id"], copy.deepcopy(a))

    async def list_agents(self, *, only_enabled: bool) -> list[dict[str, Any]]:
        rows = sorted(self._agents.values(), key=lambda a: (a.get("sort", 100), a["id"]))
        return [copy.deepcopy(a) for a in rows if a["enabled"] or not only_enabled]

    async def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        a = self._agents.get(agent_id)
        return copy.deepcopy(a) if a else None

    async def update_agent(self, agent_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        a = self._agents.get(agent_id)
        if not a:
            return None
        a.update({k: v for k, v in patch.items() if v is not None})
        return copy.deepcopy(a)

    # runs
    async def create_run(self, run: dict[str, Any]) -> dict[str, Any]:
        self._runs[run["id"]] = copy.deepcopy(run)
        self._events[run["id"]] = []
        return copy.deepcopy(run)

    async def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        r = self._runs.get(run_id)
        return copy.deepcopy(r) if r else None

    async def update_run(self, run_id: UUID, **fields: Any) -> dict[str, Any] | None:
        r = self._runs.get(run_id)
        if not r:
            return None
        r.update(fields)
        return copy.deepcopy(r)

    async def list_runs(self, *, user_sub=None, agent_id=None, status=None, limit=50, offset=0):
        rows = [
            r
            for r in self._runs.values()
            if (user_sub is None or r["user_sub"] == user_sub)
            and (agent_id is None or r["agent_id"] == agent_id)
            and (status is None or r["status"] == status)
        ]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return [copy.deepcopy(r) for r in rows[offset : offset + limit]], len(rows)

    async def count_runs_since(self, user_sub: str, since: datetime) -> int:
        return sum(1 for r in self._runs.values() if r["user_sub"] == user_sub and r["created_at"] >= since)

    async def thread_belongs_to(self, user_sub: str, agent_id: str, thread_id: str) -> bool:
        return any(
            r["user_sub"] == user_sub and r["agent_id"] == agent_id and r.get("thread_id") == thread_id
            for r in self._runs.values()
        )

    async def fail_stale_runs(self) -> int:
        n = 0
        for r in self._runs.values():
            if r["status"] in ("queued", "running"):
                r.update(status="failed", error="Service restarted", finished_at=datetime.now(timezone.utc))
                n += 1
        return n

    # events
    async def append_event(self, run_id: UUID, type_: str, data: dict[str, Any]) -> int:
        events = self._events.setdefault(run_id, [])
        seq = len(events) + 1
        events.append({"seq": seq, "type": type_, "data": copy.deepcopy(data)})
        return seq

    async def list_events(self, run_id: UUID, after_seq: int = 0) -> list[dict[str, Any]]:
        return [copy.deepcopy(e) for e in self._events.get(run_id, []) if e["seq"] > after_seq]

    # admin
    async def stats(self, since: datetime) -> dict[str, Any]:
        today = [r for r in self._runs.values() if r["created_at"] >= since]
        by_agent: dict[str, int] = {}
        for r in self._runs.values():
            by_agent[r["agent_id"]] = by_agent.get(r["agent_id"], 0) + 1
        return {
            "runs_total": len(self._runs),
            "runs_today": len(today),
            "failed_today": sum(1 for r in today if r["status"] == "failed"),
            "active_users_today": len({r["user_sub"] for r in today}),
            "by_agent": [{"agent_id": k, "runs": v} for k, v in sorted(by_agent.items())],
        }

    async def get_setting(self, key: str) -> Any | None:
        return self._settings.get(key)

    async def put_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value

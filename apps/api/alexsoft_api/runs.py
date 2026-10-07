"""Run lifecycle: quota check, creation, background execution, event streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from .agents import AgentError, AgentRunner, Message, Meta, RunRequest, Step
from .auth import Principal
from .config import Settings
from .errors import ApiError, not_found
from .schemas import jsonable
from .store import Store

log = logging.getLogger("alexsoft_api")

QUOTA_SETTING = "daily_run_quota"
TERMINAL = ("done", "error")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def day_start(now: datetime | None = None) -> datetime:
    n = now or utcnow()
    return datetime.combine(n.date(), time.min, tzinfo=timezone.utc)


class RunService:
    def __init__(self, settings: Settings, store: Store, runners: dict[str, AgentRunner]) -> None:
        self._s = settings
        self._store = store
        self._runners = runners
        self._tasks: set[asyncio.Task] = set()
        self._quota_lock = asyncio.Lock()

    # ------------------------------------------------------------ quota
    async def daily_limit(self) -> int:
        v = await self._store.get_setting(QUOTA_SETTING)
        return int(v) if v is not None else self._s.bl_daily_run_quota

    async def set_daily_limit(self, value: int) -> None:
        await self._store.put_setting(QUOTA_SETTING, int(value))

    async def quota(self, user_sub: str) -> dict[str, Any]:
        now = utcnow()
        limit = await self.daily_limit()
        used = await self._store.count_runs_since(user_sub, day_start(now))
        return {
            "daily_limit": limit,
            "used_today": used,
            "remaining": max(0, limit - used),
            "resets_at": day_start(now) + timedelta(days=1),
        }

    # ------------------------------------------------------------ create
    async def create(self, principal: Principal, agent_id: str, text: str, thread_id: str | None) -> tuple[dict, int]:
        text = text.strip()
        if not text:
            raise ApiError(422, "Input is empty")
        if len(text) > self._s.bl_max_input_chars:
            raise ApiError(422, f"Input is longer than {self._s.bl_max_input_chars} characters")
        agent = await self._store.get_agent(agent_id)
        if not agent or not agent["enabled"]:
            raise not_found("Agent")
        if agent["kind"] not in self._runners:
            raise ApiError(503, "Agent kind is not supported by this deployment")
        if thread_id and not await self._store.thread_belongs_to(principal.sub, agent_id, thread_id):
            raise ApiError(422, "Unknown thread_id for this agent")

        async with self._quota_lock:  # check + insert must not interleave (single process)
            q = await self.quota(principal.sub)
            if q["remaining"] <= 0:
                retry = max(1, int((q["resets_at"] - utcnow()).total_seconds()))
                raise ApiError(
                    429,
                    f"Дневная квота запусков исчерпана ({q['daily_limit']}). Сброс в 00:00 UTC.",
                    headers={"Retry-After": str(retry)},
                    extra={"quota": {"daily_limit": q["daily_limit"], "used_today": q["used_today"]}},
                )
            run = await self._store.create_run({
                "id": uuid4(),
                "agent_id": agent_id,
                "user_sub": principal.sub,
                "username": principal.username or None,
                "status": "queued",
                "input": text,
                "thread_id": thread_id,
                "created_at": utcnow(),
            })
        task = asyncio.create_task(self._execute(run, agent), name=f"run-{run['id']}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return run, max(0, q["remaining"] - 1)

    # ------------------------------------------------------------ execute
    async def _emit(self, run_id: UUID, type_: str, data: dict[str, Any]) -> None:
        await self._store.append_event(run_id, type_, data)

    async def _execute(self, run: dict[str, Any], agent: dict[str, Any]) -> None:
        run_id: UUID = run["id"]
        runner = self._runners[agent["kind"]]
        req = RunRequest(
            run_id=str(run_id), agent_id=agent["id"], input=run["input"],
            thread_id=run.get("thread_id"), user_sub=run["user_sub"], config=agent.get("config") or {},
        )
        output = ""
        try:
            await self._store.update_run(run_id, status="running", started_at=utcnow())
            await self._emit(run_id, "status", {"status": "running"})
            async with asyncio.timeout(self._s.bl_run_timeout_s):
                async for ev in runner.run(req):
                    if isinstance(ev, Meta):
                        fields = {k: v for k, v in (("thread_id", ev.thread_id), ("trace_id", ev.trace_id)) if v}
                        if fields:
                            await self._store.update_run(run_id, **fields)
                    elif isinstance(ev, Step):
                        await self._emit(run_id, "step", {"name": ev.name, **({"detail": ev.detail} if ev.detail else {})})
                    elif isinstance(ev, Message):
                        output = ev.content
                        await self._emit(run_id, "message", {"content": ev.content})
            if not output:
                raise AgentError("Агент не вернул ответ")
            final = await self._store.update_run(run_id, status="succeeded", output=output, finished_at=utcnow())
            await self._emit(run_id, "status", {"status": "succeeded"})
            await self._emit(run_id, "done", {"run": jsonable(final)})
        except TimeoutError:
            await self._fail(run_id, "Агент не ответил вовремя")
        except AgentError as e:
            await self._fail(run_id, str(e))
        except asyncio.CancelledError:
            await self._fail(run_id, "Запуск прерван")
            raise
        except Exception:
            log.exception("run %s crashed", run_id)
            await self._fail(run_id, "Внутренняя ошибка запуска")

    async def _fail(self, run_id: UUID, message: str) -> None:
        try:
            await self._store.update_run(run_id, status="failed", error=message, finished_at=utcnow())
            await self._emit(run_id, "status", {"status": "failed"})
            await self._emit(run_id, "error", {"message": message})
        except Exception:
            log.exception("could not record failure of run %s", run_id)

    # ------------------------------------------------------------ stream
    async def stream(self, run_id: UUID, after_seq: int = 0, *, poll_s: float = 0.25,
                     heartbeat_s: float = 15.0) -> AsyncIterator[str]:
        """SSE frames: replay stored events, follow until `done` / `error`."""
        last_beat = asyncio.get_running_loop().time()
        while True:
            events = await self._store.list_events(run_id, after_seq)
            for e in events:
                after_seq = e["seq"]
                yield f"id: {e['seq']}\nevent: {e['type']}\ndata: {json.dumps(e['data'], ensure_ascii=False)}\n\n"
                if e["type"] in TERMINAL:
                    return
            if not events:
                run = await self._store.get_run(run_id)
                if run is None or (run["status"] in ("succeeded", "failed") and not await self._store.list_events(run_id, after_seq)):
                    return  # finished and everything delivered
                now = asyncio.get_running_loop().time()
                if now - last_beat >= heartbeat_s:
                    last_beat = now
                    yield ": keepalive\n\n"
            await asyncio.sleep(poll_s)

    async def shutdown(self) -> None:
        for t in list(self._tasks):
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

"""PostgreSQL Store (schema `bl` inside POSTGRES_DB). DDL is idempotent and runs on start (as in apps/rag)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import asyncpg

DDL = """
CREATE SCHEMA IF NOT EXISTS bl;

CREATE TABLE IF NOT EXISTS bl.agents (
    id          text PRIMARY KEY,
    title       text        NOT NULL,
    description text        NOT NULL DEFAULT '',
    kind        text        NOT NULL,
    enabled     boolean     NOT NULL DEFAULT true,
    input_hint  text,
    config      jsonb       NOT NULL DEFAULT '{}'::jsonb,
    sort        integer     NOT NULL DEFAULT 100,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bl.runs (
    id          uuid PRIMARY KEY,
    agent_id    text        NOT NULL REFERENCES bl.agents(id),
    user_sub    text        NOT NULL,
    username    text,
    status      text        NOT NULL DEFAULT 'queued',
    input       text        NOT NULL,
    output      text,
    error       text,
    thread_id   text,
    trace_id    text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    started_at  timestamptz,
    finished_at timestamptz
);
CREATE INDEX IF NOT EXISTS runs_user_created_idx ON bl.runs (user_sub, created_at DESC);
CREATE INDEX IF NOT EXISTS runs_created_idx ON bl.runs (created_at DESC);

CREATE TABLE IF NOT EXISTS bl.run_events (
    run_id     uuid        NOT NULL REFERENCES bl.runs(id) ON DELETE CASCADE,
    seq        integer     NOT NULL,
    type       text        NOT NULL,
    data       jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (run_id, seq)
);

CREATE TABLE IF NOT EXISTS bl.settings (
    key   text PRIMARY KEY,
    value jsonb NOT NULL
);
"""

_RUN_COLS = (
    "id, agent_id, user_sub, username, status, input, output, error, thread_id, trace_id, "
    "created_at, started_at, finished_at"
)
_UPDATABLE_RUN = {"status", "output", "error", "thread_id", "trace_id", "started_at", "finished_at"}


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


class PgStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PgStore is not connected")
        return self._pool

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=8, init=_init_conn)
        async with self.pool.acquire() as c:
            await c.execute(DDL)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def ping(self) -> bool:
        try:
            async with self.pool.acquire() as c:
                await c.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    # ---------------------------------------------------------------- agents
    async def seed_agents(self, agents: list[dict[str, Any]]) -> None:
        async with self.pool.acquire() as c:
            for a in agents:
                await c.execute(
                    """INSERT INTO bl.agents (id, title, description, kind, enabled, input_hint, config, sort)
                       VALUES ($1,$2,$3,$4,$5,$6,$7,$8) ON CONFLICT (id) DO NOTHING""",
                    a["id"], a["title"], a["description"], a["kind"], a["enabled"],
                    a.get("input_hint"), a.get("config", {}), a.get("sort", 100),
                )

    async def list_agents(self, *, only_enabled: bool) -> list[dict[str, Any]]:
        q = "SELECT * FROM bl.agents" + (" WHERE enabled" if only_enabled else "") + " ORDER BY sort, id"
        async with self.pool.acquire() as c:
            return [dict(r) for r in await c.fetch(q)]

    async def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        async with self.pool.acquire() as c:
            r = await c.fetchrow("SELECT * FROM bl.agents WHERE id=$1", agent_id)
        return dict(r) if r else None

    async def update_agent(self, agent_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        fields = {k: v for k, v in patch.items() if v is not None and k in {"enabled", "title", "description"}}
        if fields:
            sets = ", ".join(f"{k}=${i + 2}" for i, k in enumerate(fields))
            async with self.pool.acquire() as c:
                await c.execute(f"UPDATE bl.agents SET {sets}, updated_at=now() WHERE id=$1", agent_id, *fields.values())
        return await self.get_agent(agent_id)

    # ---------------------------------------------------------------- runs
    async def create_run(self, run: dict[str, Any]) -> dict[str, Any]:
        async with self.pool.acquire() as c:
            r = await c.fetchrow(
                f"""INSERT INTO bl.runs (id, agent_id, user_sub, username, status, input, thread_id, created_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING {_RUN_COLS}""",
                run["id"], run["agent_id"], run["user_sub"], run.get("username"), run["status"],
                run["input"], run.get("thread_id"), run["created_at"],
            )
        return dict(r)

    async def get_run(self, run_id: UUID) -> dict[str, Any] | None:
        async with self.pool.acquire() as c:
            r = await c.fetchrow(f"SELECT {_RUN_COLS} FROM bl.runs WHERE id=$1", run_id)
        return dict(r) if r else None

    async def update_run(self, run_id: UUID, **fields: Any) -> dict[str, Any] | None:
        fields = {k: v for k, v in fields.items() if k in _UPDATABLE_RUN}
        if fields:
            sets = ", ".join(f"{k}=${i + 2}" for i, k in enumerate(fields))
            async with self.pool.acquire() as c:
                await c.execute(f"UPDATE bl.runs SET {sets} WHERE id=$1", run_id, *fields.values())
        return await self.get_run(run_id)

    async def list_runs(self, *, user_sub=None, agent_id=None, status=None, limit=50, offset=0):
        where, args = [], []
        for col, val in (("user_sub", user_sub), ("agent_id", agent_id), ("status", status)):
            if val is not None:
                args.append(val)
                where.append(f"{col}=${len(args)}")
        w = (" WHERE " + " AND ".join(where)) if where else ""
        async with self.pool.acquire() as c:
            total = await c.fetchval(f"SELECT count(*) FROM bl.runs{w}", *args)
            rows = await c.fetch(
                f"SELECT {_RUN_COLS} FROM bl.runs{w} ORDER BY created_at DESC "
                f"LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
                *args, limit, offset,
            )
        return [dict(r) for r in rows], int(total)

    async def count_runs_since(self, user_sub: str, since: datetime) -> int:
        async with self.pool.acquire() as c:
            return int(await c.fetchval(
                "SELECT count(*) FROM bl.runs WHERE user_sub=$1 AND created_at >= $2", user_sub, since))

    async def thread_belongs_to(self, user_sub: str, agent_id: str, thread_id: str) -> bool:
        async with self.pool.acquire() as c:
            return bool(await c.fetchval(
                "SELECT 1 FROM bl.runs WHERE user_sub=$1 AND agent_id=$2 AND thread_id=$3 LIMIT 1",
                user_sub, agent_id, thread_id))

    async def fail_stale_runs(self) -> int:
        async with self.pool.acquire() as c:
            res = await c.execute(
                "UPDATE bl.runs SET status='failed', error='Service restarted', finished_at=now() "
                "WHERE status IN ('queued','running')")
        return int(res.split()[-1])

    # ---------------------------------------------------------------- events
    async def append_event(self, run_id: UUID, type_: str, data: dict[str, Any]) -> int:
        async with self.pool.acquire() as c:
            return int(await c.fetchval(
                """INSERT INTO bl.run_events (run_id, seq, type, data)
                   VALUES ($1, COALESCE((SELECT max(seq) FROM bl.run_events WHERE run_id=$1), 0) + 1, $2, $3)
                   RETURNING seq""",
                run_id, type_, data))

    async def list_events(self, run_id: UUID, after_seq: int = 0) -> list[dict[str, Any]]:
        async with self.pool.acquire() as c:
            rows = await c.fetch(
                "SELECT seq, type, data FROM bl.run_events WHERE run_id=$1 AND seq > $2 ORDER BY seq",
                run_id, after_seq)
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------- admin
    async def stats(self, since: datetime) -> dict[str, Any]:
        async with self.pool.acquire() as c:
            total = await c.fetchval("SELECT count(*) FROM bl.runs")
            today = await c.fetchrow(
                "SELECT count(*) AS n, count(*) FILTER (WHERE status='failed') AS failed, "
                "count(DISTINCT user_sub) AS users FROM bl.runs WHERE created_at >= $1", since)
            by_agent = await c.fetch("SELECT agent_id, count(*) AS runs FROM bl.runs GROUP BY agent_id ORDER BY agent_id")
        return {
            "runs_total": int(total),
            "runs_today": int(today["n"]),
            "failed_today": int(today["failed"]),
            "active_users_today": int(today["users"]),
            "by_agent": [{"agent_id": r["agent_id"], "runs": int(r["runs"])} for r in by_agent],
        }

    async def get_setting(self, key: str) -> Any | None:
        async with self.pool.acquire() as c:
            return await c.fetchval("SELECT value FROM bl.settings WHERE key=$1", key)

    async def put_setting(self, key: str, value: Any) -> None:
        async with self.pool.acquire() as c:
            await c.execute(
                "INSERT INTO bl.settings (key, value) VALUES ($1,$2) "
                "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value", key, value)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

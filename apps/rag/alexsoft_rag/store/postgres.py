"""PostgreSQL state (schema `rag`): collections, documents, ingest jobs, idempotency keys."""

from __future__ import annotations

import base64
import json
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from ..schemas import ChunkingConfig, Collection, Document, Job

DDL = """
CREATE SCHEMA IF NOT EXISTS rag;

CREATE TABLE IF NOT EXISTS rag.collections (
    name              text PRIMARY KEY,
    description       text,
    embedding_model   text        NOT NULL,
    dense_dimensions  integer     NOT NULL,
    chunking          jsonb,
    created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rag.documents (
    id           uuid PRIMARY KEY,
    collection   text        NOT NULL REFERENCES rag.collections(name) ON DELETE CASCADE,
    external_id  text,
    source       jsonb,
    metadata     jsonb,
    chunking     jsonb,
    status       text        NOT NULL DEFAULT 'queued',
    chunks_count integer     NOT NULL DEFAULT 0,
    error        text,
    created_at   timestamptz NOT NULL DEFAULT now(),
    indexed_at   timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS documents_collection_external_id_uq
    ON rag.documents (collection, external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS documents_collection_created_idx
    ON rag.documents (collection, created_at, id);

CREATE TABLE IF NOT EXISTS rag.jobs (
    id           uuid PRIMARY KEY,
    type         text        NOT NULL DEFAULT 'ingest',
    status       text        NOT NULL DEFAULT 'queued',
    document_id  uuid        REFERENCES rag.documents(id) ON DELETE CASCADE,
    stage        text,
    error        text,
    created_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz
);

CREATE TABLE IF NOT EXISTS rag.idempotency_keys (
    collection  text NOT NULL,
    key         text NOT NULL,
    job_id      uuid NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (collection, key)
);
"""


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode()


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        if raw.startswith("o:"):
            return max(0, int(raw[2:]))
    except Exception:
        pass
    return 0


async def _init_connection(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


def _collection(row: asyncpg.Record) -> Collection:
    chunking = row["chunking"]
    return Collection(
        name=row["name"],
        description=row["description"],
        embedding_model=row["embedding_model"],
        dense_dimensions=row["dense_dimensions"],
        chunking=ChunkingConfig(**chunking) if chunking else None,
        documents_count=row.get("documents_count") or 0,
        chunks_count=row.get("chunks_count") or 0,
        created_at=row["created_at"],
    )


def _document(row: asyncpg.Record) -> Document:
    return Document(
        id=row["id"],
        collection=row["collection"],
        external_id=row["external_id"],
        source=row["source"],
        metadata=row["metadata"],
        status=row["status"],
        chunks_count=row["chunks_count"],
        error=row["error"],
        created_at=row["created_at"],
        indexed_at=row["indexed_at"],
    )


def _job(row: asyncpg.Record) -> Job:
    return Job(
        id=row["id"],
        type=row["type"],
        status=row["status"],
        document_id=row["document_id"],
        stage=row["stage"],
        error=row["error"],
        created_at=row["created_at"],
        finished_at=row["finished_at"],
    )


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        assert self._pool is not None, "Database not connected"
        return self._pool

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._dsn, min_size=1, max_size=8, init=_init_connection
        )
        async with self.pool.acquire() as conn:
            await conn.execute(DDL)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def is_alive(self) -> bool:
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    # ---- collections -----------------------------------------------------------
    async def create_collection(
        self,
        name: str,
        description: str | None,
        embedding_model: str,
        dense_dimensions: int,
        chunking: ChunkingConfig | None,
    ) -> Collection | None:
        """Returns None if the name is already taken."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO rag.collections (name, description, embedding_model, dense_dimensions, chunking)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (name) DO NOTHING
                RETURNING *
                """,
                name,
                description,
                embedding_model,
                dense_dimensions,
                chunking.model_dump() if chunking else None,
            )
        return _collection(row) if row else None

    _COLLECTION_SQL = """
        SELECT c.*,
               (SELECT count(*) FROM rag.documents d WHERE d.collection = c.name) AS documents_count,
               (SELECT COALESCE(sum(d.chunks_count), 0) FROM rag.documents d
                 WHERE d.collection = c.name AND d.status = 'indexed')::bigint AS chunks_count
        FROM rag.collections c
    """

    async def get_collection(self, name: str) -> Collection | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(self._COLLECTION_SQL + " WHERE c.name = $1", name)
        return _collection(row) if row else None

    async def list_collections(self, limit: int, offset: int) -> tuple[list[Collection], bool]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                self._COLLECTION_SQL + " ORDER BY c.created_at, c.name LIMIT $1 OFFSET $2",
                limit + 1,
                offset,
            )
        return [_collection(r) for r in rows[:limit]], len(rows) > limit

    async def delete_collection(self, name: str) -> bool:
        async with self.pool.acquire() as conn:
            res = await conn.execute("DELETE FROM rag.collections WHERE name = $1", name)
        return res.endswith("1")

    # ---- documents ------------------------------------------------------------------
    async def create_ingest(
        self,
        collection: str,
        external_id: str | None,
        source: dict[str, Any],
        metadata: dict[str, Any] | None,
        chunking: ChunkingConfig | None,
        idempotency_key: str | None,
    ) -> tuple[Job, bool]:
        """Create or reset a document and a queued job atomically.

        Returns (job, created). With a known Idempotency-Key returns the original job
        and created=False. Re-ingest with the same `external_id` reuses the document row.
        """
        async with self.pool.acquire() as conn, conn.transaction():
            if idempotency_key:
                existing = await conn.fetchrow(
                    """
                    SELECT j.* FROM rag.idempotency_keys k JOIN rag.jobs j ON j.id = k.job_id
                    WHERE k.collection = $1 AND k.key = $2
                    """,
                    collection,
                    idempotency_key,
                )
                if existing:
                    return _job(existing), False

            doc_id: UUID | None = None
            if external_id:
                doc_id = await conn.fetchval(
                    """
                    UPDATE rag.documents
                       SET source = $3, metadata = $4, chunking = $5,
                           status = 'queued', error = NULL
                     WHERE collection = $1 AND external_id = $2
                    RETURNING id
                    """,
                    collection,
                    external_id,
                    source,
                    metadata,
                    chunking.model_dump() if chunking else None,
                )
            if doc_id is None:
                doc_id = uuid4()
                await conn.execute(
                    """
                    INSERT INTO rag.documents (id, collection, external_id, source, metadata, chunking)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    doc_id,
                    collection,
                    external_id,
                    source,
                    metadata,
                    chunking.model_dump() if chunking else None,
                )
            row = await conn.fetchrow(
                "INSERT INTO rag.jobs (id, document_id) VALUES ($1, $2) RETURNING *",
                uuid4(),
                doc_id,
            )
            if idempotency_key:
                await conn.execute(
                    "INSERT INTO rag.idempotency_keys (collection, key, job_id) VALUES ($1, $2, $3)",
                    collection,
                    idempotency_key,
                    row["id"],
                )
        return _job(row), True

    async def get_document(self, collection: str, doc_id: UUID) -> Document | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM rag.documents WHERE collection = $1 AND id = $2", collection, doc_id
            )
        return _document(row) if row else None

    async def get_document_row(self, doc_id: UUID) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM rag.documents WHERE id = $1", doc_id)

    async def list_documents(
        self, collection: str, limit: int, offset: int, status: str | None
    ) -> tuple[list[Document], bool]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM rag.documents
                 WHERE collection = $1 AND ($2::text IS NULL OR status = $2)
                 ORDER BY created_at, id LIMIT $3 OFFSET $4
                """,
                collection,
                status,
                limit + 1,
                offset,
            )
        return [_document(r) for r in rows[:limit]], len(rows) > limit

    async def delete_document(self, collection: str, doc_id: UUID) -> bool:
        async with self.pool.acquire() as conn:
            res = await conn.execute(
                "DELETE FROM rag.documents WHERE collection = $1 AND id = $2", collection, doc_id
            )
        return res.endswith("1")

    async def set_document_status(
        self,
        doc_id: UUID,
        status: str,
        *,
        chunks_count: int | None = None,
        error: str | None = None,
    ) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE rag.documents
                   SET status = $2,
                       chunks_count = COALESCE($3, chunks_count),
                       error = $4,
                       indexed_at = CASE WHEN $2 = 'indexed' THEN now() ELSE indexed_at END
                 WHERE id = $1
                """,
                doc_id,
                status,
                chunks_count,
                error,
            )

    # ---- jobs ---------------------------------------------------------------------------
    async def get_job(self, job_id: UUID) -> Job | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM rag.jobs WHERE id = $1", job_id)
        return _job(row) if row else None

    async def update_job(
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        stage: str | None = None,
        error: str | None = None,
        finished: bool = False,
    ) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE rag.jobs
                   SET status = COALESCE($2, status),
                       stage = COALESCE($3, stage),
                       error = COALESCE($4, error),
                       finished_at = CASE WHEN $5 THEN now() ELSE finished_at END
                 WHERE id = $1
                """,
                job_id,
                status,
                stage,
                error,
                finished,
            )

    async def fail_stale_jobs(self) -> int:
        """After a restart: in-process jobs are gone, so queued/running ones cannot finish."""
        async with self.pool.acquire() as conn, conn.transaction():
            rows = await conn.fetch(
                """
                UPDATE rag.jobs SET status = 'failed', error = 'service restarted', finished_at = now()
                 WHERE status IN ('queued', 'running') RETURNING document_id
                """
            )
            await conn.execute(
                """
                UPDATE rag.documents SET status = 'failed', error = 'service restarted'
                 WHERE status IN ('queued', 'processing')
                """
            )
        return len(rows)

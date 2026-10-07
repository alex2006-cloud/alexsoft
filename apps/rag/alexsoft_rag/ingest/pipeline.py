"""Ingest pipeline: load -> parse -> chunk -> embed -> upsert (runs as an in-process task)."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID, uuid5

from ..clients.litellm import LiteLLMClient
from ..clients.minio_client import ObjectStore
from ..errors import ApiError
from ..parsers import parse_document
from ..parsers.base import ParseContext, VisionOCR
from ..retrieval.sparse import SparseEmbedder
from ..schemas import ChunkingConfig
from ..store.postgres import Database
from ..store.qdrant import VectorStore
from .chunker import chunk_segments
from .loader import load_source

log = logging.getLogger("alexsoft_rag.ingest")


def point_id(document_id: UUID, position: int) -> str:
    """Deterministic point id: re-ingest overwrites points in place (no gap in search)."""
    return str(uuid5(document_id, str(position)))


class IngestPipeline:
    def __init__(
        self,
        db: Database,
        vectors: VectorStore,
        llm: LiteLLMClient,
        sparse: SparseEmbedder,
        objects: ObjectStore,
        *,
        max_chars: int,
        max_bytes: int = 50 * 1024 * 1024,
        ocr: VisionOCR | None = None,
        max_ocr_pages: int = 60,
        embed_batch_size: int = 64,
        upsert_batch_size: int = 64,
        concurrency: int = 2,
    ) -> None:
        self._db = db
        self._vectors = vectors
        self._llm = llm
        self._sparse = sparse
        self._objects = objects
        self._max_chars = max_chars
        self._max_bytes = max_bytes
        self._ocr = ocr
        self._max_ocr_pages = max_ocr_pages
        self._embed_batch = embed_batch_size
        self._upsert_batch = upsert_batch_size
        self._sem = asyncio.Semaphore(concurrency)
        self._tasks: set[asyncio.Task] = set()

    def submit(self, job_id: UUID, document_id: UUID) -> asyncio.Task:
        task = asyncio.create_task(self._guarded(job_id, document_id), name=f"ingest-{job_id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def drain(self) -> None:
        if self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

    async def _guarded(self, job_id: UUID, document_id: UUID) -> None:
        async with self._sem:
            try:
                await self.run(job_id, document_id)
            except asyncio.CancelledError:
                await self._fail(job_id, document_id, "cancelled")
                raise
            except ApiError as e:
                await self._fail(job_id, document_id, f"{e.code}: {e.detail or e.title}")
            except Exception as e:  # noqa: BLE001 - job must always reach a terminal state
                log.exception("ingest job %s crashed", job_id)
                await self._fail(job_id, document_id, f"internal_error: {e}")

    async def _fail(self, job_id: UUID, document_id: UUID, error: str) -> None:
        log.warning("ingest job %s failed: %s", job_id, error)
        try:
            await self._db.update_job(job_id, status="failed", error=error, finished=True)
            await self._db.set_document_status(document_id, "failed", error=error)
        except Exception:  # noqa: BLE001
            log.exception("could not record failure of job %s", job_id)

    async def _stage(self, job_id: UUID, stage: str) -> None:
        await self._db.update_job(job_id, status="running", stage=stage)

    async def run(self, job_id: UUID, document_id: UUID) -> None:
        row = await self._db.get_document_row(document_id)
        if row is None:
            raise ApiError(404, "not_found", "Document was deleted before ingest started")
        collection = await self._db.get_collection(row["collection"])
        if collection is None:
            raise ApiError(404, "not_found", "Collection was deleted before ingest started")
        name = collection.name
        language = collection.sparse_language

        await self._db.set_document_status(document_id, "processing")

        cfg_raw = row["chunking"] or (collection.chunking.model_dump() if collection.chunking else None)
        cfg = ChunkingConfig(**cfg_raw) if cfg_raw else ChunkingConfig()

        # load
        await self._stage(job_id, "load")
        raw = await load_source(
            dict(row["source"]), self._objects, max_bytes=self._max_bytes, external_id=row["external_id"]
        )

        # parse (format-specific: text, code, PDF with OCR, Excel, diagrams)
        await self._stage(job_id, "parse")
        ctx = ParseContext(chunk_size=cfg.chunk_size, ocr=self._ocr, max_ocr_pages=self._max_ocr_pages)
        segments = await parse_document(raw, ctx)
        total_chars = sum(len(s.text) for s in segments)
        if total_chars > self._max_chars:
            raise ApiError(413, "payload_too_large", f"Document text exceeds {self._max_chars} characters")

        # chunk
        await self._stage(job_id, "chunk")
        chunks = await asyncio.to_thread(chunk_segments, segments, cfg)
        if not chunks:
            raise ApiError(422, "validation_error", "No chunks produced from document")
        path = row["external_id"] or raw.filename

        # embed (dense via LiteLLM, sparse locally)
        await self._stage(job_id, "embed")
        dense: list[list[float]] = []
        sparse = []
        for i in range(0, len(chunks), self._embed_batch):
            batch = [c.embed_text for c in chunks[i : i + self._embed_batch]]
            vectors = await self._llm.embed(batch, model=collection.embedding_model)
            for v in vectors:
                if len(v) != collection.dense_dimensions:
                    raise ApiError(
                        502,
                        "embedding_unavailable",
                        f"Embedding has {len(v)} dims, collection expects {collection.dense_dimensions}",
                    )
            dense.extend(vectors)
            sparse.extend(await self._sparse.embed_documents(batch, language))

        # upsert (overwrite in place, then drop tail left from a longer previous version)
        await self._stage(job_id, "upsert")
        metadata = dict(row["metadata"] or {})
        await self._vectors.ensure_metadata_indexes(name, metadata)
        points = [
            (
                point_id(document_id, pos),
                dense[pos],
                sparse[pos],
                {
                    "collection": name,
                    "document_id": str(document_id),
                    "external_id": row["external_id"],
                    "position": pos,
                    "text": chunk.text,
                    "header": chunk.header,
                    "kind": chunk.kind,
                    "locator": {"path": path, **chunk.locator},
                    "metadata": metadata,
                },
            )
            for pos, chunk in enumerate(chunks)
        ]
        for i in range(0, len(points), self._upsert_batch):
            await self._vectors.upsert(name, points[i : i + self._upsert_batch])
        await self._vectors.delete_document_points(name, document_id, from_position=len(chunks))

        if await self._db.get_document_row(document_id) is None:  # deleted while we were indexing
            await self._vectors.delete_document_points(name, document_id)
            await self._db.update_job(job_id, status="failed", error="document deleted", finished=True)
            return

        await self._db.set_document_status(document_id, "indexed", chunks_count=len(chunks))
        await self._db.update_job(job_id, status="succeeded", finished=True)
        log.info("ingest job %s done: document=%s chunks=%d", job_id, document_id, len(chunks))

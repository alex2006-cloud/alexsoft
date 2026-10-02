"""Retrieval layer: query embedding -> hybrid search in Qdrant -> normalized chunks."""

from __future__ import annotations

import time
from uuid import UUID

from ..clients.litellm import LiteLLMClient
from ..errors import not_found
from ..schemas import Chunk, SearchParams, Timings
from ..store.postgres import Database
from ..store.qdrant import VectorStore, build_filter
from .sparse import SparseEmbedder

PREFETCH_MIN = 20


def normalize_score(raw: float, fusion: str, rrf_k: int) -> float:
    """Map fused Qdrant score to [0, 1]; 1.0 = top rank in both dense and sparse lists.

    RRF: sum of 1/(k+rank) over 2 lists; best case 2/(k+1).  DBSF: sum of 2 normalized scores (<= 2).
    """
    best = 2.0 / (rrf_k + 1) if fusion == "rrf" else 2.0
    return max(0.0, min(1.0, raw / best))


class SearchService:
    def __init__(
        self,
        db: Database,
        vectors: VectorStore,
        llm: LiteLLMClient,
        sparse: SparseEmbedder,
        *,
        rrf_k: int = 60,
    ) -> None:
        self._db = db
        self._vectors = vectors
        self._llm = llm
        self._sparse = sparse
        self._rrf_k = rrf_k

    async def search(self, params: SearchParams, query: str) -> tuple[list[Chunk], Timings]:
        t_start = time.perf_counter()
        collection = await self._db.get_collection(params.collection)
        if collection is None:
            raise not_found(f"Collection {params.collection!r}")

        t0 = time.perf_counter()
        # same embedding model as at ingest: it is fixed on the collection
        dense = (await self._llm.embed([query], model=collection.embedding_model))[0]
        sparse = await self._sparse.embed_query(query)
        t_embed = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        points = await self._vectors.hybrid_search(
            params.collection,
            dense,
            sparse,
            top_k=params.top_k,
            prefetch_limit=max(PREFETCH_MIN, params.top_k * 4),
            fusion=params.fusion,
            rrf_k=self._rrf_k,
            flt=build_filter(params.filter),
        )
        t_search = (time.perf_counter() - t0) * 1000

        chunks: list[Chunk] = []
        for p in points:
            score = normalize_score(float(p.score), params.fusion, self._rrf_k)
            if params.score_threshold is not None and score < params.score_threshold:
                continue
            payload = p.payload or {}
            chunks.append(
                Chunk(
                    id=str(p.id),
                    document_id=UUID(payload["document_id"]),
                    external_id=payload.get("external_id"),
                    text=payload.get("text", ""),
                    score=round(score, 6),
                    position=payload.get("position"),
                    metadata=payload.get("metadata") or None,
                )
            )
        timings = Timings(
            embed=round(t_embed, 2),
            search=round(t_search, 2),
            total=round((time.perf_counter() - t_start) * 1000, 2),
        )
        return chunks, timings

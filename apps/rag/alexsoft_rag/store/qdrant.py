"""Qdrant access: collections with named vectors `dense` + `sparse`, hybrid query via prefetch."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qm

from ..errors import ApiError, upstream
from ..retrieval.sparse import SparseVec

log = logging.getLogger("alexsoft_rag.qdrant")

DENSE = "dense"
SPARSE = "sparse"


def build_filter(
    metadata_filter: dict[str, Any] | None, *, document_id: UUID | None = None
) -> qm.Filter | None:
    """Payload filter. All conditions are ANDed; list value = any-of (contract MetadataFilter)."""
    must: list[qm.Condition] = []
    if document_id is not None:
        must.append(
            qm.FieldCondition(key="document_id", match=qm.MatchValue(value=str(document_id)))
        )
    for key, value in (metadata_filter or {}).items():
        field = f"metadata.{key}"
        if isinstance(value, list):
            must.append(qm.FieldCondition(key=field, match=qm.MatchAny(any=[str(v) for v in value])))
        elif isinstance(value, bool) or isinstance(value, (str, int)):
            must.append(qm.FieldCondition(key=field, match=qm.MatchValue(value=value)))
        elif isinstance(value, float):
            must.append(qm.FieldCondition(key=field, range=qm.Range(gte=value, lte=value)))
    return qm.Filter(must=must) if must else None


class VectorStore:
    def __init__(self, url: str, api_key: str = "", client: AsyncQdrantClient | None = None) -> None:
        # trust_env=False: internal service, must not go through a Windows system (SOCKS/HTTP) proxy
        self.client = client or AsyncQdrantClient(
            url=url, api_key=api_key or None, timeout=60, trust_env=False
        )

    async def aclose(self) -> None:
        await self.client.close()

    async def is_alive(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False

    async def create_collection(self, name: str, dimensions: int) -> None:
        try:
            await self.client.create_collection(
                collection_name=name,
                vectors_config={DENSE: qm.VectorParams(size=dimensions, distance=qm.Distance.COSINE)},
                sparse_vectors_config={SPARSE: qm.SparseVectorParams(modifier=qm.Modifier.IDF)},
            )
            for field, schema in (
                ("document_id", qm.PayloadSchemaType.KEYWORD),
                ("external_id", qm.PayloadSchemaType.KEYWORD),
                ("position", qm.PayloadSchemaType.INTEGER),
            ):
                await self.client.create_payload_index(name, field, schema)
        except Exception as e:
            raise upstream("vector_store_unavailable", f"Qdrant create_collection failed: {e}") from e

    async def delete_collection(self, name: str) -> None:
        try:
            await self.client.delete_collection(name)
        except Exception as e:
            raise upstream("vector_store_unavailable", f"Qdrant delete_collection failed: {e}") from e

    async def exists(self, name: str) -> bool:
        try:
            return await self.client.collection_exists(name)
        except Exception as e:
            raise upstream("vector_store_unavailable", f"Qdrant unavailable: {e}") from e

    async def ensure_metadata_indexes(self, name: str, metadata: dict[str, Any] | None) -> None:
        """Best-effort payload indexes for metadata keys (speeds up filters; idempotent)."""
        for key, value in (metadata or {}).items():
            if isinstance(value, bool):
                schema = qm.PayloadSchemaType.BOOL
            elif isinstance(value, int):
                schema = qm.PayloadSchemaType.INTEGER
            elif isinstance(value, float):
                schema = qm.PayloadSchemaType.FLOAT
            else:
                schema = qm.PayloadSchemaType.KEYWORD
            try:
                await self.client.create_payload_index(name, f"metadata.{key}", schema)
            except Exception as e:  # already exists / type conflict: filters still work
                log.debug("payload index metadata.%s skipped: %s", key, e)

    async def upsert(
        self,
        name: str,
        points: list[tuple[str, list[float], SparseVec, dict[str, Any]]],
    ) -> None:
        structs = [
            qm.PointStruct(
                id=pid,
                vector={
                    DENSE: dense,
                    SPARSE: qm.SparseVector(indices=sparse.indices, values=sparse.values),
                },
                payload=payload,
            )
            for pid, dense, sparse, payload in points
        ]
        try:
            await self.client.upsert(collection_name=name, points=structs, wait=True)
        except Exception as e:
            raise upstream("vector_store_unavailable", f"Qdrant upsert failed: {e}") from e

    async def delete_document_points(
        self, name: str, document_id: UUID, *, from_position: int | None = None
    ) -> None:
        """Delete a document's points; with `from_position` only the tail (position >= N)."""
        must: list[qm.Condition] = [
            qm.FieldCondition(key="document_id", match=qm.MatchValue(value=str(document_id)))
        ]
        if from_position is not None:
            must.append(qm.FieldCondition(key="position", range=qm.Range(gte=from_position)))
        try:
            await self.client.delete(
                collection_name=name,
                points_selector=qm.FilterSelector(filter=qm.Filter(must=must)),
                wait=True,
            )
        except Exception as e:
            raise upstream("vector_store_unavailable", f"Qdrant delete failed: {e}") from e

    async def hybrid_search(
        self,
        name: str,
        dense: list[float],
        sparse: SparseVec,
        *,
        top_k: int,
        prefetch_limit: int,
        fusion: str,
        rrf_k: int,
        flt: qm.Filter | None,
    ) -> list[qm.ScoredPoint]:
        query: qm.Query
        if fusion == "dbsf":
            query = qm.FusionQuery(fusion=qm.Fusion.DBSF)
        else:
            query = qm.RrfQuery(rrf=qm.Rrf(k=rrf_k))
        try:
            res = await self.client.query_points(
                collection_name=name,
                prefetch=[
                    qm.Prefetch(query=dense, using=DENSE, limit=prefetch_limit, filter=flt),
                    qm.Prefetch(
                        query=qm.SparseVector(indices=sparse.indices, values=sparse.values),
                        using=SPARSE,
                        limit=prefetch_limit,
                        filter=flt,
                    ),
                ],
                query=query,
                limit=top_k,
                with_payload=True,
            )
        except Exception as e:
            if "doesn't exist" in str(e) or "Not found" in str(e):
                raise ApiError(404, "not_found", f"Collection {name} not found in Qdrant") from e
            raise upstream("vector_store_unavailable", f"Qdrant query failed: {e}") from e
        return list(res.points)

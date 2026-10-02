"""Service container: wires clients, stores and pipelines (tests can inject fakes)."""

from __future__ import annotations

from dataclasses import dataclass

from .clients.guard import GuardrailsClient, build_guard
from .clients.litellm import LiteLLMClient
from .clients.minio_client import ObjectStore
from .config import Settings
from .ingest.pipeline import IngestPipeline
from .retrieval.query import QueryService
from .retrieval.search import SearchService
from .retrieval.sparse import FastEmbedBm25, SparseEmbedder
from .store.postgres import Database
from .store.qdrant import VectorStore


@dataclass
class Services:
    settings: Settings
    db: Database
    vectors: VectorStore
    llm: LiteLLMClient
    objects: ObjectStore
    guard: GuardrailsClient
    sparse: SparseEmbedder
    pipeline: IngestPipeline
    search: SearchService
    query: QueryService


def build_services(settings: Settings, *, llm: LiteLLMClient | None = None) -> Services:
    """`llm` can be injected (tests use a fake that needs no provider keys)."""
    db = Database(settings.database_dsn)
    vectors = VectorStore(settings.qdrant_url, settings.qdrant_api_key)
    llm = llm or LiteLLMClient(
        settings.ai_gateway_url,
        settings.litellm_master_key,
        embedding_model=settings.rag_embedding_model,
        timeout_s=settings.rag_llm_timeout_s,
    )
    objects = ObjectStore(
        settings.minio_hostport,
        settings.minio_root_user,
        settings.minio_root_password,
        settings.rag_minio_bucket,
        secure=settings.minio_secure,
    )
    guard = build_guard(settings.llm_guard_enabled)
    sparse = FastEmbedBm25(settings.rag_sparse_model, settings.rag_sparse_language)
    pipeline = IngestPipeline(
        db,
        vectors,
        llm,
        sparse,
        objects,
        max_chars=settings.rag_max_document_chars,
        embed_batch_size=settings.rag_embed_batch_size,
        upsert_batch_size=settings.rag_upsert_batch_size,
        concurrency=settings.rag_ingest_concurrency,
    )
    search = SearchService(db, vectors, llm, sparse, rrf_k=settings.rag_rrf_k)
    query = QueryService(search, llm, guard, default_model=settings.rag_llm_model)
    return Services(settings, db, vectors, llm, objects, guard, sparse, pipeline, search, query)

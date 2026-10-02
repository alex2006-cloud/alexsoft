"""Pydantic models mirroring artifacts/api/rag.openapi.yaml (contract-first)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

CollectionName = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")]
MetadataValue = Union[str, float, int, bool, list[str]]
DocumentStatus = Literal["queued", "processing", "indexed", "failed"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- health -----------------------------------------------------------------
class Health(BaseModel):
    status: Literal["ok", "degraded", "down"]
    dependencies: dict[str, Literal["ok", "down"]] | None = None


# ---- chunking / collections --------------------------------------------------
class ChunkingConfig(Strict):
    strategy: Literal["sentence", "markdown", "token"] = "markdown"
    chunk_size: int = Field(512, ge=64, le=8192)
    chunk_overlap: int = Field(64, ge=0, le=1024)

    @model_validator(mode="after")
    def _overlap_smaller_than_size(self) -> "ChunkingConfig":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


class CollectionCreate(Strict):
    name: CollectionName
    description: str | None = Field(None, max_length=500)
    chunking: ChunkingConfig | None = None


class Collection(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str
    dense_dimensions: int
    chunking: ChunkingConfig | None = None
    documents_count: int = 0
    chunks_count: int = 0
    created_at: datetime


class CollectionPage(BaseModel):
    items: list[Collection]
    next_cursor: str | None = None


# ---- documents / jobs ----------------------------------------------------------
def _check_metadata(v: dict[str, MetadataValue] | None) -> dict[str, MetadataValue] | None:
    if v is not None and len(v) > 32:
        raise ValueError("metadata has more than 32 properties")
    return v


class MinioSource(Strict):
    type: Literal["minio"]
    bucket: str
    key: str
    version_id: str | None = None


class InlineSource(Strict):
    type: Literal["inline"]
    # upper bound is enforced in the route (413 payload_too_large per contract), not here (422)
    text: str = Field(min_length=1)
    content_type: Literal["text/plain", "text/markdown"] = "text/plain"


DocumentSource = Annotated[Union[MinioSource, InlineSource], Field(discriminator="type")]


class DocumentIngest(Strict):
    external_id: str | None = Field(None, max_length=256)
    source: DocumentSource
    metadata: dict[str, MetadataValue] | None = None
    chunking: ChunkingConfig | None = None

    @field_validator("metadata")
    @classmethod
    def _metadata_size(cls, v: dict[str, MetadataValue] | None) -> dict[str, MetadataValue] | None:
        return _check_metadata(v)


class Document(BaseModel):
    id: UUID
    collection: str
    external_id: str | None = None
    source: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    status: DocumentStatus
    chunks_count: int = 0
    error: str | None = None
    created_at: datetime
    indexed_at: datetime | None = None


class DocumentPage(BaseModel):
    items: list[Document]
    next_cursor: str | None = None


class Job(BaseModel):
    id: UUID
    type: Literal["ingest"] = "ingest"
    status: Literal["queued", "running", "succeeded", "failed"]
    document_id: UUID | None = None
    stage: Literal["load", "parse", "chunk", "embed", "upsert"] | None = None
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


# ---- retrieval -------------------------------------------------------------------
class SearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collection: CollectionName
    top_k: int = Field(5, ge=1, le=50)
    fusion: Literal["rrf", "dbsf"] = "rrf"
    score_threshold: float | None = Field(None, ge=0, le=1)
    filter: dict[str, MetadataValue] | None = Field(None)

    @field_validator("filter")
    @classmethod
    def _filter_size(cls, v: dict[str, MetadataValue] | None) -> dict[str, MetadataValue] | None:
        if v is not None and len(v) > 16:
            raise ValueError("filter has more than 16 properties")
        return v


class SearchRequest(SearchParams):
    query: str = Field(min_length=1, max_length=4000)


class Chunk(BaseModel):
    id: str
    document_id: UUID
    external_id: str | None = None
    text: str
    score: float
    position: int | None = Field(None, ge=0)
    metadata: dict[str, Any] | None = None


class Timings(BaseModel):
    embed: float | None = None
    search: float | None = None
    guard: float | None = None
    generate: float | None = None
    total: float | None = None


class SearchResponse(BaseModel):
    chunks: list[Chunk]
    timings_ms: Timings | None = None


class QueryRequest(SearchParams):
    question: str = Field(min_length=1, max_length=4000)
    model: str | None = None
    temperature: float = Field(0.1, ge=0, le=2)
    max_output_tokens: int = Field(1024, ge=1, le=8192)


class Citation(BaseModel):
    chunk_id: str
    document_id: UUID
    external_id: str | None = None
    quote: str | None = None


class Usage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class QueryResponse(BaseModel):
    answer: str | None = None
    insufficient_context: bool
    citations: list[Citation]
    chunks: list[Chunk]
    model: str | None = None
    usage: Usage | None = None
    trace_id: str | None = None
    timings_ms: Timings | None = None

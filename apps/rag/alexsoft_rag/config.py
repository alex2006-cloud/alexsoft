"""Service configuration. Source of truth: repo-root `.env` (see `.env.example`)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # service
    rag_host: str = "127.0.0.1"
    rag_port: int = 8200
    rag_api_key: str = ""
    rag_max_document_chars: int = 1_000_000
    rag_max_object_bytes: int = 50 * 1024 * 1024
    rag_max_ocr_pages: int = 60
    rag_ingest_concurrency: int = 2
    rag_embed_batch_size: int = 64
    rag_upsert_batch_size: int = 64
    rag_sparse_model: str = "Qdrant/bm25"
    rag_sparse_language: str = "russian"
    rag_rrf_k: int = 60

    # models (always via LiteLLM)
    rag_embedding_model: str = "text-embedding-3-small"
    rag_embedding_dimensions: int = 1536
    rag_llm_model: str = "deepseek"
    rag_vision_model: str = "vision"  # LiteLLM alias used for OCR of scanned PDF pages
    ai_gateway_url: str = "http://127.0.0.1:8080"
    litellm_master_key: str = ""
    rag_llm_timeout_s: float = 120.0

    # guardrails (stage 6 component; false = NoopGuard)
    llm_guard_enabled: bool = False

    # qdrant
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_api_key: str = ""

    # minio
    minio_endpoint: str = "localhost"
    minio_port: int = 9000
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "change-me"
    rag_minio_bucket: str = "rag-docs"
    minio_secure: bool = False

    # postgres (schema "rag" inside POSTGRES_DB)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "alexsoft"
    postgres_user: str = "alexsoft"
    postgres_password: str = "change-me"
    rag_database_url: str = ""  # optional full DSN override

    @property
    def database_dsn(self) -> str:
        if self.rag_database_url:
            return self.rag_database_url
        return (
            f"postgresql://{quote(self.postgres_user)}:{quote(self.postgres_password)}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def minio_hostport(self) -> str:
        return f"{self.minio_endpoint}:{self.minio_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

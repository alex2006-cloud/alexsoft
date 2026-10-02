"""Local sparse (BM25) embeddings via fastembed. No LLM provider involved."""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SparseVec:
    indices: list[int]
    values: list[float]


class SparseEmbedder(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[SparseVec]: ...

    async def embed_query(self, text: str) -> SparseVec: ...


class FastEmbedBm25:
    def __init__(self, model_name: str = "Qdrant/bm25", language: str = "russian") -> None:
        self._model_name = model_name
        self._language = language
        self._model = None
        self._lock = threading.Lock()

    def _get(self):
        with self._lock:
            if self._model is None:
                from fastembed import SparseTextEmbedding

                kwargs = {"language": self._language} if "bm25" in self._model_name else {}
                self._model = SparseTextEmbedding(model_name=self._model_name, **kwargs)
            return self._model

    def warmup(self) -> None:
        self._get()

    def _docs(self, texts: list[str]) -> list[SparseVec]:
        model = self._get()
        return [
            SparseVec([int(i) for i in e.indices], [float(v) for v in e.values])
            for e in model.embed(texts)
        ]

    def _query(self, text: str) -> SparseVec:
        model = self._get()
        e = next(iter(model.query_embed(text)))
        return SparseVec([int(i) for i in e.indices], [float(v) for v in e.values])

    async def embed_documents(self, texts: list[str]) -> list[SparseVec]:
        if not texts:
            return []
        return await asyncio.to_thread(self._docs, texts)

    async def embed_query(self, text: str) -> SparseVec:
        return await asyncio.to_thread(self._query, text)

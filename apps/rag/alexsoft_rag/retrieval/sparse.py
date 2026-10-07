"""Local sparse (BM25) embeddings via fastembed. No LLM provider involved.

The BM25 language (stemming/stop-words) is a per-collection setting (`sparse_language`).
Identifiers (`snake_case`, `camelCase`, `kebab-case`) are expanded into their words so that a query
like "embed query" finds `embed_query` / `embedQuery`.
"""

from __future__ import annotations

import asyncio
import re
import threading
from dataclasses import dataclass
from typing import Protocol

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_IDENT = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[_\-][A-Za-z0-9]+)+|[a-z0-9]+[A-Z][A-Za-z0-9]*|[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*")


@dataclass(frozen=True)
class SparseVec:
    indices: list[int]
    values: list[float]


def expand_identifiers(text: str) -> str:
    """Append the words of compound identifiers: `embed_query`, `embedQuery` -> `embed query`."""
    extra: list[str] = []
    for m in _IDENT.finditer(text):
        ident = m.group(0)
        words = [w for part in re.split(r"[_\-]+", ident) for w in _CAMEL.split(part) if w]
        if len(words) > 1:
            extra.append(" ".join(words))
    return f"{text}\n{' '.join(extra)}" if extra else text


class SparseEmbedder(Protocol):
    async def embed_documents(self, texts: list[str], language: str = "russian") -> list[SparseVec]: ...

    async def embed_query(self, text: str, language: str = "russian") -> SparseVec: ...


class _Bm25:
    def __init__(self, model_name: str, language: str) -> None:
        self._model_name = model_name
        self._language = language
        self._model = None
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            if self._model is None:
                from fastembed import SparseTextEmbedding

                kwargs = {"language": self._language} if "bm25" in self._model_name else {}
                self._model = SparseTextEmbedding(model_name=self._model_name, **kwargs)
            return self._model


class FastEmbedBm25:
    """One lazily-created fastembed model per language."""

    def __init__(self, model_name: str = "Qdrant/bm25", language: str = "russian") -> None:
        self._model_name = model_name
        self._default_language = language
        self._models: dict[str, _Bm25] = {}
        self._lock = threading.Lock()

    def _model(self, language: str | None) -> _Bm25:
        lang = language or self._default_language
        with self._lock:
            if lang not in self._models:
                self._models[lang] = _Bm25(self._model_name, lang)
            return self._models[lang]

    def warmup(self, languages: tuple[str, ...] = ("russian", "english")) -> None:
        for lang in languages:
            self._model(lang).get()

    def _docs(self, texts: list[str], language: str | None) -> list[SparseVec]:
        model = self._model(language).get()
        expanded = [expand_identifiers(t) for t in texts]
        return [
            SparseVec([int(i) for i in e.indices], [float(v) for v in e.values])
            for e in model.embed(expanded)
        ]

    def _query(self, text: str, language: str | None) -> SparseVec:
        model = self._model(language).get()
        e = next(iter(model.query_embed(expand_identifiers(text))))
        return SparseVec([int(i) for i in e.indices], [float(v) for v in e.values])

    async def embed_documents(self, texts: list[str], language: str = "russian") -> list[SparseVec]:
        if not texts:
            return []
        return await asyncio.to_thread(self._docs, texts, language)

    async def embed_query(self, text: str, language: str = "russian") -> SparseVec:
        return await asyncio.to_thread(self._query, text, language)

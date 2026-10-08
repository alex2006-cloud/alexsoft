"""Thin client for apps/rag (`POST /v1/search`) used by the BP1 agent.

Contract: artifacts/api/rag.openapi.yaml. Never raises: every failure becomes a string starting
with "ERROR:", so the LLM can explain it to the user instead of crashing the graph run.
"""
from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_RAG_PORT = "8200"
COLLECTIONS = ("project-docs", "project-code")
MAX_CHUNK_CHARS = 1500
MAX_QUERY_CHARS = 4000
TIMEOUT_S = 20.0


def rag_base_url() -> str:
    url = (os.environ.get("RAG_URL") or "").strip()
    if url:
        return url.rstrip("/")
    port = (os.environ.get("RAG_PORT") or "").strip() or DEFAULT_RAG_PORT
    return f"http://127.0.0.1:{port}"


def _locator_text(locator: dict[str, Any] | None) -> str:
    if not locator:
        return ""
    parts: list[str] = []
    if locator.get("page"):
        parts.append(f"стр. {locator['page']}")
    if locator.get("sheet"):
        rng = f"!{locator['range']}" if locator.get("range") else ""
        parts.append(f"лист {locator['sheet']}{rng}")
    if locator.get("section"):
        parts.append(f"раздел «{locator['section']}»")
    if locator.get("line_start"):
        end = locator.get("line_end")
        parts.append(f"строки {locator['line_start']}-{end}" if end else f"строка {locator['line_start']}")
    if locator.get("symbol"):
        parts.append(f"символ {locator['symbol']}")
    return ", ".join(parts)


def format_chunks(chunks: list[dict[str, Any]]) -> str:
    """Numbered sources the LLM can cite: `[n] path (locator)` followed by the chunk text."""
    if not chunks:
        return "NO_RESULTS: по этому запросу в материалах проекта ничего не найдено."
    blocks: list[str] = []
    for i, ch in enumerate(chunks, 1):
        source = ch.get("external_id") or (ch.get("locator") or {}).get("path") or ch.get("document_id", "?")
        loc = _locator_text(ch.get("locator"))
        head = f"[{i}] {source}" + (f" ({loc})" if loc else "")
        text = (ch.get("text") or "").strip()
        if len(text) > MAX_CHUNK_CHARS:
            text = text[:MAX_CHUNK_CHARS] + " …"
        blocks.append(f"{head}\n{text}")
    return "\n\n".join(blocks)


def search(
    collection: str,
    query: str,
    top_k: int = 5,
    *,
    transport: httpx.BaseTransport | None = None,
) -> str:
    """Hybrid search in a RAG collection; returns formatted sources or an `ERROR:` string."""
    if collection not in COLLECTIONS:
        return f"ERROR: неизвестная коллекция «{collection}», допустимо: {', '.join(COLLECTIONS)}"
    query = (query or "").strip()
    if not query:
        return "ERROR: пустой поисковый запрос"
    api_key = (os.environ.get("RAG_API_KEY") or "").strip()
    if not api_key:
        return "ERROR: RAG_API_KEY не задан, поиск по базе знаний недоступен"
    body = {"collection": collection, "query": query[:MAX_QUERY_CHARS], "top_k": max(1, min(int(top_k), 20))}
    try:
        # trust_env=False: the Windows system proxy would break the loopback call.
        with httpx.Client(base_url=rag_base_url(), timeout=TIMEOUT_S, trust_env=False,
                          transport=transport) as client:
            resp = client.post("/v1/search", json=body, headers={"X-API-Key": api_key})
    except httpx.HTTPError as exc:
        return f"ERROR: сервис RAG недоступен ({type(exc).__name__})"
    if resp.status_code in (401, 403):
        return "ERROR: RAG отклонил ключ доступа (проверь RAG_API_KEY)"
    if resp.status_code == 404:
        return f"ERROR: коллекция «{collection}» не найдена в RAG"
    if resp.status_code >= 400:
        return f"ERROR: RAG вернул HTTP {resp.status_code}"
    try:
        chunks = resp.json().get("chunks") or []
    except ValueError:
        return "ERROR: RAG вернул не-JSON ответ"
    return format_chunks(chunks)

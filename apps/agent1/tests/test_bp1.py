"""Unit tests for the BP1 agent: rag_client (MockTransport) and the graph with a fake LLM."""
from __future__ import annotations

import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import rag_client  # noqa: E402


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.delenv("RAG_URL", raising=False)
    monkeypatch.setenv("RAG_PORT", "8200")


def _transport(status: int = 200, payload: dict | None = None, seen: list | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, json=payload if payload is not None else {})

    return httpx.MockTransport(handler)


CHUNKS = {
    "chunks": [
        {"id": "1", "document_id": "d1", "external_id": "artifacts/adr/0011.md", "text": "LiteLLM — шлюз.",
         "score": 0.9, "locator": {"path": "artifacts/adr/0011.md", "section": "Решение"}},
        {"id": "2", "document_id": "d2", "external_id": "apps/rag/app.py", "text": "def main(): ...",
         "score": 0.5, "locator": {"line_start": 10, "line_end": 20, "symbol": "main"}},
    ]
}


def test_search_formats_sources_and_sends_contract():
    seen: list[httpx.Request] = []
    out = rag_client.search("project-docs", "что такое LiteLLM", 3, transport=_transport(payload=CHUNKS, seen=seen))
    assert "[1] artifacts/adr/0011.md (раздел «Решение»)" in out
    assert "[2] apps/rag/app.py (строки 10-20, символ main)" in out
    req = seen[0]
    assert req.url.path == "/v1/search"
    assert req.headers["x-api-key"] == "test-key"
    assert b'"collection":"project-docs"' in req.content.replace(b" ", b"")
    assert b'"top_k":3' in req.content.replace(b" ", b"")


def test_search_no_results():
    out = rag_client.search("project-code", "xyz", transport=_transport(payload={"chunks": []}))
    assert out.startswith("NO_RESULTS")


def test_search_missing_key(monkeypatch):
    monkeypatch.setenv("RAG_API_KEY", "")
    assert rag_client.search("project-docs", "q").startswith("ERROR:")


@pytest.mark.parametrize("status,needle", [(401, "ключ"), (404, "не найдена"), (500, "HTTP 500")])
def test_search_http_errors(status, needle):
    out = rag_client.search("project-docs", "q", transport=_transport(status))
    assert out.startswith("ERROR:") and needle in out


def test_search_unreachable():
    def boom(request):
        raise httpx.ConnectError("down")

    out = rag_client.search("project-docs", "q", transport=httpx.MockTransport(boom))
    assert out.startswith("ERROR:") and "недоступен" in out


def test_search_validates_input():
    assert rag_client.search("secret-collection", "q").startswith("ERROR:")
    assert rag_client.search("project-docs", "   ").startswith("ERROR:")


def test_graph_calls_tool_and_answers(monkeypatch):
    pytest.importorskip("langgraph")
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage

    import graph_bp1

    calls: list[tuple] = []
    monkeypatch.setattr(rag_client, "search", lambda c, q, k=5, **kw: calls.append((c, q, k)) or "[1] a.md\ntext")

    class FakeLLM(GenericFakeChatModel):
        def bind_tools(self, tools, **kwargs):
            return self

    replies = iter([
        AIMessage(content="", tool_calls=[{"name": "search_project", "id": "c1",
                                           "args": {"query": "как устроен RAG", "collection": "project-docs"}}]),
        AIMessage(content="RAG на LlamaIndex.\n\nИсточники:\n- a.md"),
    ])
    graph_bp1._bound_llm.cache_clear()
    monkeypatch.setattr(graph_bp1, "make_llm", lambda *a, **k: FakeLLM(messages=replies))
    app = graph_bp1.build_graph()
    out = app.invoke({"messages": [{"role": "user", "content": "как устроен RAG?"}]})
    graph_bp1._bound_llm.cache_clear()

    assert calls == [("project-docs", "как устроен RAG", 5)]
    assert "Источники" in out["messages"][-1].content
    assert any(getattr(m, "type", "") == "tool" for m in out["messages"])

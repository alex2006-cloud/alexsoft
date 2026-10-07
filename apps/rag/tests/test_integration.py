"""Integration tests: real Qdrant + PostgreSQL + MinIO, fake LLM/embeddings (no provider keys).

Skipped automatically when the local services are not running.
"""

from __future__ import annotations

import io
import time
import uuid

import pytest
from starlette.testclient import TestClient

from alexsoft_rag.config import Settings
from alexsoft_rag.main import create_app
from alexsoft_rag.services import build_services

from .conftest import FAKE_DIMS, FakeLLM, port_open

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (port_open(5432) and port_open(6333) and port_open(9000)),
        reason="needs local PostgreSQL, Qdrant and MinIO",
    ),
]

KEY = "test-key"
H = {"X-API-Key": KEY}


@pytest.fixture(scope="module")
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture(scope="module")
def client(llm):
    settings = Settings(rag_api_key=KEY, rag_embedding_dimensions=FAKE_DIMS)
    app = create_app(build_services(settings, llm=llm))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def coll(client):
    name = f"t-{uuid.uuid4().hex[:10]}"
    r = client.post("/v1/collections", json={"name": name}, headers=H)
    assert r.status_code == 201, r.text
    yield name
    client.delete(f"/v1/collections/{name}", headers=H)


def wait_job(client, job_id: str, timeout: float = 60.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/v1/jobs/{job_id}", headers=H).json()
        if job["status"] in ("succeeded", "failed"):
            return job
        time.sleep(0.2)
    raise AssertionError(f"job {job_id} did not finish")


def ingest(client, coll, text, external_id=None, metadata=None, **extra):
    body = {"source": {"type": "inline", "text": text, "content_type": "text/markdown"}}
    if external_id:
        body["external_id"] = external_id
    if metadata:
        body["metadata"] = metadata
    body.update(extra)
    r = client.post(f"/v1/collections/{coll}/documents", json=body, headers=H)
    assert r.status_code == 202, r.text
    return r


BROKER = "# Брокер\n\nRabbitMQ — целевой брокер сообщений для долгих AI-задач, этап 6 дорожной карты."
CACHE = "# Кеш\n\nRedis используется как кеш ответов AI на этапе 6, локально стоит Memurai."
VDB = "# Векторная БД\n\nQdrant выбран как векторная база данных для hybrid-поиска RAG."


# ---- auth / health / errors ----------------------------------------------------
def test_health_live_is_open_and_ready_reports_dependencies(client):
    assert client.get("/health/live").json() == {"status": "ok", "dependencies": None}
    r = client.get("/health/ready")
    deps = r.json()["dependencies"]
    assert deps["postgres"] == deps["qdrant"] == deps["minio"] == "ok"
    assert r.status_code == 200


def test_auth_required_and_request_id_echo(client):
    r = client.get("/v1/collections")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["code"] == "unauthorized"
    assert client.get("/v1/collections", headers={"X-API-Key": "nope"}).status_code == 401
    ok = client.get("/v1/collections", headers={**H, "X-Request-Id": "req-123"})
    assert ok.status_code == 200 and ok.headers["X-Request-Id"] == "req-123"
    assert client.get("/health/live").headers["X-Request-Id"]


def test_validation_and_not_found_are_problem_json(client):
    r = client.post("/v1/collections", json={"name": "BAD NAME"}, headers=H)
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "validation_error" and body["errors"][0]["field"]
    assert client.get("/v1/collections/nope-nope", headers=H).status_code == 404
    assert client.post("/v1/search", json={"collection": "nope-nope", "query": "x"}, headers=H).status_code == 404


# ---- storage layer ----------------------------------------------------------------
def test_collection_crud_and_conflict(client):
    name = f"t-{uuid.uuid4().hex[:10]}"
    r = client.post(
        "/v1/collections",
        json={"name": name, "description": "d", "chunking": {"strategy": "sentence", "chunk_size": 128, "chunk_overlap": 8}},
        headers=H,
    )
    assert r.status_code == 201 and r.headers["Location"] == f"/v1/collections/{name}"
    body = r.json()
    assert body["dense_dimensions"] == FAKE_DIMS and body["embedding_model"] == "text-embedding-3-small"
    assert client.post("/v1/collections", json={"name": name}, headers=H).status_code == 409
    assert client.get(f"/v1/collections/{name}", headers=H).json()["chunking"]["strategy"] == "sentence"
    names = [c["name"] for c in client.get("/v1/collections?limit=200", headers=H).json()["items"]]
    assert name in names
    assert client.delete(f"/v1/collections/{name}", headers=H).status_code == 204
    assert client.delete(f"/v1/collections/{name}", headers=H).status_code == 404


def test_collection_pagination_cursor(client):
    names = [f"t-{uuid.uuid4().hex[:10]}" for _ in range(2)]
    try:
        for n in names:
            assert client.post("/v1/collections", json={"name": n}, headers=H).status_code == 201
        page1 = client.get("/v1/collections?limit=1", headers=H).json()
        assert len(page1["items"]) == 1 and page1["next_cursor"]
        page2 = client.get(f"/v1/collections?limit=1&cursor={page1['next_cursor']}", headers=H).json()
        assert page2["items"][0]["name"] != page1["items"][0]["name"]
    finally:
        for n in names:
            client.delete(f"/v1/collections/{n}", headers=H)


# ---- ingest + search ------------------------------------------------------------------
def test_ingest_search_query_roundtrip(client, llm, coll):
    jobs = [
        ingest(client, coll, BROKER, "adr-broker", {"kind": "adr", "lang": "ru"}).json(),
        ingest(client, coll, CACHE, "adr-cache", {"kind": "adr"}).json(),
        ingest(client, coll, VDB, "note-vdb", {"kind": "note"}).json(),
    ]
    for j in jobs:
        done = wait_job(client, j["id"])
        assert done["status"] == "succeeded", done
        assert done["finished_at"]

    docs = client.get(f"/v1/collections/{coll}/documents", headers=H).json()["items"]
    assert {d["external_id"] for d in docs} == {"adr-broker", "adr-cache", "note-vdb"}
    assert all(d["status"] == "indexed" and d["chunks_count"] >= 1 for d in docs)
    info = client.get(f"/v1/collections/{coll}", headers=H).json()
    assert info["documents_count"] == 3 and info["chunks_count"] >= 3

    # hybrid search finds the right document (keywords + dense overlap)
    r = client.post("/v1/search", json={"collection": coll, "query": "какой брокер RabbitMQ", "top_k": 3}, headers=H)
    assert r.status_code == 200, r.text
    chunks = r.json()["chunks"]
    assert chunks[0]["external_id"] == "adr-broker"
    assert 0 < chunks[0]["score"] <= 1
    assert chunks == sorted(chunks, key=lambda c: -c["score"])
    assert set(r.json()["timings_ms"]) >= {"embed", "search", "total"}

    # dbsf fusion also works
    r = client.post("/v1/search", json={"collection": coll, "query": "векторная база Qdrant", "fusion": "dbsf"}, headers=H)
    assert r.json()["chunks"][0]["external_id"] == "note-vdb"

    # metadata filter: scalar and any-of list
    r = client.post("/v1/search", json={"collection": coll, "query": "этап 6", "filter": {"kind": "note"}}, headers=H)
    assert {c["external_id"] for c in r.json()["chunks"]} == {"note-vdb"}
    r = client.post("/v1/search", json={"collection": coll, "query": "этап 6", "filter": {"kind": ["adr"]}}, headers=H)
    assert {c["external_id"] for c in r.json()["chunks"]} <= {"adr-broker", "adr-cache"}

    # score threshold removes weak matches
    r = client.post("/v1/search", json={"collection": coll, "query": "zzz qqq", "score_threshold": 0.99}, headers=H)
    assert r.json()["chunks"] == []

    # grounded answer with citations
    llm.answer = "Выбран RabbitMQ, он нужен на этапе 6 [1]."
    r = client.post("/v1/query", json={"collection": coll, "question": "Какой брокер выбран?", "top_k": 2}, headers=H)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["insufficient_context"] is False and body["answer"].startswith("Выбран RabbitMQ")
    assert body["citations"][0]["chunk_id"] == body["chunks"][0]["id"]
    assert body["usage"]["prompt_tokens"] == 10 and body["model"]
    assert llm.chat_calls[-1]["model"] == "deepseek"
    assert "RabbitMQ" in llm.chat_calls[-1]["messages"][-1]["content"]

    # model says there is no answer -> insufficient_context, no answer
    llm.answer = "INSUFFICIENT_CONTEXT"
    body = client.post("/v1/query", json={"collection": coll, "question": "Что такое Kafka?"}, headers=H).json()
    assert body["insufficient_context"] is True and body["answer"] is None and body["citations"] == []
    llm.answer = "Ответ по контексту [1]."


def test_query_on_empty_filter_result_skips_llm(client, llm, coll):
    ingest(client, coll, BROKER, "adr-broker", {"kind": "adr"})
    # wait for indexing
    deadline = time.time() + 60
    while time.time() < deadline:
        docs = client.get(f"/v1/collections/{coll}/documents", headers=H).json()["items"]
        if docs and docs[0]["status"] == "indexed":
            break
        time.sleep(0.2)
    calls_before = len(llm.chat_calls)
    body = client.post(
        "/v1/query",
        json={"collection": coll, "question": "брокер?", "filter": {"kind": "missing"}},
        headers=H,
    ).json()
    assert body["insufficient_context"] is True and body["answer"] is None and body["chunks"] == []
    assert len(llm.chat_calls) == calls_before


def test_reingest_same_external_id_replaces_chunks(client, coll):
    j1 = ingest(client, coll, BROKER, "doc").json()
    wait_job(client, j1["id"])
    doc1 = client.get(f"/v1/collections/{coll}/documents", headers=H).json()["items"][0]

    j2 = ingest(client, coll, "# Другое\n\nТеперь документ говорит про Grafana Loki и логи.", "doc").json()
    assert wait_job(client, j2["id"])["status"] == "succeeded"
    docs = client.get(f"/v1/collections/{coll}/documents", headers=H).json()["items"]
    assert len(docs) == 1 and docs[0]["id"] == doc1["id"]  # same document row

    old = client.post("/v1/search", json={"collection": coll, "query": "RabbitMQ брокер"}, headers=H).json()["chunks"]
    assert all("RabbitMQ" not in c["text"] for c in old)
    new = client.post("/v1/search", json={"collection": coll, "query": "Grafana Loki"}, headers=H).json()["chunks"]
    assert "Loki" in new[0]["text"]


def test_idempotency_key_returns_same_job(client, coll):
    body = {"external_id": "idem", "source": {"type": "inline", "text": BROKER, "content_type": "text/markdown"}}
    h = {**H, "Idempotency-Key": "key-1"}
    a = client.post(f"/v1/collections/{coll}/documents", json=body, headers=h)
    b = client.post(f"/v1/collections/{coll}/documents", json=body, headers=h)
    assert a.status_code == b.status_code == 202
    assert a.json()["id"] == b.json()["id"] and a.headers["Location"].endswith(a.json()["id"])
    wait_job(client, a.json()["id"])


def test_delete_document_removes_its_chunks(client, coll):
    j = ingest(client, coll, BROKER, "to-delete").json()
    wait_job(client, j["id"])
    doc = client.get(f"/v1/collections/{coll}/documents", headers=H).json()["items"][0]
    assert client.get(f"/v1/collections/{coll}/documents/{doc['id']}", headers=H).json()["status"] == "indexed"
    assert client.delete(f"/v1/collections/{coll}/documents/{doc['id']}", headers=H).status_code == 204
    assert client.get(f"/v1/collections/{coll}/documents/{doc['id']}", headers=H).status_code == 404
    assert client.post("/v1/search", json={"collection": coll, "query": "RabbitMQ"}, headers=H).json()["chunks"] == []


def test_status_filter_and_missing_collection_on_documents(client, coll):
    assert client.get(f"/v1/collections/{coll}/documents?status=failed", headers=H).json()["items"] == []
    assert client.get("/v1/collections/nope-nope/documents", headers=H).status_code == 404
    r = client.post("/v1/collections/nope-nope/documents", json={"source": {"type": "inline", "text": "x"}}, headers=H)
    assert r.status_code == 404


def test_payload_too_large_and_bad_source(client, coll):
    settings = client.app.state.services.settings
    big = "x" * (settings.rag_max_document_chars + 1)
    r = client.post(f"/v1/collections/{coll}/documents", json={"source": {"type": "inline", "text": big}}, headers=H)
    assert r.status_code == 413 and r.json()["code"] == "payload_too_large"
    r = client.post(
        f"/v1/collections/{coll}/documents",
        json={"source": {"type": "inline", "text": "x"}, "unknown": 1},
        headers=H,
    )
    assert r.status_code == 422


def test_unknown_job_is_404(client):
    assert client.get(f"/v1/jobs/{uuid.uuid4()}", headers=H).status_code == 404


# ---- MinIO source -----------------------------------------------------------------------
def test_minio_source_ingest_and_failures(client, coll):
    store = client.app.state.services.objects
    key = f"it/{uuid.uuid4().hex}.md"
    data = BROKER.encode()
    store._client.put_object(store.default_bucket, key, io.BytesIO(data), len(data))
    try:
        j = ingest_raw(client, coll, {"type": "minio", "bucket": store.default_bucket, "key": key}, "from-minio")
        assert wait_job(client, j["id"])["status"] == "succeeded"
        hit = client.post("/v1/search", json={"collection": coll, "query": "RabbitMQ"}, headers=H).json()["chunks"][0]
        assert hit["external_id"] == "from-minio"

        j = ingest_raw(client, coll, {"type": "minio", "bucket": store.default_bucket, "key": "it/missing.md"}, "gone")
        done = wait_job(client, j["id"])
        assert done["status"] == "failed" and "not_found" in done["error"]
        gone = [d for d in client.get(f"/v1/collections/{coll}/documents?status=failed", headers=H).json()["items"]]
        assert gone and gone[0]["error"]

        j = ingest_raw(client, coll, {"type": "minio", "bucket": store.default_bucket, "key": "it/file.pdf"}, "pdf")
        assert wait_job(client, j["id"])["status"] == "failed"
    finally:
        store._client.remove_object(store.default_bucket, key)


def ingest_raw(client, coll, source, external_id):
    r = client.post(
        f"/v1/collections/{coll}/documents", json={"source": source, "external_id": external_id}, headers=H
    )
    assert r.status_code == 202, r.text
    return r.json()


# ---- multi-format ingest (ADR-0018) ------------------------------------------------------
def put_object(client, key: str, data: bytes) -> dict:
    store = client.app.state.services.objects
    store._client.put_object(store.default_bucket, key, io.BytesIO(data), len(data))
    return {"type": "minio", "bucket": store.default_bucket, "key": key}


def test_multiformat_documents_have_locators(client, llm):
    from .test_parsers import DRAWIO, PY, make_mixed_pdf, make_xlsx

    name = f"t-{uuid.uuid4().hex[:10]}"
    assert client.post("/v1/collections", json={"name": name, "sparse_language": "english"}, headers=H).status_code == 201
    got = client.get(f"/v1/collections/{name}", headers=H).json()
    assert got["sparse_language"] == "english"
    prefix = f"it/{uuid.uuid4().hex}"
    keys = []
    try:
        files = {
            "pnl.xlsx": make_xlsx(),
            "scan.pdf": make_mixed_pdf(),
            "svc.py": PY.encode(),
            "arch.drawio": DRAWIO.encode(),
        }
        for fname, data in files.items():
            key = f"{prefix}/{fname}"
            keys.append(key)
            job = ingest_raw(client, name, put_object(client, key, data), key)
            done = wait_job(client, job["id"])
            assert done["status"] == "succeeded", (fname, done)

        def search(q, **kw):
            r = client.post("/v1/search", json={"collection": name, "query": q, "top_k": 5, **kw}, headers=H)
            assert r.status_code == 200, r.text
            return r.json()["chunks"]

        xlsx_hit = next(c for c in search("Статья 7 Q1 Q2 Итого") if c["external_id"].endswith("pnl.xlsx"))
        assert xlsx_hit["locator"]["sheet"] == "Бюджет" and xlsx_hit["locator"]["range"].startswith("A")
        assert xlsx_hit["locator"]["path"].endswith("pnl.xlsx")

        pdf_hits = [c for c in search("RabbitMQ broker long running AI tasks") if c["external_id"].endswith("scan.pdf")]
        assert pdf_hits and pdf_hits[0]["locator"]["page"] == 1

        code_hit = next(c for c in search("embed_query method of Service class") if c["external_id"].endswith("svc.py"))
        loc = code_hit["locator"]
        assert loc["line_start"] >= 1 and loc["line_end"] >= loc["line_start"]
        assert "Service" in loc.get("symbol", "") or "alpha" in loc.get("symbol", "")

        diagram_hit = next(c for c in search("LangGraph LiteLLM chat связи") if c["external_id"].endswith("arch.drawio"))
        assert "LangGraph" in diagram_hit["text"] and diagram_hit["locator"]["section"] == "Target"
    finally:
        client.delete(f"/v1/collections/{name}", headers=H)
        store = client.app.state.services.objects
        for key in keys:
            store._client.remove_object(store.default_bucket, key)


def test_unchanged_content_hash_skips_reindexing(client, coll, llm):
    first = client.post(
        f"/v1/collections/{coll}/documents",
        json={"source": {"type": "inline", "text": BROKER}, "external_id": "doc-h", "content_hash": "h1"},
        headers=H,
    ).json()
    assert wait_job(client, first["id"])["status"] == "succeeded"
    calls = llm.embed_calls

    again = client.post(
        f"/v1/collections/{coll}/documents",
        json={"source": {"type": "inline", "text": BROKER}, "external_id": "doc-h", "content_hash": "h1"},
        headers=H,
    ).json()
    assert again["status"] == "succeeded" and again["id"] != first["id"]  # nothing to do
    assert llm.embed_calls == calls

    changed = client.post(
        f"/v1/collections/{coll}/documents",
        json={"source": {"type": "inline", "text": BROKER + "\n\nещё"}, "external_id": "doc-h", "content_hash": "h2"},
        headers=H,
    ).json()
    assert wait_job(client, changed["id"])["status"] == "succeeded"
    assert llm.embed_calls > calls
    docs = client.get(f"/v1/collections/{coll}/documents", headers=H).json()["items"]
    assert len(docs) == 1 and docs[0]["content_hash"] == "h2"

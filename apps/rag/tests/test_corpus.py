"""Regression on the real project corpus (chunking + BM25 + pipeline + hybrid), fake dense embeddings.

This does NOT measure production quality (dense is a hashing stand-in); use eval/run_eval.py against
the live service with text-embedding-3-small for that. Here it guards the lexical/hybrid path.
"""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

import pytest
import yaml
from starlette.testclient import TestClient

from alexsoft_rag.config import REPO_ROOT, Settings
from alexsoft_rag.main import create_app
from alexsoft_rag.services import build_services

from .conftest import FAKE_DIMS, FakeLLM, port_open

sys.path.insert(0, str(REPO_ROOT / "infra" / "rag"))
from seed_corpus import collect, kind_of  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (port_open(5432) and port_open(6333) and port_open(9000)),
        reason="needs local PostgreSQL, Qdrant and MinIO",
    ),
]

H = {"X-API-Key": "test-key"}
QUESTIONS = yaml.safe_load((Path(__file__).parents[1] / "eval" / "questions.yaml").read_text(encoding="utf-8"))
MIN_HIT_AT_5 = 0.7


def test_corpus_hit_rate_with_hybrid_search():
    settings = Settings(rag_api_key="test-key", rag_embedding_dimensions=FAKE_DIMS)
    app = create_app(build_services(settings, llm=FakeLLM()))
    name = f"corpus-{uuid.uuid4().hex[:8]}"
    with TestClient(app) as c:
        assert c.post("/v1/collections", json={"name": name}, headers=H).status_code == 201
        try:
            files = collect(REPO_ROOT)
            assert len(files) > 20
            jobs = []
            for p in files:
                rel = p.relative_to(REPO_ROOT).as_posix()
                r = c.post(
                    f"/v1/collections/{name}/documents",
                    json={
                        "external_id": rel,
                        "source": {"type": "inline", "text": p.read_text(encoding="utf-8"), "content_type": "text/markdown"},
                        "metadata": {"kind": kind_of(rel), "lang": "ru"},
                    },
                    headers=H,
                )
                assert r.status_code == 202, r.text
                jobs.append(r.json()["id"])

            deadline = time.time() + 300
            for jid in jobs:
                while True:
                    job = c.get(f"/v1/jobs/{jid}", headers=H).json()
                    if job["status"] in ("succeeded", "failed"):
                        break
                    assert time.time() < deadline, "ingest timed out"
                    time.sleep(0.3)
                assert job["status"] == "succeeded", job

            info = c.get(f"/v1/collections/{name}", headers=H).json()
            assert info["documents_count"] == len(files) and info["chunks_count"] > len(files)

            hits = total = 0
            misses = []
            for item in QUESTIONS["questions"]:
                if item.get("answerable") is False or item.get("seed") is False:
                    continue  # seed: false = needs the full kb-sync (PDF/Excel/code), not this minimal corpus
                total += 1
                chunks = c.post(
                    "/v1/search", json={"collection": name, "query": item["q"], "top_k": 5}, headers=H
                ).json()["chunks"]
                if any(e in (ch["external_id"] or "") for ch in chunks for e in item["expect_any"]):
                    hits += 1
                else:
                    misses.append(item["q"])
            assert hits / total >= MIN_HIT_AT_5, f"hit@5 {hits}/{total}; misses: {misses}"
        finally:
            c.delete(f"/v1/collections/{name}", headers=H)

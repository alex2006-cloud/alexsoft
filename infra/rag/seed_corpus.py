"""Seed the RAG corpus: upload project docs to MinIO (bucket rag-docs) and ingest them via the RAG API.

Run (RAG service + Qdrant + MinIO + LiteLLM with embeddings must be up):
    powershell -ExecutionPolicy Bypass -File infra\\rag\\seed-corpus.ps1
Idempotent: documents are keyed by `external_id` = repo-relative path, re-running replaces chunks.
"""

from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

import httpx
from minio import Minio

from alexsoft_rag.config import REPO_ROOT, get_settings

CORPUS_GLOBS = [
    "CONCEPT.md",
    "ROADMAP.md",
    "README.md",
    "AGENTS.md",
    "artifacts/README.md",
    "artifacts/adr/*.md",
    "artifacts/business-cases/bc1/*.md",
    "apps/*/README.md",
    "infra/README.md",
    "infra/*/README.md",
]
EXCLUDE = {"artifacts/adr/0000-template.md"}


def kind_of(rel: str) -> str:
    if rel.startswith("artifacts/adr/"):
        return "adr"
    if rel.startswith("artifacts/business-cases/"):
        return "business-case"
    if rel in {"CONCEPT.md", "ROADMAP.md", "AGENTS.md"}:
        return rel.removesuffix(".md").lower()
    if rel.endswith("README.md"):
        return "readme"
    return "doc"


def collect(root: Path) -> list[Path]:
    seen: dict[str, Path] = {}
    for pattern in CORPUS_GLOBS:
        for p in sorted(root.glob(pattern)):
            rel = p.relative_to(root).as_posix()
            if p.is_file() and rel not in EXCLUDE:
                seen[rel] = p
    return list(seen.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--collection", default="project-docs")
    ap.add_argument("--prefix", default="project", help="MinIO key prefix")
    ap.add_argument("--api", default=None, help="RAG base URL (default http://127.0.0.1:RAG_PORT)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    s = get_settings()
    base = args.api or f"http://127.0.0.1:{s.rag_port}"
    files = collect(REPO_ROOT)
    print(f"Corpus: {len(files)} files -> s3://{s.rag_minio_bucket}/{args.prefix}/ -> collection {args.collection}")
    if args.dry_run:
        for p in files:
            print("  ", p.relative_to(REPO_ROOT).as_posix())
        return 0

    mc = Minio(s.minio_hostport, access_key=s.minio_root_user, secret_key=s.minio_root_password, secure=False)
    if not mc.bucket_exists(s.rag_minio_bucket):
        mc.make_bucket(s.rag_minio_bucket)

    http = httpx.Client(
        base_url=base, headers={"X-API-Key": s.rag_api_key}, timeout=60, trust_env=False
    )
    r = http.post("/v1/collections", json={"name": args.collection, "description": "Документация проекта alexsoft"})
    if r.status_code == 201:
        print(f"Created collection {args.collection}")
    elif r.status_code != 409:
        print("create collection failed:", r.status_code, r.text)
        return 1

    jobs: list[tuple[str, str]] = []
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        data = p.read_bytes()
        key = f"{args.prefix}/{rel}"
        mc.put_object(s.rag_minio_bucket, key, io.BytesIO(data), len(data), content_type="text/markdown")
        r = http.post(
            f"/v1/collections/{args.collection}/documents",
            json={
                "external_id": rel,
                "source": {"type": "minio", "bucket": s.rag_minio_bucket, "key": key},
                "metadata": {"kind": kind_of(rel), "lang": "ru", "path": rel},
            },
        )
        if r.status_code != 202:
            print(f"  FAIL {rel}: {r.status_code} {r.text[:200]}")
            return 1
        jobs.append((rel, r.json()["id"]))
        print(f"  queued {rel}")

    failed = 0
    pending = dict(jobs)
    deadline = time.time() + 600
    ok = 0
    while pending and time.time() < deadline:
        for rel, jid in list(pending.items()):
            job = http.get(f"/v1/jobs/{jid}").json()
            if job["status"] == "succeeded":
                ok += 1
                pending.pop(rel)
            elif job["status"] == "failed":
                failed += 1
                pending.pop(rel)
                print(f"  FAILED {rel}: {job.get('error')}")
        time.sleep(1)
    info = http.get(f"/v1/collections/{args.collection}").json()
    print(f"Done: {ok} indexed, {failed} failed, {len(pending)} timed out. "
          f"Collection: {info['documents_count']} docs, {info['chunks_count']} chunks")
    return 0 if failed == 0 and not pending else 1


if __name__ == "__main__":
    sys.exit(main())

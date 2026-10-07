"""kb-sync runner: repo files -> MinIO -> RAG API (idempotent, incremental by content hash)."""

from __future__ import annotations

import hashlib
import io
import posixpath
import subprocess
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from minio import Minio

from ..config import Settings
from .config import CollectionRule, SyncConfig
from .rules import find_secret, is_secret_name, match_any
from .summaries import Summarizer

IGNORE_MARKER = "kb-sync: ignore-secrets"
BINARY_EXT = {".pdf", ".xlsx"}
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".md": "text/markdown",
}
CODE_LANG = {
    ".py": "python", ".ts": "typescript", ".tsx": "tsx", ".js": "javascript", ".jsx": "javascript",
    ".mjs": "javascript", ".ps1": "powershell", ".sql": "sql", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".json": "json", ".conf": "nginx", ".sh": "shell", ".dsl": "structurizr",
    ".puml": "plantuml",
}


@dataclass
class Item:
    external_id: str
    collection: str
    metadata: dict[str, Any]
    data: bytes | None  # None = already indexed, only keep it (no re-upload)
    content_type: str = "text/plain"
    content_hash: str | None = None


@dataclass
class Plan:
    items: list[Item] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (path, reason)
    flagged: list[tuple[str, str]] = field(default_factory=list)  # (path, secret reason)


def git_files(root: Path) -> list[str]:
    """Tracked + untracked-but-not-ignored files (so brand new docs are picked up before commit)."""
    out: set[str] = set()
    for args in (["ls-files", "-z"], ["ls-files", "-z", "--others", "--exclude-standard"]):
        res = subprocess.run(["git", *args], cwd=root, capture_output=True, check=True)
        out.update(p for p in res.stdout.decode("utf-8", "replace").split("\0") if p)
    return sorted(p for p in out if (root / p).is_file())


def kind_for(rel: str, cfg: SyncConfig, rule: CollectionRule) -> str:
    for glob, kind in cfg.kinds:
        if match_any(rel, [glob]):
            return kind
    return "code" if rule.name.endswith("code") else "doc"


def build_plan(cfg: SyncConfig, root: Path, files: list[str], *, only: list[str] | None = None) -> Plan:
    plan = Plan()
    for rel in files:
        ext = posixpath.splitext(rel.lower())[1]
        if only and not match_any(rel, only):
            continue
        if match_any(rel, cfg.exclude):
            plan.skipped.append((rel, "excluded"))
            continue
        if is_secret_name(rel):  # before routing: a tracked `.env` must be loud, not "not routed"
            plan.flagged.append((rel, "secret file name"))
            continue
        rule = next((c for c in cfg.collections if match_any(rel, c.include)), None)
        if rule is None:
            plan.skipped.append((rel, "not routed"))
            continue
        path = root / rel
        try:
            size = path.stat().st_size
            limit = cfg.max_binary_bytes if ext in BINARY_EXT else cfg.max_text_bytes
            if size == 0:
                plan.skipped.append((rel, "empty"))
                continue
            if size > limit:
                plan.skipped.append((rel, f"too large ({size // 1024} KB)"))
                continue
            data = path.read_bytes()
        except OSError as e:
            plan.skipped.append((rel, f"unreadable ({e.__class__.__name__})"))
            continue
        if ext not in BINARY_EXT:
            text = data.decode("utf-8", "replace")
            # opt-out for files that contain fake secrets on purpose (scanner tests)
            reason = None if IGNORE_MARKER in text else find_secret(text)
            if reason:
                plan.flagged.append((rel, reason))
                continue
        meta: dict[str, Any] = {
            "kind": kind_for(rel, cfg, rule),
            "path": rel,
            "area": "/".join(rel.split("/")[:2]) if "/" in rel else "root",
            "ext": ext.lstrip("."),
        }
        if ext in CODE_LANG and rule.name.endswith("code"):
            meta["lang"] = CODE_LANG[ext]
        plan.items.append(
            Item(
                external_id=rel,
                collection=rule.name,
                metadata=meta,
                data=data,
                content_type=CONTENT_TYPES.get(ext, "text/plain"),
                content_hash=hashlib.sha256(data).hexdigest(),
            )
        )
    return plan


class KbSync:
    def __init__(
        self,
        cfg: SyncConfig,
        settings: Settings,
        root: Path,
        api_base: str,
        *,
        http: httpx.Client | None = None,
        minio: Minio | None = None,
    ) -> None:
        self.cfg = cfg
        self.s = settings
        self.root = root
        self.http = http or httpx.Client(
            base_url=api_base, headers={"X-API-Key": settings.rag_api_key}, timeout=60, trust_env=False
        )
        self.minio = minio or Minio(
            settings.minio_hostport,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=settings.minio_secure,
        )

    # ---- remote state -------------------------------------------------------------------------
    def ensure_collections(self, names: set[str]) -> None:
        for rule in self.cfg.collections:
            if rule.name not in names:
                continue
            body: dict[str, Any] = {
                "name": rule.name,
                "description": rule.description,
                "sparse_language": rule.sparse_language,
            }
            if rule.chunking:
                body["chunking"] = rule.chunking
            r = self.http.post("/v1/collections", json=body)
            if r.status_code == 201:
                print(f"  created collection {rule.name} (sparse_language={rule.sparse_language})")
            elif r.status_code != 409:
                raise RuntimeError(f"create collection {rule.name}: HTTP {r.status_code} {r.text[:300]}")

    def remote_documents(self, collection: str) -> dict[str, dict[str, Any]]:
        docs: dict[str, dict[str, Any]] = {}
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {"limit": 200}
            if cursor:
                params["cursor"] = cursor
            r = self.http.get(f"/v1/collections/{collection}/documents", params=params)
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            page = r.json()
            for d in page["items"]:
                if d.get("external_id"):
                    docs[d["external_id"]] = d
            cursor = page.get("next_cursor")
            if not cursor:
                return docs

    # ---- summaries -----------------------------------------------------------------------------
    def add_summaries(self, plan: Plan, remote: dict[str, dict[str, dict[str, Any]]], *, dry_run: bool) -> Counter:
        rule = self.cfg.summaries
        stats: Counter = Counter()
        if not rule.enabled:
            return stats
        eligible = [
            it
            for it in plan.items
            if it.collection == rule.collection
            and it.data is not None
            and match_any(it.external_id, rule.include)
            and not match_any(it.external_id, rule.exclude)
            and it.data.count(b"\n") + 1 >= rule.min_lines
        ]
        stats["eligible"] = len(eligible)
        if dry_run or not eligible:
            return stats

        summarizer = Summarizer(
            self.s.ai_gateway_url, self.s.litellm_master_key, rule.model, max_file_bytes=rule.max_file_bytes
        )
        known = remote.get(rule.collection, {})

        def work(it: Item) -> Item | None:
            sid = f"summary/{it.external_id}.md"
            meta = {"kind": "code-summary", "path": it.external_id, "src_hash": it.content_hash,
                    "area": it.metadata.get("area"), "ext": "md"}
            have = known.get(sid)
            if have and have.get("status") == "indexed" and (have.get("metadata") or {}).get("src_hash") == it.content_hash:
                stats["summary_current"] += 1
                return Item(sid, rule.collection, meta, None, "text/markdown", have.get("content_hash"))
            try:
                text, cached = summarizer.summarize(it.external_id, it.data or b"")
            except Exception as e:  # noqa: BLE001 - one failed summary must not stop the sync
                stats["summary_failed"] += 1
                print(f"  ! summary failed for {it.external_id}: {e}")
                if have:  # keep the previous one rather than deleting it
                    return Item(sid, rule.collection, meta, None, "text/markdown", have.get("content_hash"))
                return None
            stats["summary_cached" if cached else "summary_generated"] += 1
            data = text.encode("utf-8")
            return Item(sid, rule.collection, meta, data, "text/markdown", hashlib.sha256(data).hexdigest())

        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                for result in pool.map(work, eligible):
                    if result is not None:
                        plan.items.append(result)
        finally:
            summarizer.close()
        return stats

    # ---- sync ------------------------------------------------------------------------------------
    def sync(self, plan: Plan, remote: dict[str, dict[str, dict[str, Any]]], *, delete: bool, force: bool) -> int:
        bucket = self.s.rag_minio_bucket
        if not self.minio.bucket_exists(bucket):
            self.minio.make_bucket(bucket)

        stats: Counter = Counter()
        jobs: dict[str, str] = {}  # external_id@collection -> job id
        wanted: dict[str, set[str]] = {}
        for it in plan.items:
            wanted.setdefault(it.collection, set()).add(it.external_id)
            doc = remote.get(it.collection, {}).get(it.external_id)
            unchanged = (
                doc is not None
                and doc.get("status") == "indexed"
                and (it.data is None or doc.get("content_hash") == it.content_hash)
                and (doc.get("metadata") or {}) == it.metadata
            )
            if unchanged and not force:
                stats["unchanged"] += 1
                continue
            if it.data is None:  # kept as is, but its metadata changed
                stats["unchanged"] += 1
                continue
            key = f"{self.cfg.minio_prefix}/{it.external_id}"
            self.minio.put_object(bucket, key, io.BytesIO(it.data), len(it.data), content_type=it.content_type)
            r = self.http.post(
                f"/v1/collections/{it.collection}/documents",
                json={
                    "external_id": it.external_id,
                    "source": {"type": "minio", "bucket": bucket, "key": key, "content_type": it.content_type},
                    "metadata": it.metadata,
                    "content_hash": it.content_hash,
                },
            )
            if r.status_code != 202:
                stats["failed"] += 1
                print(f"  FAIL {it.collection}:{it.external_id}: HTTP {r.status_code} {r.text[:200]}")
                continue
            stats["new" if doc is None else "updated"] += 1
            jobs[f"{it.collection}:{it.external_id}"] = r.json()["id"]

        if delete:
            for collection, docs in remote.items():
                if collection not in wanted:
                    continue
                for ext_id, doc in docs.items():
                    if ext_id not in wanted[collection]:
                        self.http.delete(f"/v1/collections/{collection}/documents/{doc['id']}")
                        self.minio_remove(bucket, f"{self.cfg.minio_prefix}/{ext_id}")
                        stats["deleted"] += 1

        failed = self.wait_jobs(jobs, stats)
        print("  " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
        return failed + stats["failed"]

    def minio_remove(self, bucket: str, key: str) -> None:
        try:
            self.minio.remove_object(bucket, key)
        except Exception:  # noqa: BLE001 - orphan object is harmless
            pass

    def wait_jobs(self, jobs: dict[str, str], stats: Counter, *, timeout_s: int = 3600) -> int:
        pending = dict(jobs)
        deadline = time.time() + timeout_s
        failed = 0
        last_report = time.time()
        while pending and time.time() < deadline:
            for name, jid in list(pending.items()):
                job = self.http.get(f"/v1/jobs/{jid}").json()
                if job["status"] == "succeeded":
                    pending.pop(name)
                    stats["indexed"] += 1
                elif job["status"] == "failed":
                    pending.pop(name)
                    failed += 1
                    print(f"  FAILED {name}: {job.get('error')}")
            if pending and time.time() - last_report > 15:
                print(f"  ... {len(jobs) - len(pending)}/{len(jobs)} jobs done")
                last_report = time.time()
            if pending:
                time.sleep(1)
        if pending:
            print(f"  TIMEOUT: {len(pending)} job(s) still running: {list(pending)[:5]}")
        return failed + len(pending)

    def close(self) -> None:
        self.http.close()

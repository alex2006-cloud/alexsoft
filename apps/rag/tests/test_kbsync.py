"""kb-sync: file selection, glob rules and the secret guard. No services needed.

This file contains fake secrets on purpose, hence the marker for the scanner:
kb-sync: ignore-secrets
"""

from __future__ import annotations

from pathlib import Path

import pytest

from alexsoft_rag.kbsync.config import CollectionRule, SyncConfig, SummaryRule, load_config
from alexsoft_rag.kbsync.rules import find_secret, is_secret_name, match_glob
from alexsoft_rag.kbsync.runner import build_plan
from alexsoft_rag.kbsync.summaries import cache_key, summary_text


@pytest.mark.parametrize(
    "path,pattern,expected",
    [
        ("README.md", "*.md", True),
        ("apps/rag/README.md", "*.md", True),  # no slash: file name at any depth
        ("apps/rag/README.md", "**/README.md", True),
        ("README.md", "**/README.md", True),
        ("apps/rag/a/b.py", "apps/**/*.py", True),
        ("apps/b.py", "apps/**/*.py", True),
        ("infra/b.py", "apps/**/*.py", False),
        ("artifacts/adr/0001.md", "artifacts/adr/*.md", True),
        ("artifacts/adr/sub/0001.md", "artifacts/adr/*.md", False),
        ("a/node_modules/x/y.js", "**/node_modules/**", True),
        ("A.PDF", "*.pdf", True),
    ],
)
def test_match_glob(path, pattern, expected):
    assert match_glob(path, pattern) is expected


@pytest.mark.parametrize(
    "name,secret",
    [
        (".env", True), (".env.local", True), ("apps/x/.env.production", True), (".env.example", False),
        ("certs/server.pem", True), ("id_rsa", True), ("credentials.json", True), ("dump.sql", False),
        ("data.sqlite", True), ("README.md", False),
    ],
)
def test_secret_file_names(name, secret):
    assert is_secret_name(name) is secret


def test_secret_content_detection():
    assert find_secret("OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz0123456789")
    assert find_secret("-----BEGIN RSA PRIVATE KEY-----\nMIIE")
    assert find_secret("key = AKIAABCDEFGHIJKLMNOP")
    assert find_secret('password = "Zx9fQ2mK7vLp3Rt8Yw"')
    assert find_secret("api_key: 4f9a8c1d7e2b6a05c3d9e8f7a1b2c3d4")


def test_secret_scanner_ignores_placeholders_and_identifiers():
    clean = [
        "OPENAI_API_KEY=",
        "LITELLM_MASTER_KEY=sk-change-me",
        "password = settings.rag_api_key",
        "token = os.environ['RAG_API_KEY_VALUE']",
        'api_key="your_api_key_here_1234"',
        "api_key: ${OPENAI_API_KEY}",
        "RAG_API_KEY=change_me_please_123",
        "secret_name = some_long_identifier_name",
        "see sk-REDACTED in the logs",
        "password: <password>",
    ]
    for text in clean:
        assert find_secret(text) is None, text


def _cfg() -> SyncConfig:
    return SyncConfig(
        minio_prefix="kb",
        exclude=["**/node_modules/**", "*.lock"],
        max_text_bytes=1000,
        max_binary_bytes=10_000,
        collections=[
            CollectionRule("project-docs", "", "russian", ["*.md", "*.xlsx"]),
            CollectionRule("project-code", "", "english", ["*.py", "*.yaml"]),
        ],
        kinds=[("**/README.md", "readme"), ("**/tests/**", "test")],
        summaries=SummaryRule(),
    )


def test_build_plan_routes_skips_and_flags(tmp_path: Path):
    files = {
        "README.md": b"# Hi\n",
        "apps/a/README.md": b"# A\n",
        "apps/a/main.py": b"print('x')\n",
        "apps/a/tests/test_x.py": b"def test_x(): pass\n",
        "apps/a/node_modules/dep/i.py": b"x = 1\n",
        "apps/a/leak.py": b'API_KEY = "Zx9fQ2mK7vLp3Rt8YwQ1"\n',
        "apps/a/.env": b"A=1\n",
        "apps/a/big.py": b"x = 1\n" * 500,
        "apps/a/empty.py": b"",
        "apps/a/pic.png": b"\x89PNG",
        "poetry.lock": b"x",
        "table.xlsx": b"PK\x03\x04binary-with-sk-abcdefghijklmnopqrstuvwxyz",  # binary: not scanned
    }
    for rel, data in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    plan = build_plan(_cfg(), tmp_path, sorted(files))
    by_id = {i.external_id: i for i in plan.items}

    assert set(by_id) == {"README.md", "apps/a/README.md", "apps/a/main.py", "apps/a/tests/test_x.py", "table.xlsx"}
    assert by_id["README.md"].collection == "project-docs" and by_id["README.md"].metadata["kind"] == "readme"
    assert by_id["apps/a/main.py"].collection == "project-code"
    assert by_id["apps/a/main.py"].metadata["kind"] == "code" and by_id["apps/a/main.py"].metadata["lang"] == "python"
    assert by_id["apps/a/tests/test_x.py"].metadata["kind"] == "test"
    assert by_id["table.xlsx"].metadata["kind"] == "doc"
    assert by_id["README.md"].content_hash and len(by_id["README.md"].content_hash) == 64

    flagged = dict(plan.flagged)
    assert set(flagged) == {"apps/a/leak.py", "apps/a/.env"}  # never indexed
    reasons = dict(plan.skipped)
    assert reasons["apps/a/node_modules/dep/i.py"] == "excluded"
    assert reasons["poetry.lock"] == "excluded"
    assert reasons["apps/a/empty.py"] == "empty"
    assert reasons["apps/a/big.py"].startswith("too large")
    assert reasons["apps/a/pic.png"] == "not routed"


def test_build_plan_only_filter(tmp_path: Path):
    (tmp_path / "a.md").write_text("# a")
    (tmp_path / "b.md").write_text("# b")
    plan = build_plan(_cfg(), tmp_path, ["a.md", "b.md"], only=["a.md"])
    assert [i.external_id for i in plan.items] == ["a.md"]


class FakeMinio:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def bucket_exists(self, bucket):
        return True

    def put_object(self, bucket, key, stream, length, content_type=None):
        self.objects[key] = stream.read()

    def remove_object(self, bucket, key):
        self.objects.pop(key, None)


def _sync_env(remote_docs: dict[str, dict]):
    """KbSync wired to a mock RAG API; returns (sync, posted ingests, deleted ids)."""
    import httpx

    from alexsoft_rag.config import Settings
    from alexsoft_rag.kbsync.runner import KbSync

    posted: list[dict] = []
    deleted: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path.endswith("/documents"):
            import json

            posted.append(json.loads(request.content))
            return httpx.Response(202, json={"id": f"job-{len(posted)}"})
        if request.method == "GET" and path.startswith("/v1/jobs/"):
            return httpx.Response(200, json={"status": "succeeded"})
        if request.method == "DELETE":
            deleted.append(path.rsplit("/", 1)[-1])
            return httpx.Response(204)
        return httpx.Response(404)

    http = httpx.Client(base_url="http://rag", transport=httpx.MockTransport(handler))
    sync = KbSync(_cfg(), Settings(), Path("."), "http://rag", http=http, minio=FakeMinio())
    return sync, posted, deleted


def test_sync_is_incremental_and_deletes_vanished(tmp_path: Path):
    (tmp_path / "a.md").write_text("# a", encoding="utf-8")
    (tmp_path / "b.md").write_text("# b", encoding="utf-8")
    plan = build_plan(_cfg(), tmp_path, ["a.md", "b.md"])
    a = next(i for i in plan.items if i.external_id == "a.md")

    remote = {
        "project-docs": {
            # a.md: same hash + metadata -> unchanged; gone.md: no longer in the repo -> deleted
            "a.md": {"id": "id-a", "status": "indexed", "content_hash": a.content_hash, "metadata": a.metadata},
            "gone.md": {"id": "id-gone", "status": "indexed", "content_hash": "x", "metadata": {}},
        },
        "project-code": {},
    }
    sync, posted, deleted = _sync_env(remote)
    failed = sync.sync(plan, remote, delete=True, force=False)

    assert failed == 0
    assert [p["external_id"] for p in posted] == ["b.md"]  # only the new file is ingested
    assert posted[0]["content_hash"] == next(i for i in plan.items if i.external_id == "b.md").content_hash
    assert posted[0]["source"]["key"] == "kb/b.md" and posted[0]["metadata"]["kind"] == "doc"
    assert deleted == ["id-gone"]
    assert sync.minio.objects == {"kb/b.md": b"# b"}

    # a changed file is re-ingested; --force re-ingests everything
    (tmp_path / "a.md").write_text("# a v2", encoding="utf-8")
    plan2 = build_plan(_cfg(), tmp_path, ["a.md", "b.md"])
    sync2, posted2, _ = _sync_env(remote)
    sync2.sync(plan2, remote, delete=False, force=False)
    assert [p["external_id"] for p in posted2] == ["a.md", "b.md"]  # b.md is not in `remote`
    sync3, posted3, _ = _sync_env(remote)
    sync3.sync(plan, remote, delete=False, force=True)
    assert [p["external_id"] for p in posted3] == ["a.md", "b.md"]


def test_real_sources_yaml_loads():
    cfg = load_config()
    names = [c.name for c in cfg.collections]
    assert names == ["project-docs", "project-code"]
    assert {c.sparse_language for c in cfg.collections} == {"russian", "english"}
    assert cfg.summaries.enabled and cfg.summaries.collection == "project-code"


def test_eval_questions_are_well_formed():
    import yaml

    cfg = load_config()
    known = {c.name for c in cfg.collections}
    data = yaml.safe_load((Path(__file__).parents[1] / "eval" / "questions.yaml").read_text(encoding="utf-8"))
    questions = data["questions"]
    assert any(q.get("collection") == "project-code" for q in questions)
    for q in questions:
        assert q["q"].strip()
        assert q.get("collection", "project-docs") in known
        if q.get("answerable") is not False:
            assert q["expect_any"], q["q"]


def test_summary_cache_key_depends_on_content_model_and_path():
    a = cache_key("deepseek", "x.py", b"one")
    assert a == cache_key("deepseek", "x.py", b"one")
    assert a != cache_key("deepseek", "x.py", b"two")
    assert a != cache_key("qwen", "x.py", b"one")
    assert a != cache_key("deepseek", "y.py", b"one")
    assert summary_text("x.py", " body ").startswith("# Описание файла x.py")

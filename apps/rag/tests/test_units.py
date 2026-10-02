from uuid import uuid4

import pytest
from pydantic import ValidationError

from alexsoft_rag.clients.guard import NoopGuard, build_guard
from alexsoft_rag.ingest.chunker import chunk_text
from alexsoft_rag.ingest.loader import content_type_for_key, load_source
from alexsoft_rag.ingest.parser import clean_text
from alexsoft_rag.errors import ApiError
from alexsoft_rag.retrieval.query import INSUFFICIENT_MARK, build_messages, extract_citations
from alexsoft_rag.retrieval.search import normalize_score
from alexsoft_rag.schemas import Chunk, ChunkingConfig, CollectionCreate, DocumentIngest
from alexsoft_rag.store.postgres import decode_cursor, encode_cursor
from alexsoft_rag.store.qdrant import build_filter


# ---- parser -----------------------------------------------------------------
def test_clean_text_normalizes():
    raw = "\ufeffTitle  \r\n\r\n\r\n\r\nBody\x00 text\t\r\n"
    assert clean_text(raw) == "Title\n\nBody text"


# ---- chunker ------------------------------------------------------------------
MD = (
    "# Doc\n\nIntro paragraph about the project.\n\n"
    "## Broker\n\n" + ("RabbitMQ is the target broker for long AI tasks. " * 60) + "\n\n"
    "## Tiny\n\nshort\n\n"
    "## Cache\n\nRedis caches AI answers at stage 6.\n"
)


def test_markdown_chunking_respects_size_and_headers():
    cfg = ChunkingConfig(strategy="markdown", chunk_size=128, chunk_overlap=16)
    chunks = chunk_text(clean_text(MD), cfg)
    assert len(chunks) >= 3
    assert any("Broker" in c.header_path for c in chunks)
    assert all(c.text.strip() for c in chunks)
    # the lone "## Tiny / short" section is merged into a neighbour instead of becoming its own chunk
    assert not any(c.text.strip().endswith("short") and len(c.text) < 40 for c in chunks)


def test_token_and_sentence_strategies():
    text = "Первое предложение. Второе предложение. " * 80
    for strategy in ("token", "sentence"):
        chunks = chunk_text(text, ChunkingConfig(strategy=strategy, chunk_size=64, chunk_overlap=8))
        assert len(chunks) > 1


def test_empty_text_gives_no_chunks():
    assert chunk_text("   \n", ChunkingConfig()) == []


def test_embed_text_includes_section_path():
    chunks = chunk_text("# A\n\n## B\n\nsome body text here", ChunkingConfig(chunk_size=64, chunk_overlap=0))
    assert chunks and "B" in chunks[0].embed_text


def test_chunking_config_overlap_must_be_smaller():
    with pytest.raises(ValidationError):
        ChunkingConfig(chunk_size=64, chunk_overlap=64)


# ---- loader --------------------------------------------------------------------
def test_content_type_by_extension():
    assert content_type_for_key("adr/0015.md") == "text/markdown"
    assert content_type_for_key("notes.txt") == "text/plain"


async def test_loader_inline_and_unsupported_binary():
    text, ct = await load_source({"type": "inline", "text": "hi", "content_type": "text/markdown"}, None, 100)
    assert (text, ct) == ("hi", "text/markdown")
    with pytest.raises(ApiError) as e:
        await load_source({"type": "minio", "bucket": "b", "key": "x/report.pdf"}, None, 100)
    assert e.value.status == 422


# ---- schemas -------------------------------------------------------------------
def test_collection_name_pattern():
    CollectionCreate(name="project-docs")
    for bad in ("A", "x", "Upper", "-bad", "a" * 64):
        with pytest.raises(ValidationError):
            CollectionCreate(name=bad)


def test_ingest_requires_known_source_and_forbids_extra():
    DocumentIngest(source={"type": "inline", "text": "x"})
    with pytest.raises(ValidationError):
        DocumentIngest(source={"type": "ftp", "url": "x"})
    with pytest.raises(ValidationError):
        DocumentIngest(source={"type": "inline", "text": "x"}, bogus=1)


# ---- filters -----------------------------------------------------------------------
def test_build_filter_conditions():
    assert build_filter(None) is None
    flt = build_filter({"kind": "adr", "tags": ["a", "b"], "year": 2026, "ok": True, "w": 0.5})
    keys = {c.key for c in flt.must}
    assert keys == {"metadata.kind", "metadata.tags", "metadata.year", "metadata.ok", "metadata.w"}
    doc = uuid4()
    assert build_filter(None, document_id=doc).must[0].key == "document_id"


# ---- score / cursor ------------------------------------------------------------------
def test_normalize_score_bounds():
    k = 60
    assert normalize_score(2 / (k + 1), "rrf", k) == pytest.approx(1.0)
    assert normalize_score(1 / (k + 1), "rrf", k) == pytest.approx(0.5)
    assert normalize_score(5.0, "dbsf", k) == 1.0
    assert normalize_score(-1.0, "rrf", k) == 0.0


def test_cursor_roundtrip():
    assert decode_cursor(encode_cursor(150)) == 150
    assert decode_cursor(None) == 0
    assert decode_cursor("garbage!!") == 0


# ---- query helpers ----------------------------------------------------------------------
def _chunk(n: int) -> Chunk:
    return Chunk(id=f"p{n}", document_id=uuid4(), external_id=f"doc-{n}", text=f"text {n}", score=0.5, position=n)


def test_citations_follow_markers_and_ignore_invalid():
    chunks = [_chunk(1), _chunk(2), _chunk(3)]
    cites = extract_citations("Факт [2]. Ещё [2][1]. Мусор [9] и [0].", chunks)
    assert [c.chunk_id for c in cites] == ["p2", "p1"]
    assert extract_citations("без ссылок", chunks) == []


def test_prompt_numbers_context_and_guards_instructions():
    msgs = build_messages("Вопрос?", [_chunk(1), _chunk(2)])
    assert msgs[0]["role"] == "system" and INSUFFICIENT_MARK in msgs[0]["content"]
    assert "[1] (источник: doc-1)" in msgs[1]["content"] and "[2]" in msgs[1]["content"]
    assert msgs[1]["content"].rstrip().endswith("Вопрос: Вопрос?")


# ---- guard -------------------------------------------------------------------------------
async def test_noop_guard_allows_and_real_guard_is_not_available_yet():
    g = build_guard(False)
    assert isinstance(g, NoopGuard)
    assert (await g.check_input("x")).allowed and (await g.check_output("p", "o")).allowed
    with pytest.raises(RuntimeError):
        build_guard(True)

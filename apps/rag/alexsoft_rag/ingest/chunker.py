"""Chunking: segments (from parsers) -> text chunks with locators, driven by ChunkingConfig."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter, TokenTextSplitter
from llama_index.core.utils import get_tokenizer

from ..parsers.base import Segment
from ..schemas import ChunkingConfig

MIN_CHUNK_TOKENS = 32  # tiny markdown sections (e.g. a lone heading) are merged into the previous chunk
PAGE_MAX_FACTOR = 2  # a page/table block is kept whole up to chunk_size * this

DEFAULT_STRATEGY = {
    "markdown": "markdown",
    "text": "sentence",
    "diagram": "sentence",
    "code": "code",
    "page": "pages",
    "table": "table",
}


@dataclass(frozen=True)
class TextChunk:
    text: str
    header: str = ""  # context for embeddings (section path; `File / Language / Symbol` for code; ...)
    locator: dict[str, Any] = field(default_factory=dict)
    kind: str = "text"

    @property
    def embed_text(self) -> str:
        """Text used for embeddings: the header gives the model/BM25 extra context."""
        return f"{self.header}\n\n{self.text}" if self.header else self.text


def effective_strategy(kind: str, requested: str) -> str:
    """Resolve the strategy for a segment kind; incompatible requests fall back to `auto`."""
    default = DEFAULT_STRATEGY.get(kind, "sentence")
    if requested == "auto" or kind == "table":
        return default
    if requested in ("sentence", "token"):
        return requested
    if requested == "markdown":
        return "markdown" if kind in ("markdown", "text", "diagram") else default
    if requested == "code":
        return "code" if kind == "code" else default
    if requested == "pages":
        return "pages" if kind == "page" else default
    return default


def _section(header_path: str | None) -> str:
    parts = [p for p in (header_path or "").split("/") if p]
    return " > ".join(parts)


def _markdown(seg: Segment, cfg: ChunkingConfig) -> list[TextChunk]:
    splitter = SentenceSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap)
    tokenizer = get_tokenizer()
    nodes = MarkdownNodeParser().get_nodes_from_documents([Document(text=seg.text)])
    chunks: list[TextChunk] = []
    for node in nodes:
        body = node.get_content().strip()
        if not body:
            continue
        # header_path holds the *parents* of this section; its own heading is the first line of the body
        first_line = body.splitlines()[0].strip()
        own = first_line.lstrip("#").strip() if first_line.startswith("#") else ""
        parent = _section(node.metadata.get("header_path"))
        header = " > ".join(p for p in (parent, own) if p)
        pieces = [body] if len(tokenizer(body)) <= cfg.chunk_size else splitter.split_text(body)
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            if chunks and len(tokenizer(piece)) < MIN_CHUNK_TOKENS:
                prev = chunks[-1]
                merged = f"{prev.text}\n\n{piece}"
                if len(tokenizer(merged)) <= cfg.chunk_size:
                    chunks[-1] = TextChunk(merged, prev.header, prev.locator, "markdown")
                    continue
            loc = dict(seg.locator)
            if header:
                loc["section"] = header
            chunks.append(TextChunk(piece, header, loc, "markdown"))
    return chunks


def _windowed(seg: Segment, cfg: ChunkingConfig, strategy: str) -> list[TextChunk]:
    if strategy == "token":
        parts = TokenTextSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap).split_text(seg.text)
    else:
        parts = SentenceSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap).split_text(seg.text)
    return [TextChunk(p.strip(), seg.header, dict(seg.locator), seg.kind) for p in parts if p.strip()]


def _whole_or_split(seg: Segment, cfg: ChunkingConfig) -> list[TextChunk]:
    """pages / table: keep the block whole while it is reasonably small, else split by sentences."""
    text = seg.text.strip()
    if not text:
        return []
    if len(get_tokenizer()(text)) <= cfg.chunk_size * PAGE_MAX_FACTOR:
        return [TextChunk(text, seg.header, dict(seg.locator), seg.kind)]
    return _windowed(seg, cfg, "sentence")


def chunk_segments(segments: list[Segment], cfg: ChunkingConfig) -> list[TextChunk]:
    if cfg.chunk_overlap >= cfg.chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    out: list[TextChunk] = []
    for seg in segments:
        if not seg.text.strip():
            continue
        strategy = effective_strategy(seg.kind, cfg.strategy)
        if strategy == "markdown":
            out.extend(_markdown(seg, cfg))
        elif strategy == "code":
            from .code_chunker import chunk_code

            out.extend(chunk_code(seg, cfg))
        elif strategy in ("pages", "table"):
            out.extend(_whole_or_split(seg, cfg))
        else:  # sentence | token
            out.extend(_windowed(seg, cfg, strategy))
    return out


def chunk_text(text: str, cfg: ChunkingConfig) -> list[TextChunk]:
    """Convenience: chunk a single markdown/plain text."""
    return chunk_segments([Segment(text, kind="markdown")], cfg) if text.strip() else []

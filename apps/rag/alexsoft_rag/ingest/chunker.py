"""Chunking via LlamaIndex node parsers, driven by ChunkingConfig."""

from __future__ import annotations

from dataclasses import dataclass

from llama_index.core import Document
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter, TokenTextSplitter
from llama_index.core.utils import get_tokenizer

from ..schemas import ChunkingConfig

MIN_CHUNK_TOKENS = 32  # tiny markdown sections (e.g. a lone heading) are merged into the previous chunk


@dataclass(frozen=True)
class TextChunk:
    text: str
    header_path: str = ""

    @property
    def embed_text(self) -> str:
        """Text used for embeddings: section path gives the model/BM25 extra context."""
        return f"{self.header_path}\n\n{self.text}" if self.header_path else self.text


def _header_path(raw: str | None) -> str:
    parts = [p for p in (raw or "").split("/") if p]
    return " > ".join(parts)


def chunk_text(text: str, cfg: ChunkingConfig) -> list[TextChunk]:
    if not text.strip():
        return []
    if cfg.chunk_overlap >= cfg.chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    if cfg.strategy == "token":
        parts = TokenTextSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap).split_text(text)
        return [TextChunk(p.strip()) for p in parts if p.strip()]

    splitter = SentenceSplitter(chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap)
    if cfg.strategy == "sentence":
        return [TextChunk(p.strip()) for p in splitter.split_text(text) if p.strip()]

    # markdown: split by headings, then size-split oversize sections, then merge tiny ones
    tokenizer = get_tokenizer()
    nodes = MarkdownNodeParser().get_nodes_from_documents([Document(text=text)])
    chunks: list[TextChunk] = []
    for node in nodes:
        body = node.get_content().strip()
        if not body:
            continue
        # header_path holds the *parents* of this section; its own heading is the first line of the body
        first_line = body.splitlines()[0].strip()
        own = first_line.lstrip("#").strip() if first_line.startswith("#") else ""
        parent = _header_path(node.metadata.get("header_path"))
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
                    chunks[-1] = TextChunk(merged, prev.header_path)
                    continue
            chunks.append(TextChunk(piece, header))
    return chunks

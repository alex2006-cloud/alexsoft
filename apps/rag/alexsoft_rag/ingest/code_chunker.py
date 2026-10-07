"""Code chunking: parser units are already syntax-aware; oversized ones are packed by lines."""

from __future__ import annotations

from ..parsers.base import Segment, count_tokens
from ..parsers.code import build_header
from ..schemas import ChunkingConfig
from .chunker import PAGE_MAX_FACTOR, TextChunk


def chunk_code(seg: Segment, cfg: ChunkingConfig) -> list[TextChunk]:
    if count_tokens(seg.text) <= cfg.chunk_size * PAGE_MAX_FACTOR:
        return [TextChunk(seg.text, seg.header, dict(seg.locator), "code")]

    lines = seg.text.split("\n")
    base = int(seg.locator.get("line_start", 1))
    symbol = str(seg.locator.get("symbol", ""))
    path = seg.header.split("\n", 1)[0].removeprefix("File: ")
    language = str(seg.meta.get("language", ""))
    out: list[TextChunk] = []
    start = 0
    tokens = 0
    for i, line in enumerate(lines):
        t = count_tokens(line) + 1
        if tokens + t > cfg.chunk_size and i > start:
            out.append(_piece(lines, start, i, base, symbol, path, language, seg))
            start, tokens = i, 0
        tokens += t
    out.append(_piece(lines, start, len(lines), base, symbol, path, language, seg))
    return [c for c in out if c.text.strip()]


def _piece(lines, a, b, base, symbol, path, language, seg) -> TextChunk:
    first, last = base + a, base + b - 1
    locator = {**seg.locator, "line_start": first, "line_end": last}
    return TextChunk(
        "\n".join(lines[a:b]), build_header(path, language, symbol, first, last), locator, "code"
    )

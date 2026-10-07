"""Parser framework: raw bytes -> segments with locators (ADR-0018)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class RawDocument:
    """A loaded source: file name (for type detection and `path`), bytes, optional MIME hint."""

    filename: str
    data: bytes
    content_type: str | None = None


@dataclass
class Segment:
    """A parsed piece of a document, before chunking.

    kind: markdown | text | code | page | table | diagram
    locator: contract Locator fields that are already known (page, sheet, range, ...)
    meta: parser hints for the chunker (e.g. language for code)
    header: optional context line(s) prepended to the text for embeddings
    """

    text: str
    kind: str = "text"
    locator: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    header: str = ""


class VisionOCR(Protocol):
    """Recognizes text on a page image (PNG bytes); implemented over LiteLLM (model alias `vision`)."""

    async def read_page(self, png: bytes, prompt: str | None = None) -> str: ...


@dataclass
class ParseContext:
    chunk_size: int = 512  # target tokens per chunk; table parsers size row groups from it
    ocr: VisionOCR | None = None
    max_ocr_pages: int = 60
    ocr_concurrency: int = 3


def count_tokens(text: str) -> int:
    from llama_index.core.utils import get_tokenizer

    return len(get_tokenizer()(text))


def normalize_newlines(text: str) -> str:
    """Keep every line as is (code line numbers must match the original file)."""
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")

"""Parser registry: file type (by extension / MIME) -> parser."""

from __future__ import annotations

import posixpath
from collections.abc import Awaitable, Callable

from ..errors import ApiError
from .base import ParseContext, RawDocument, Segment
from .text import parse_markdown, parse_plain

Parser = Callable[[RawDocument, ParseContext], Awaitable[list[Segment]]]

MARKDOWN_EXT = {".md", ".markdown"}
TEXT_EXT = {".txt", ".rst", ".csv", ".tsv", ".log"}

# Binary formats we cannot read (yet): rejected with a clear error instead of garbage chunks.
UNSUPPORTED_BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".zip", ".gz", ".tar", ".7z",
    ".xls", ".docx", ".doc", ".pptx", ".ppt", ".bin", ".exe", ".dll", ".pckl", ".pyc", ".db",
}

MIME_TO_EXT = {
    "text/markdown": ".md",
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/json": ".json",
    "application/x-yaml": ".yaml",
    "text/yaml": ".yaml",
    "text/x-python": ".py",
    "application/typescript": ".ts",
    "application/sql": ".sql",
    "application/xml": ".xml",
    "text/xml": ".xml",
}


def detect_ext(raw: RawDocument) -> str:
    ext = posixpath.splitext(raw.filename.lower())[1]
    if raw.content_type:
        mime = raw.content_type.split(";")[0].strip().lower()
        # an explicit MIME wins only when the filename gives no usable hint
        if not ext or ext == ".bin":
            ext = MIME_TO_EXT.get(mime, ext)
    return ext


def _registry() -> dict[str, Parser]:
    reg: dict[str, Parser] = {}
    for e in MARKDOWN_EXT:
        reg[e] = parse_markdown
    for e in TEXT_EXT:
        reg[e] = parse_plain
    # code / pdf / xlsx / diagrams are registered by their modules (ADR-0018)
    for module_name in ("code", "xlsx", "pdf", "diagrams"):
        try:
            module = __import__(f"{__name__}.{module_name}", fromlist=["EXTENSIONS"])
        except ModuleNotFoundError as e:  # parser module not part of this build / dependency missing
            if e.name and e.name.startswith(__name__):
                continue
            raise
        reg.update(module.EXTENSIONS)
    return reg


_REGISTRY: dict[str, Parser] | None = None


def supported_extensions() -> list[str]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _registry()
    return sorted(_REGISTRY)


async def parse_document(raw: RawDocument, ctx: ParseContext) -> list[Segment]:
    """Parse a loaded document into segments; unknown extensions are tried as UTF-8 text."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _registry()
    ext = detect_ext(raw)
    if ext in UNSUPPORTED_BINARY_EXT:
        raise ApiError(
            422,
            "validation_error",
            f"Unsupported document type '{ext}': supported are {', '.join(supported_extensions())}",
        )
    parser = _REGISTRY.get(ext, parse_plain)
    segments = await parser(raw, ctx)
    if not segments:
        raise ApiError(422, "validation_error", "Document is empty after parsing")
    return segments

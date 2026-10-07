"""Markdown and plain text parsers."""

from __future__ import annotations

from ..errors import ApiError
from ..ingest.parser import clean_text
from .base import ParseContext, RawDocument, Segment


def decode_text(raw: RawDocument) -> str:
    try:
        return raw.data.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ApiError(
            422, "validation_error", f"{raw.filename}: not valid UTF-8 text (unsupported binary format?)"
        ) from e


async def parse_markdown(raw: RawDocument, ctx: ParseContext) -> list[Segment]:
    text = clean_text(decode_text(raw))
    return [Segment(text, kind="markdown")] if text else []


async def parse_plain(raw: RawDocument, ctx: ParseContext) -> list[Segment]:
    text = clean_text(decode_text(raw))
    return [Segment(text, kind="text")] if text else []

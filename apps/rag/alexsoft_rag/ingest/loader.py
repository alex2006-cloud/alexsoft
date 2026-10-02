"""Loader: DocumentSource (MinIO object or inline text) -> raw text + content type."""

from __future__ import annotations

import posixpath
from typing import Any

from ..clients.minio_client import ObjectStore
from ..errors import ApiError

_BINARY_EXT = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz", ".xlsx", ".xls",
    ".docx", ".doc", ".pptx", ".bin", ".exe", ".pckl",
}
_MARKDOWN_EXT = {".md", ".markdown"}


def content_type_for_key(key: str) -> str:
    ext = posixpath.splitext(key.lower())[1]
    return "text/markdown" if ext in _MARKDOWN_EXT else "text/plain"


async def load_source(source: dict[str, Any], objects: ObjectStore, max_chars: int) -> tuple[str, str]:
    """Returns (text, content_type). Only UTF-8 text documents are supported (stage 5)."""
    kind = source.get("type")
    if kind == "inline":
        text = source["text"]
        return text, source.get("content_type", "text/plain")

    if kind == "minio":
        key: str = source["key"]
        ext = posixpath.splitext(key.lower())[1]
        if ext in _BINARY_EXT:
            raise ApiError(
                422,
                "validation_error",
                f"Unsupported document type '{ext}': only UTF-8 text/markdown sources are supported",
            )
        data = await objects.get_object(
            source.get("bucket") or objects.default_bucket,
            key,
            source.get("version_id"),
            max_bytes=max_chars * 4,
        )
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise ApiError(422, "validation_error", "Document is not valid UTF-8 text") from e
        return text, content_type_for_key(key)

    raise ApiError(422, "validation_error", f"Unknown source type: {kind!r}")

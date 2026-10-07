"""Loader: DocumentSource (MinIO object or inline text) -> RawDocument (bytes + file name)."""

from __future__ import annotations

import posixpath
from typing import Any

from ..clients.minio_client import ObjectStore
from ..errors import ApiError
from ..parsers import supported_extensions
from ..parsers.base import RawDocument

_BINARY_FORMATS = {".pdf", ".xlsx"}  # readable only from MinIO, never from inline text


async def load_source(
    source: dict[str, Any],
    objects: ObjectStore,
    *,
    max_bytes: int,
    external_id: str | None = None,
) -> RawDocument:
    """Fetch source bytes. Size limits: inline text is checked by the route, objects here."""
    kind = source.get("type")
    if kind == "inline":
        content_type = source.get("content_type", "text/plain")
        name = external_id or ("inline.md" if content_type == "text/markdown" else "inline.txt")
        ext = posixpath.splitext(name.lower())[1]
        # inline is text: keep text/code/diagram extensions, otherwise decide md/txt by content_type
        if ext not in supported_extensions() or ext in _BINARY_FORMATS:
            name += ".md" if content_type == "text/markdown" else ".txt"
        return RawDocument(filename=name, data=source["text"].encode("utf-8"), content_type=content_type)

    if kind == "minio":
        key: str = source["key"]
        data = await objects.get_object(
            source.get("bucket") or objects.default_bucket,
            key,
            source.get("version_id"),
            max_bytes=max_bytes,
        )
        return RawDocument(filename=key, data=data, content_type=source.get("content_type"))

    raise ApiError(422, "validation_error", f"Unknown source type: {kind!r}")

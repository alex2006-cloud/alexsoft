"""kb-sync configuration (apps/rag/kb/sources.yaml)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..config import REPO_ROOT

DEFAULT_SOURCES = REPO_ROOT / "apps" / "rag" / "kb" / "sources.yaml"


@dataclass
class CollectionRule:
    name: str
    description: str
    sparse_language: str
    include: list[str]
    chunking: dict[str, Any] = field(default_factory=dict)


@dataclass
class SummaryRule:
    enabled: bool = False
    model: str = "deepseek"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    min_lines: int = 25
    max_file_bytes: int = 60_000
    collection: str = "project-code"


@dataclass
class SyncConfig:
    minio_prefix: str
    exclude: list[str]
    max_text_bytes: int
    max_binary_bytes: int
    collections: list[CollectionRule]  # order matters: the first matching rule wins
    kinds: list[tuple[str, str]]  # (glob, kind), first match wins
    summaries: SummaryRule


def load_config(path: Path | None = None) -> SyncConfig:
    path = path or DEFAULT_SOURCES
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    collections = [
        CollectionRule(
            name=name,
            description=spec.get("description", ""),
            sparse_language=spec.get("sparse_language", "russian"),
            include=list(spec.get("include", [])),
            chunking=dict(spec.get("chunking") or {}),
        )
        for name, spec in (raw.get("collections") or {}).items()
    ]
    if not collections:
        raise ValueError(f"{path}: no collections configured")
    s = raw.get("summaries") or {}
    return SyncConfig(
        minio_prefix=raw.get("minio_prefix", "kb").strip("/"),
        exclude=list(raw.get("exclude", [])),
        max_text_bytes=int(raw.get("max_text_bytes", 1_000_000)),
        max_binary_bytes=int(raw.get("max_binary_bytes", 50 * 1024 * 1024)),
        collections=collections,
        kinds=[(k["glob"], k["kind"]) for k in raw.get("kinds", [])],
        summaries=SummaryRule(
            enabled=bool(s.get("enabled", False)),
            model=s.get("model", "deepseek"),
            include=list(s.get("include", [])),
            exclude=list(s.get("exclude", [])),
            min_lines=int(s.get("min_lines", 25)),
            max_file_bytes=int(s.get("max_file_bytes", 60_000)),
            collection=s.get("collection", "project-code"),
        ),
    )

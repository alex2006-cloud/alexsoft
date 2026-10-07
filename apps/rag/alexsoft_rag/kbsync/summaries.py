"""Per-file code summaries (LLM via LiteLLM), cached on disk by content hash.

A summary answers "what does this file do?" questions that raw code retrieves badly. It is indexed as a
normal document (`summary/<path>.md`) next to the code.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import httpx

PROMPT_VERSION = "v1"
PROMPT = (
    "Ты технический писатель. Ниже файл исходного кода проекта alexsoft: {path}.\n"
    "Напиши краткое описание на русском (5-10 предложений): назначение файла, ключевые функции и классы и что "
    "они делают, от чего файл зависит и с какими частями системы взаимодействует. Имена идентификаторов, "
    "файлов и технологий оставляй как в коде. Не пересказывай код построчно и не выдумывай того, чего нет в файле.\n\n"
    "```\n{code}\n```"
)


def cache_dir() -> Path:
    base = os.environ.get("RAG_SUMMARY_CACHE")
    if base:
        return Path(base)
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "AlexsoftRag" / "summaries"


def cache_key(model: str, path: str, content: bytes) -> str:
    h = hashlib.sha256()
    h.update(f"{PROMPT_VERSION}|{model}|{path}|".encode())
    h.update(content)
    return h.hexdigest()


def summary_text(path: str, body: str) -> str:
    return f"# Описание файла {path}\n\n{body.strip()}\n"


class Summarizer:
    def __init__(self, base_url: str, api_key: str, model: str, *, max_file_bytes: int, timeout_s: float = 120.0):
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=timeout_s, trust_env=False)
        self._model = model
        self._max_bytes = max_file_bytes
        self._dir = cache_dir()
        self._dir.mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self._http.close()

    def cached(self, path: str, content: bytes) -> str | None:
        f = self._dir / f"{cache_key(self._model, path, content)}.md"
        return f.read_text(encoding="utf-8") if f.exists() else None

    def summarize(self, path: str, content: bytes) -> tuple[str, bool]:
        """-> (markdown, from_cache). Raises RuntimeError on LLM failure."""
        hit = self.cached(path, content)
        if hit is not None:
            return hit, True
        code = content[: self._max_bytes].decode("utf-8", "replace")
        if len(content) > self._max_bytes:
            code += "\n... (файл обрезан)"
        r = self._http.post(
            "/v1/chat/completions",
            json={
                "model": self._model,
                "messages": [{"role": "user", "content": PROMPT.format(path=path, code=code)}],
                "temperature": 0.1,
                "max_tokens": 700,
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"LiteLLM HTTP {r.status_code}: {r.text[:200]}")
        try:
            body = r.json()["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise RuntimeError("unexpected LiteLLM response") from e
        if not body.strip():
            raise RuntimeError("empty summary")
        text = summary_text(path, body)
        (self._dir / f"{cache_key(self._model, path, content)}.md").write_text(text, encoding="utf-8")
        return text, False

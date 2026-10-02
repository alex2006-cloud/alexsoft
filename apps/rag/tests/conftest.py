"""Shared test helpers: deterministic fake LLM/embeddings so tests need no provider keys."""

from __future__ import annotations

import hashlib
import math
import re
import socket

import pytest

from alexsoft_rag.clients.litellm import ChatResult

FAKE_DIMS = 256


def hashed_vector(text: str, dims: int = FAKE_DIMS) -> list[float]:
    """Feature-hashed bag of words: similar texts get similar vectors (cosine)."""
    vec = [0.0] * dims
    for tok in re.findall(r"\w+", text.lower()):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % dims] += 1.0 if (h >> 8) % 2 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class FakeLLM:
    """Stands in for LiteLLMClient (embeddings + chat); records chat calls."""

    embedding_model = "fake-embedding"

    def __init__(self, answer: str = "Ответ по контексту [1].") -> None:
        self.answer = answer
        self.chat_calls: list[dict] = []
        self.embed_calls = 0

    async def embed(self, texts, model=None):
        self.embed_calls += 1
        return [hashed_vector(t) for t in texts]

    async def chat(self, model, messages, *, temperature, max_tokens):
        self.chat_calls.append({"model": model, "messages": messages})
        return ChatResult(self.answer, model, 10, 5)

    async def is_alive(self) -> bool:
        return True

    async def aclose(self) -> None:
        pass


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()

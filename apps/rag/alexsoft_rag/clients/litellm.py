"""LiteLLM (AI Gateway, ADR-0011) client — the only path to models (embeddings and chat)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..errors import upstream


@dataclass
class ChatResult:
    text: str
    model: str | None
    prompt_tokens: int | None
    completion_tokens: int | None


class LiteLLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        embedding_model: str,
        timeout_s: float = 120.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._base = base_url.rstrip("/")
        self.embedding_model = embedding_model
        self._http = client or httpx.AsyncClient(
            base_url=self._base, headers=headers, timeout=timeout_s, trust_env=False
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Dense embeddings for `texts`, in input order (model defaults to the service's one)."""
        if not texts:
            return []
        try:
            r = await self._http.post(
                "/v1/embeddings", json={"model": model or self.embedding_model, "input": texts}
            )
        except httpx.HTTPError as e:
            raise upstream("embedding_unavailable", f"LiteLLM embeddings request failed: {e}") from e
        if r.status_code != 200:
            raise upstream(
                "embedding_unavailable",
                f"LiteLLM embeddings HTTP {r.status_code}: {_safe_body(r)}",
            )
        data = r.json().get("data") or []
        data.sort(key=lambda d: d.get("index", 0))
        vectors = [d["embedding"] for d in data]
        if len(vectors) != len(texts):
            raise upstream("embedding_unavailable", "LiteLLM returned wrong number of embeddings")
        return vectors

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> ChatResult:
        try:
            r = await self._http.post(
                "/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
        except httpx.HTTPError as e:
            raise upstream("llm_unavailable", f"LiteLLM chat request failed: {e}") from e
        if r.status_code != 200:
            raise upstream("llm_unavailable", f"LiteLLM chat HTTP {r.status_code}: {_safe_body(r)}")
        body = r.json()
        try:
            text = body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise upstream("llm_unavailable", "LiteLLM returned an unexpected chat payload") from e
        usage = body.get("usage") or {}
        return ChatResult(
            text=text,
            model=body.get("model"),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    async def is_alive(self) -> bool:
        try:
            r = await self._http.get("/health/liveliness", timeout=5.0)
            return r.status_code == 200
        except httpx.HTTPError:
            return False


def _safe_body(r: httpx.Response) -> str:
    import re

    return re.sub(r"sk-[A-Za-z0-9_-]{8,}", "sk-REDACTED", r.text)[:300]

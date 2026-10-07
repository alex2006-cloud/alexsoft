"""Vision OCR for scanned PDF pages: a vision model via LiteLLM (no direct provider access)."""

from __future__ import annotations

import base64
import hashlib

from ..store.postgres import Database
from .litellm import LiteLLMClient

OCR_PROMPT = (
    "Это страница документа. Перепиши весь текст со страницы дословно, сохраняя порядок чтения. "
    "Таблицы оформи как markdown-таблицы, заголовки — как markdown-заголовки. Диаграммы и схемы кратко "
    "опиши словами (узлы и связи). Не добавляй комментариев и не пересказывай. "
    "Если на странице нет текста, ответь пустой строкой."
)


class LiteLLMVisionOCR:
    """Implements `parsers.base.VisionOCR`. Results are cached by image hash (Postgres)."""

    def __init__(self, llm: LiteLLMClient, db: Database, model: str, *, max_tokens: int = 3000) -> None:
        self._llm = llm
        self._db = db
        self._model = model
        self._max_tokens = max_tokens

    async def read_page(self, png: bytes, prompt: str | None = None) -> str:
        digest = hashlib.sha256(png).hexdigest()
        cached = await self._db.get_ocr(digest, self._model)
        if cached is not None:
            return cached
        data_uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        result = await self._llm.chat(
            self._model,
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or OCR_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            temperature=0.0,
            max_tokens=self._max_tokens,
        )
        text = result.text.strip()
        await self._db.put_ocr(digest, self._model, text)
        return text

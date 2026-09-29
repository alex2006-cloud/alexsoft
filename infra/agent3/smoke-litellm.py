"""One short LLM call via Agent3 make_model_client → LiteLLM."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agent3"))

from autogen_core.models import UserMessage

from llm import make_model_client, model_name  # noqa: E402


async def _run() -> None:
    client = make_model_client()
    try:
        result = await client.create(
            [UserMessage(content="Reply with exactly one word: pong", source="user")]
        )
        text = (result.content if hasattr(result, "content") else str(result)).strip()
        if isinstance(text, list):
            text = " ".join(str(part) for part in text).strip()
        print(f"model={model_name()} reply={text[:200]!r}")
        if not text:
            raise SystemExit("empty reply from LiteLLM")
    finally:
        await client.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()

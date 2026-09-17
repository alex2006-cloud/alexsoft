"""Invoke graph_llm once against LiteLLM."""
from __future__ import annotations

import os
import sys

# Ensure apps/agent1 is importable when not installed editable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agent1"))

from graph_llm import graph  # noqa: E402


def main() -> None:
    out = graph.invoke({"message": "Reply with exactly one word: pong", "reply": ""})
    reply = (out.get("reply") or "").strip()
    print(f"model={os.environ.get('AGENT1_MODEL', 'qwen')} reply={reply[:200]!r}")
    if not reply:
        raise SystemExit("empty reply from LiteLLM graph")


if __name__ == "__main__":
    main()

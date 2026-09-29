"""One short LLM call via Agent2 make_llm → LiteLLM."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agent2"))

from llm import make_llm, model_name  # noqa: E402


def main() -> None:
    llm = make_llm(temperature=0)
    reply = llm.call([{"role": "user", "content": "Reply with exactly one word: pong"}])
    text = (reply if isinstance(reply, str) else str(reply)).strip()
    print(f"model={model_name()} reply={text[:200]!r}")
    if not text:
        raise SystemExit("empty reply from LiteLLM")


if __name__ == "__main__":
    main()

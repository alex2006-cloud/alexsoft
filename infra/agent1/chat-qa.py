"""REPL for the Agent1 Q&A + calculator product (thread memory via MemorySaver)."""
from __future__ import annotations

import argparse
import os
import sys
import uuid

# Ensure apps/agent1 is importable when not installed editable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "agent1"))

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

from graph_qa import build_graph  # noqa: E402
from llm import model_name  # noqa: E402


def ask(app, thread_id: str, message: str) -> str:
    out = app.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    last = out["messages"][-1]
    return (getattr(last, "content", None) or str(last)).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", metavar="QUESTION", help="ask a single question and exit")
    args = parser.parse_args()

    app = build_graph(MemorySaver())
    thread_id = str(uuid.uuid4())

    if args.once:
        print(ask(app, thread_id, args.once))
        return

    print(f"Agent1 Q&A + калькулятор (model={model_name()}). Пустая строка или 'exit' — выход.")
    while True:
        try:
            message = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not message or message.lower() in {"exit", "quit"}:
            return
        print()
        print(ask(app, thread_id, message))


if __name__ == "__main__":
    main()

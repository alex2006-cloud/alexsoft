"""Smoke: RAG search + the BP1 graph end-to-end (needs RAG :8200, LiteLLM :8080, RAG_API_KEY in .env).

Run with the Agent1 venv:  python infra/agent1/smoke-bp1.py ["question"]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "apps", "agent1"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

import rag_client  # noqa: E402


def main() -> int:
    question = " ".join(sys.argv[1:]) or "Какой шлюз к LLM используется в проекте и почему?"
    probe = rag_client.search("project-docs", "AI Gateway LiteLLM", 2)
    print("RAG search:", probe[:200].replace("\n", " "))
    if probe.startswith("ERROR"):
        return 1

    from langgraph.checkpoint.memory import MemorySaver

    from graph_bp1 import build_graph

    app = build_graph(MemorySaver())
    out = app.invoke({"messages": [{"role": "user", "content": question}]},
                     config={"configurable": {"thread_id": "smoke-bp1"}})
    msgs = out["messages"]
    print("tool calls:", sum(1 for m in msgs if getattr(m, "type", "") == "tool"))
    print("\nQ:", question, "\nA:", msgs[-1].content)
    return 0 if msgs[-1].content.strip() else 1


if __name__ == "__main__":
    raise SystemExit(main())

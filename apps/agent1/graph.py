"""Minimal Agent1 graph for LangSmith Studio (no LLM until wire step)."""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class EchoState(TypedDict):
    message: str
    reply: str


def echo_node(state: EchoState) -> EchoState:
    msg = state.get("message") or ""
    return {"message": msg, "reply": f"echo:{msg}"}


def build_graph():
    g = StateGraph(EchoState)
    g.add_node("echo", echo_node)
    g.add_edge(START, "echo")
    g.add_edge("echo", END)
    return g.compile()


# LangGraph CLI looks for a compiled graph export.
graph = build_graph()

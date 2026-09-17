"""Tiny LangGraph smoke: two nodes, no LLM."""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    value: int


def add_one(state: State) -> State:
    return {"value": state["value"] + 1}


def times_two(state: State) -> State:
    return {"value": state["value"] * 2}


def main() -> None:
    import langgraph

    g = StateGraph(State)
    g.add_node("add_one", add_one)
    g.add_node("times_two", times_two)
    g.add_edge(START, "add_one")
    g.add_edge("add_one", "times_two")
    g.add_edge("times_two", END)
    app = g.compile()
    out = app.invoke({"value": 3})
    assert out["value"] == 8, out
    print(f"langgraph {getattr(langgraph, '__version__', 'ok')} smoke_ok value={out['value']}")


if __name__ == "__main__":
    main()

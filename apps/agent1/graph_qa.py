"""Agent1 product: Q&A assistant with a calculator tool (LangGraph + LiteLLM)."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from calculator import CalculatorError, calculate
from llm import make_llm
from prompts import CALCULATOR_DESCRIPTION, SYSTEM_PROMPT


@tool("calculator", description=CALCULATOR_DESCRIPTION)
def calculator(expression: str) -> str:
    """Safe math evaluation; the LLM-facing text lives in prompts.CALCULATOR_DESCRIPTION."""
    try:
        return calculate(expression)
    except CalculatorError as exc:
        return f"ERROR: {exc}"


TOOLS = [calculator]


@lru_cache(maxsize=1)
def _bound_llm():
    """Built on first call so the Studio/CLI runner can load .env before the client exists."""
    return make_llm().bind_tools(TOOLS)


def agent_node(state: MessagesState) -> dict:
    reply = _bound_llm().invoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
    return {"messages": [reply]}


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    g = StateGraph(MessagesState)
    g.add_node("agent", agent_node)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=checkpointer)


# LangGraph CLI / Studio provides persistence itself, so no checkpointer here.
graph = build_graph()

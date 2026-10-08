"""BP1 product: Q&A over the alexsoft knowledge base (LangGraph + apps/rag + LiteLLM)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

import rag_client
from llm import make_llm
from prompts import BP1_SYSTEM_PROMPT, SEARCH_PROJECT_DESCRIPTION


@tool("search_project", description=SEARCH_PROJECT_DESCRIPTION)
def search_project(
    query: str,
    collection: Literal["project-docs", "project-code"] = "project-docs",
    top_k: int = 5,
) -> str:
    """Hybrid search in apps/rag; the LLM-facing text lives in prompts.SEARCH_PROJECT_DESCRIPTION."""
    return rag_client.search(collection, query, top_k)


TOOLS = [search_project]


@lru_cache(maxsize=1)
def _bound_llm():
    """Built on first call so the Studio/CLI runner can load .env before the client exists."""
    return make_llm().bind_tools(TOOLS)


def agent_node(state: MessagesState) -> dict:
    reply = _bound_llm().invoke([SystemMessage(BP1_SYSTEM_PROMPT), *state["messages"]])
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

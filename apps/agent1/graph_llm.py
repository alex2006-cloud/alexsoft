"""Agent1 graph with LiteLLM (OpenAI-compatible) — used after wire step."""
from __future__ import annotations

import os
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph


class ChatState(TypedDict):
    message: str
    reply: str


def _llm() -> ChatOpenAI:
    base = (os.environ.get("OPENAI_BASE_URL") or "").strip()
    if not base:
        gateway = (os.environ.get("AI_GATEWAY_URL") or "http://127.0.0.1:8080").rstrip("/")
        base = f"{gateway}/v1"
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("LITELLM_MASTER_KEY")
        or "sk-unset"
    )
    model = os.environ.get("AGENT1_MODEL") or "deepseek"
    return ChatOpenAI(model=model, api_key=api_key, base_url=base, temperature=0)


def chat_node(state: ChatState) -> ChatState:
    msg = state.get("message") or ""
    llm = _llm()
    result = llm.invoke(msg)
    content = getattr(result, "content", None) or str(result)
    return {"message": msg, "reply": content}


def build_graph():
    g = StateGraph(ChatState)
    g.add_node("chat", chat_node)
    g.add_edge(START, "chat")
    g.add_edge("chat", END)
    return g.compile()


graph = build_graph()

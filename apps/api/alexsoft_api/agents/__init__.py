"""Agent registry seed + runner lookup."""

from __future__ import annotations

from typing import Any

from ..config import Settings
from .base import AgentError, AgentRunner, Message, Meta, RunRequest, Step
from .echo import EchoRunner
from .langgraph_server import LangGraphServerRunner

__all__ = [
    "AgentError", "AgentRunner", "Message", "Meta", "RunRequest", "Step",
    "EchoRunner", "LangGraphServerRunner", "build_runners", "seed_agents",
]


def build_runners(settings: Settings) -> dict[str, AgentRunner]:
    return {
        "echo": EchoRunner(),
        "langgraph": LangGraphServerRunner(settings.bl_agent_server_url, timeout_s=settings.bl_run_timeout_s),
    }


def seed_agents(settings: Settings) -> list[dict[str, Any]]:
    """Initial registry rows (inserted only if missing; later edits in the admin panel are kept)."""
    return [
        {
            "id": "echo-demo",
            "title": "Эхо (демо)",
            "description": "Заглушка без LLM: возвращает ваш текст. Проверка входа, квоты и потока статуса.",
            "kind": "echo",
            "enabled": True,
            "input_hint": "Любой текст",
            "config": {},
            "sort": 10,
        },
        {
            "id": "agent1-qa",
            "title": "Q&A с калькулятором",
            "description": "Диалоговый ассистент (LangGraph, LLM через LiteLLM): отвечает на вопросы и считает инструментом, а не «в уме».",
            "kind": "langgraph",
            "enabled": True,
            "input_hint": "Например: 37 от 128 в процентах",
            "config": {"assistant_id": "agent1_qa", "url": settings.bl_agent_server_url},
            "sort": 20,
        },
        {
            "id": "bp1-project-qa",
            "title": "Q&A по проекту (БП1)",
            "description": "Ответы по документации и коду alexsoft на базе RAG (LangGraph + Qdrant) со ссылками на источники.",
            "kind": "langgraph",
            "enabled": True,
            "input_hint": "Спросите об архитектуре проекта",
            "config": {"assistant_id": "bp1_qa", "url": settings.bl_agent_server_url},
            "sort": 30,
        },
    ]

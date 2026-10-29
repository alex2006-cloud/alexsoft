"""Agent registry seed + runner lookup."""

from __future__ import annotations

from typing import Any

from ..config import Settings
from .base import AgentError, AgentRunner, Message, Meta, RunRequest, Step
from .echo import EchoRunner
from .langgraph_server import LangGraphServerRunner
from .rabbit_langgraph import RabbitLangGraphRunner

__all__ = [
    "AgentError", "AgentRunner", "Message", "Meta", "RunRequest", "Step",
    "EchoRunner", "LangGraphServerRunner", "RabbitLangGraphRunner", "build_runners", "seed_agents",
]


def build_runners(settings: Settings) -> dict[str, AgentRunner]:
    transport = (settings.bl_agent_transport or "http").strip().lower()
    if transport == "rabbitmq":
        langgraph: AgentRunner = RabbitLangGraphRunner(
            settings.amqp_url,
            queue_name=settings.bl_agent_queue,
            timeout_s=settings.bl_run_timeout_s,
            default_agent_url=settings.bl_agent_server_url,
        )
    else:
        langgraph = LangGraphServerRunner(settings.bl_agent_server_url, timeout_s=settings.bl_run_timeout_s)
    return {
        "echo": EchoRunner(),
        "langgraph": langgraph,
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

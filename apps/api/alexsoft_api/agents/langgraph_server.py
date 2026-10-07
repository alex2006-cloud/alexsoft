"""Adapter for the LangGraph Agent Server (apps/agent1 via `langgraph dev`, :2024).

Flow: POST /threads (or reuse thread_id) -> POST /threads/{id}/runs/stream (SSE) with stream_mode
["updates", "values"]. `updates` become steps, the last AI message of `values` is the answer.
The server's run_id is used as trace_id (it equals the LangSmith run id when tracing is enabled).
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .base import AgentError, Message, Meta, RunnerEvent, RunRequest, Step

log = logging.getLogger("alexsoft_api")


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and p.get("type") == "text":
                parts.append(str(p.get("text", "")))
        return "".join(parts)
    return ""


def _last_ai_text(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("type") in ("ai", "AIMessage", "assistant") or m.get("role") == "assistant":
            t = _text(m.get("content")).strip()
            if t:
                return t
    return ""


def _steps_from_update(update: dict[str, Any]) -> list[Step]:
    steps: list[Step] = []
    for node, payload in update.items():
        if not isinstance(payload, dict):
            steps.append(Step(str(node)))
            continue
        msgs = payload.get("messages")
        if isinstance(msgs, dict):  # some servers wrap messages
            msgs = [msgs]
        emitted = False
        for m in msgs or []:
            for call in m.get("tool_calls") or []:
                args = call.get("args") or {}
                detail = ", ".join(f"{k}={v}" for k, v in args.items()) if isinstance(args, dict) else str(args)
                steps.append(Step(f"tool:{call.get('name', '?')}", detail[:300] or None))
                emitted = True
            if m.get("type") == "tool":
                steps.append(Step(f"result:{m.get('name', 'tool')}", _text(m.get("content"))[:300] or None))
                emitted = True
        if not emitted:
            steps.append(Step(str(node)))
    return steps


async def _sse(response: httpx.Response) -> AsyncIterator[tuple[str, str]]:
    event, data = "message", []
    async for line in response.aiter_lines():
        if line == "":
            if data:
                yield event, "\n".join(data)
            event, data = "message", []
        elif line.startswith(":"):
            continue
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip())
    if data:
        yield event, "\n".join(data)


class LangGraphServerRunner:
    def __init__(self, default_url: str, *, timeout_s: float = 120.0,
                 transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._default_url = default_url.rstrip("/")
        self._timeout = timeout_s
        self._transport = transport

    async def run(self, req: RunRequest) -> AsyncIterator[RunnerEvent]:
        base = str(req.config.get("url") or self._default_url).rstrip("/")
        assistant = req.config.get("assistant_id")
        if not assistant:
            raise AgentError("Агент не настроен (assistant_id)")
        timeout = httpx.Timeout(self._timeout, connect=5.0)
        async with httpx.AsyncClient(base_url=base, timeout=timeout, trust_env=False,
                                     transport=self._transport) as client:
            thread_id = req.thread_id
            try:
                if not thread_id:
                    r = await client.post("/threads", json={})
                    r.raise_for_status()
                    thread_id = r.json()["thread_id"]
                yield Meta(thread_id=thread_id)
                body = {
                    "assistant_id": assistant,
                    "input": {"messages": [{"role": "user", "content": req.input}]},
                    "stream_mode": ["updates", "values"],
                }
                last_values: dict[str, Any] = {}
                async with client.stream("POST", f"/threads/{thread_id}/runs/stream", json=body) as resp:
                    if resp.status_code >= 400:
                        await resp.aread()
                        log.error("agent server %s: %s", resp.status_code, resp.text[:300])
                        raise AgentError("Агент временно недоступен")
                    async for event, data in _sse(resp):
                        try:
                            payload = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        if event == "metadata" and isinstance(payload, dict) and payload.get("run_id"):
                            yield Meta(trace_id=str(payload["run_id"]))
                        elif event == "updates" and isinstance(payload, dict):
                            for s in _steps_from_update(payload):
                                yield s
                        elif event == "values" and isinstance(payload, dict):
                            last_values = payload
                        elif event == "error":
                            log.error("agent server error event: %s", str(payload)[:300])
                            raise AgentError("Агент завершился с ошибкой")
            except httpx.HTTPError as e:
                log.error("agent server unreachable: %s", e)
                raise AgentError("Агент временно недоступен") from e
            answer = _last_ai_text(last_values.get("messages") or [])
            if not answer:
                raise AgentError("Агент не вернул ответ")
            yield Message(answer)

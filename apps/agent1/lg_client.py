"""HTTP client for the local LangGraph Agent Server (used by rmq_worker)."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

log = logging.getLogger("agent1.lg_client")


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


def _steps_from_update(update: dict[str, Any]) -> list[tuple[str, str | None]]:
    steps: list[tuple[str, str | None]] = []
    for node, payload in update.items():
        if not isinstance(payload, dict):
            steps.append((str(node), None))
            continue
        msgs = payload.get("messages")
        if isinstance(msgs, dict):
            msgs = [msgs]
        emitted = False
        for m in msgs or []:
            for call in m.get("tool_calls") or []:
                args = call.get("args") or {}
                detail = ", ".join(f"{k}={v}" for k, v in args.items()) if isinstance(args, dict) else str(args)
                steps.append((f"tool:{call.get('name', '?')}", (detail[:300] or None)))
                emitted = True
            if m.get("type") == "tool":
                steps.append((f"result:{m.get('name', 'tool')}", _text(m.get("content"))[:300] or None))
                emitted = True
        if not emitted:
            steps.append((str(node), None))
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


async def stream_run(
    *,
    base_url: str,
    assistant_id: str,
    user_input: str,
    thread_id: str | None = None,
    timeout_s: float = 120.0,
) -> AsyncIterator[dict[str, Any]]:
    """Yield event dicts: meta | step | message | error (same shape as BL rabbit replies)."""
    base = base_url.rstrip("/")
    timeout = httpx.Timeout(timeout_s, connect=5.0)
    async with httpx.AsyncClient(base_url=base, timeout=timeout, trust_env=False) as client:
        tid = thread_id
        try:
            if not tid:
                r = await client.post("/threads", json={})
                r.raise_for_status()
                tid = r.json()["thread_id"]
            yield {"type": "meta", "thread_id": tid}
            body = {
                "assistant_id": assistant_id,
                "input": {"messages": [{"role": "user", "content": user_input}]},
                "stream_mode": ["updates", "values"],
            }
            last_values: dict[str, Any] = {}
            async with client.stream("POST", f"/threads/{tid}/runs/stream", json=body) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    log.error("agent server %s: %s", resp.status_code, resp.text[:300])
                    yield {"type": "error", "detail": "Агент временно недоступен"}
                    return
                async for event, data in _sse(resp):
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if event == "metadata" and isinstance(payload, dict) and payload.get("run_id"):
                        yield {"type": "meta", "trace_id": str(payload["run_id"])}
                    elif event == "updates" and isinstance(payload, dict):
                        for name, detail in _steps_from_update(payload):
                            yield {"type": "step", "name": name, "detail": detail}
                    elif event == "values" and isinstance(payload, dict):
                        last_values = payload
                    elif event == "error":
                        yield {"type": "error", "detail": "Агент завершился с ошибкой"}
                        return
            answer = _last_ai_text(last_values.get("messages") or [])
            if not answer:
                yield {"type": "error", "detail": "Агент не вернул ответ"}
                return
            yield {"type": "message", "content": answer}
            yield {"type": "done"}
        except httpx.HTTPError as e:
            log.error("agent server unreachable: %s", e)
            yield {"type": "error", "detail": "Агент временно недоступен"}

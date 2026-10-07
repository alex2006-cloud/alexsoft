"""Stub agent without LLM: lets the whole chain (login -> quota -> run -> SSE) be tested before real agents."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

from .base import Message, Meta, RunnerEvent, RunRequest, Step


class EchoRunner:
    def __init__(self, delay_s: float = 0.25) -> None:
        self._delay = delay_s

    async def run(self, req: RunRequest) -> AsyncIterator[RunnerEvent]:
        yield Meta(thread_id=req.thread_id or uuid.uuid4().hex, trace_id=req.run_id)
        yield Step("receive", f"{len(req.input)} символов")
        await asyncio.sleep(self._delay)
        yield Step("process", "заглушка без LLM")
        await asyncio.sleep(self._delay)
        yield Message(f"Эхо: {req.input}")

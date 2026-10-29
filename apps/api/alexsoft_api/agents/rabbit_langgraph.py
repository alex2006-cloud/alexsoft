"""LangGraph runs via RabbitMQ: BL publishes, Agent worker consumes and replies with events.

Replaces the temporary direct HTTP BL→Agent link (ADR-0015 / cutover фаза 5).
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from urllib.parse import quote

import aio_pika
from aio_pika import DeliveryMode, Message as AmqpMessage
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from .base import AgentError, Message, Meta, RunnerEvent, RunRequest, Step

log = logging.getLogger("alexsoft_api")

QUEUE_DEFAULT = "alexsoft.agent.runs"


def rabbit_url(*, host: str, port: int, user: str, password: str, vhost: str = "/") -> str:
    vh = quote(vhost, safe="") if vhost != "/" else ""
    return f"amqp://{quote(user)}:{quote(password)}@{host}:{port}/{vh}"


class RabbitLangGraphRunner:
    """Publish a run job; stream Meta/Step/Message from the worker's reply queue."""

    def __init__(
        self,
        amqp_url: str,
        *,
        queue_name: str = QUEUE_DEFAULT,
        timeout_s: float = 120.0,
        default_agent_url: str = "http://127.0.0.1:2024",
    ) -> None:
        self._url = amqp_url
        self._queue = queue_name
        self._timeout = timeout_s
        self._default_agent_url = default_agent_url.rstrip("/")
        self._conn: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        if self._conn and not self._conn.is_closed:
            await self._conn.close()
        self._conn = None
        self._channel = None

    async def _channel_ready(self) -> AbstractChannel:
        async with self._lock:
            if self._channel and not self._channel.is_closed:
                return self._channel
            self._conn = await aio_pika.connect_robust(self._url)
            self._channel = await self._conn.channel()
            await self._channel.set_qos(prefetch_count=1)
            await self._channel.declare_queue(self._queue, durable=True)
            return self._channel

    async def run(self, req: RunRequest) -> AsyncIterator[RunnerEvent]:
        assistant = req.config.get("assistant_id")
        if not assistant:
            raise AgentError("Агент не настроен (assistant_id)")
        raw_url = str(req.config.get("url") or self._default_agent_url).rstrip("/")
        # Registry may still hold laptop seed (127.0.0.1); worker needs the compose DNS name.
        if "127.0.0.1" in raw_url or "localhost" in raw_url:
            agent_url = self._default_agent_url
        else:
            agent_url = raw_url

        ch = await self._channel_ready()
        # Exclusive auto-delete reply queue for this run (worker uses msg.reply_to).
        reply = await ch.declare_queue(exclusive=True, auto_delete=True)
        body = {
            "run_id": req.run_id,
            "agent_id": req.agent_id,
            "assistant_id": assistant,
            "input": req.input,
            "thread_id": req.thread_id,
            "user_sub": req.user_sub,
            "agent_url": agent_url,
        }
        await ch.default_exchange.publish(
            AmqpMessage(
                body=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                correlation_id=req.run_id,
                reply_to=reply.name,
                expiration=int(self._timeout * 1000),
            ),
            routing_key=self._queue,
        )
        log.info("published agent run %s to %s (reply=%s)", req.run_id, self._queue, reply.name)

        deadline = asyncio.get_event_loop().time() + self._timeout
        got_message = False
        try:
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise AgentError("Агент не ответил вовремя")
                try:
                    incoming = await asyncio.wait_for(reply.get(fail=False), timeout=min(remaining, 5.0))
                except asyncio.TimeoutError:
                    continue
                if incoming is None:
                    continue
                async with incoming.process(requeue=False):
                    try:
                        ev = json.loads(incoming.body.decode("utf-8"))
                    except json.JSONDecodeError:
                        log.warning("bad rabbit reply for run %s", req.run_id)
                        continue
                    if incoming.correlation_id and incoming.correlation_id != req.run_id:
                        continue
                    kind = ev.get("type")
                    if kind == "meta":
                        yield Meta(thread_id=ev.get("thread_id"), trace_id=ev.get("trace_id"))
                    elif kind == "step":
                        yield Step(str(ev.get("name") or "step"), ev.get("detail"))
                    elif kind == "message":
                        got_message = True
                        yield Message(str(ev.get("content") or ""))
                    elif kind == "error":
                        raise AgentError(str(ev.get("detail") or "Агент завершился с ошибкой"))
                    elif kind == "done":
                        if not got_message:
                            raise AgentError("Агент не вернул ответ")
                        return
        except AgentError:
            raise
        except Exception as e:
            log.error("rabbit langgraph runner failed: %s", e)
            raise AgentError("Агент временно недоступен") from e

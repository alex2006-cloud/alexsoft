"""RabbitMQ consumer: alexsoft.agent.runs → LangGraph Agent Server → reply queue.

Run: python rmq_worker.py  (env: RABBITMQ_*, BL_AGENT_QUEUE, BL_AGENT_SERVER_URL, BL_RUN_TIMEOUT_S)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from urllib.parse import quote

import aio_pika
from aio_pika import DeliveryMode, Message as AmqpMessage
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage

from lg_client import stream_run

log = logging.getLogger("agent1.rmq_worker")

QUEUE_DEFAULT = "alexsoft.agent.runs"


def _amqp_url() -> str:
    if url := (os.environ.get("RABBITMQ_URL") or "").strip():
        return url
    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = os.environ.get("RABBITMQ_PORT", "5672")
    user = os.environ.get("RABBITMQ_USER", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")
    vhost = os.environ.get("RABBITMQ_VHOST", "/")
    vh = quote(vhost, safe="") if vhost != "/" else ""
    return f"amqp://{quote(user)}:{quote(password)}@{host}:{port}/{vh}"


async def _reply(ch: AbstractChannel, reply_to: str, corr: str | None, ev: dict) -> None:
    await ch.default_exchange.publish(
        AmqpMessage(
            body=json.dumps(ev, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            correlation_id=corr,
            delivery_mode=DeliveryMode.NOT_PERSISTENT,
        ),
        routing_key=reply_to,
    )


async def _handle(
    ch: AbstractChannel,
    message: AbstractIncomingMessage,
    *,
    default_agent_url: str,
    timeout_s: float,
) -> None:
    async with message.process(requeue=False):
        reply_to = message.reply_to
        corr = message.correlation_id
        if not reply_to:
            log.error("job without reply_to, drop")
            return
        try:
            job = json.loads(message.body.decode("utf-8"))
        except json.JSONDecodeError:
            log.error("bad job json")
            return

        run_id = str(job.get("run_id") or corr or "")
        assistant = job.get("assistant_id")
        user_input = job.get("input") or ""
        agent_url = str(job.get("agent_url") or default_agent_url).rstrip("/")
        thread_id = job.get("thread_id")
        if not assistant or not user_input:
            await _reply(ch, reply_to, corr, {"type": "error", "detail": "Некорректное задание"})
            await _reply(ch, reply_to, corr, {"type": "done"})
            return

        log.info("consume run_id=%s assistant=%s", run_id, assistant)
        try:
            async for ev in stream_run(
                base_url=agent_url,
                assistant_id=str(assistant),
                user_input=str(user_input),
                thread_id=thread_id,
                timeout_s=timeout_s,
            ):
                await _reply(ch, reply_to, corr, ev)
                if ev.get("type") in ("error", "done"):
                    return
            await _reply(ch, reply_to, corr, {"type": "done"})
        except Exception as e:
            log.exception("worker failed run_id=%s: %s", run_id, e)
            await _reply(ch, reply_to, corr, {"type": "error", "detail": "Агент временно недоступен"})
            await _reply(ch, reply_to, corr, {"type": "done"})


async def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    queue_name = os.environ.get("BL_AGENT_QUEUE", QUEUE_DEFAULT)
    default_url = (os.environ.get("BL_AGENT_SERVER_URL") or "http://127.0.0.1:2024").rstrip("/")
    timeout_s = float(os.environ.get("BL_RUN_TIMEOUT_S") or "120")
    url = _amqp_url()

    conn = await aio_pika.connect_robust(url)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=1)
    queue = await ch.declare_queue(queue_name, durable=True)
    log.info("agent rmq worker listening on %s → %s", queue_name, default_url)

    async def on_message(message: AbstractIncomingMessage) -> None:
        await _handle(ch, message, default_agent_url=default_url, timeout_s=timeout_s)

    await queue.consume(on_message)

    stop = asyncio.Event()

    def _stop(*_: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            pass
    await stop.wait()
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

"""LangGraph Agent Server adapter against a fake server (httpx.MockTransport)."""

from __future__ import annotations

import json

import httpx
import pytest

from alexsoft_api.agents import AgentError, LangGraphServerRunner, Message, Meta, RunRequest, Step


def sse(*frames: tuple[str, dict]) -> bytes:
    return "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in frames).encode()


def req(**kw) -> RunRequest:
    base = dict(run_id="r1", agent_id="agent1-qa", input="2+2", thread_id=None, user_sub="u",
                config={"assistant_id": "agent1_qa"})
    base.update(kw)
    return RunRequest(**base)


async def collect(runner, request):
    return [e async for e in runner.run(request)]


def server(stream_body: bytes, *, status=200, calls=None):
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append((request.method, request.url.path, request.content))
        if request.url.path == "/threads":
            return httpx.Response(200, json={"thread_id": "th-1"})
        if request.url.path.endswith("/runs/stream"):
            return httpx.Response(status, content=stream_body, headers={"content-type": "text/event-stream"})
        return httpx.Response(404)
    return httpx.MockTransport(handler)


async def test_happy_path_steps_and_answer():
    body = sse(
        ("metadata", {"run_id": "run-77", "attempt": 1}),
        ("updates", {"agent": {"messages": [{"type": "ai", "content": "", "tool_calls": [
            {"name": "calculator", "args": {"expression": "2+2"}}]}]}}),
        ("updates", {"tools": {"messages": [{"type": "tool", "name": "calculator", "content": "4"}]}}),
        ("values", {"messages": [
            {"type": "human", "content": "2+2"},
            {"type": "ai", "content": [{"type": "text", "text": "Результат: 4"}]},
        ]}),
    )
    calls: list = []
    events = await collect(LangGraphServerRunner("http://agent", transport=server(body, calls=calls)), req())
    assert Meta(thread_id="th-1") in events and Meta(trace_id="run-77") in events
    steps = [e for e in events if isinstance(e, Step)]
    assert steps[0].name == "tool:calculator" and "expression=2+2" in steps[0].detail
    assert steps[1].name == "result:calculator" and steps[1].detail == "4"
    assert events[-1] == Message("Результат: 4")
    payload = json.loads(calls[-1][2])
    assert payload["assistant_id"] == "agent1_qa"
    assert payload["input"]["messages"][0] == {"role": "user", "content": "2+2"}


async def test_reuses_existing_thread():
    calls: list = []
    body = sse(("values", {"messages": [{"type": "ai", "content": "ok"}]}))
    events = await collect(LangGraphServerRunner("http://agent", transport=server(body, calls=calls)), req(thread_id="keep"))
    assert Meta(thread_id="keep") in events
    assert all(path != "/threads" for _, path, _ in calls)


@pytest.mark.parametrize("body,status", [
    (sse(("values", {"messages": [{"type": "human", "content": "x"}]})), 200),  # no AI answer
    (sse(("error", {"message": "boom"})), 200),
    (b"{}", 500),
])
async def test_errors_become_agent_error(body, status):
    with pytest.raises(AgentError):
        await collect(LangGraphServerRunner("http://agent", transport=server(body, status=status)), req())


async def test_unreachable_server_is_agent_error():
    def boom(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(AgentError):
        await collect(LangGraphServerRunner("http://agent", transport=httpx.MockTransport(boom)), req())


async def test_missing_assistant_is_agent_error():
    with pytest.raises(AgentError):
        await collect(LangGraphServerRunner("http://agent"), req(config={}))

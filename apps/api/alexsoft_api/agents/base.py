"""Agent adapter interface (ADR-0020). A runner turns one user input into a stream of events.

BL calls the Agent Platform directly (temporary link until the RabbitMQ broker of stage 6).
Adding the BP1 agent = a registry row (kind + config) and, if needed, a new runner kind.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class RunRequest:
    run_id: str
    agent_id: str
    input: str
    thread_id: str | None
    user_sub: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Step:
    name: str
    detail: str | None = None


@dataclass
class Message:
    """Part of or the whole answer. The last Message is the run output."""

    content: str


@dataclass
class Meta:
    """Identifiers learned during the run."""

    thread_id: str | None = None
    trace_id: str | None = None


RunnerEvent = Step | Message | Meta


class AgentRunner(Protocol):
    def run(self, req: RunRequest) -> AsyncIterator[RunnerEvent]: ...


class AgentError(Exception):
    """Failure that is safe to show to the user."""

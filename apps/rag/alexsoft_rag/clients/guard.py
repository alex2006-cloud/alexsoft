"""Guardrails interface. Real LLM Guard is a stage-6 component (ADR-0015, ADR-0017)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: str | None = None


class GuardrailsClient(Protocol):
    async def check_input(self, text: str) -> GuardResult: ...

    async def check_output(self, prompt: str, output: str) -> GuardResult: ...


class NoopGuard:
    """Allows everything. Used while LLM_GUARD_ENABLED=false (stage 5)."""

    async def check_input(self, text: str) -> GuardResult:
        return GuardResult(True)

    async def check_output(self, prompt: str, output: str) -> GuardResult:
        return GuardResult(True)


def build_guard(enabled: bool) -> GuardrailsClient:
    if enabled:
        raise RuntimeError(
            "LLM_GUARD_ENABLED=true but the LLM Guard client is not implemented yet "
            "(stage 6). Set LLM_GUARD_ENABLED=false."
        )
    return NoopGuard()

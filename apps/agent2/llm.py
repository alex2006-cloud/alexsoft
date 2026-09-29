"""Shared LiteLLM-backed LLM for Agent2 crews (ADR-0011: no direct provider calls)."""
from __future__ import annotations

import os

from crewai import LLM

DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL = "deepseek"

# Windows system SOCKS proxy breaks loopback OpenAI-compatible clients (httpx).
_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def _disable_env_proxies() -> None:
    for key in _PROXY_ENV_KEYS:
        os.environ.pop(key, None)


def gateway_base_url() -> str:
    base = (os.environ.get("OPENAI_BASE_URL") or "").strip()
    if base:
        return base
    gateway = (os.environ.get("AI_GATEWAY_URL") or DEFAULT_GATEWAY_URL).rstrip("/")
    return f"{gateway}/v1"


def model_name() -> str:
    """LiteLLM alias (e.g. deepseek), without openai/ prefix."""
    return (os.environ.get("AGENT2_MODEL") or "").strip() or DEFAULT_MODEL


def make_llm(temperature: float = 0.4) -> LLM:
    """OpenAI-compatible client pointed at alexsoft LiteLLM proxy."""
    _disable_env_proxies()
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("LITELLM_MASTER_KEY")
        or "sk-unset"
    )
    alias = model_name()
    return LLM(
        model=f"openai/{alias}",
        api_key=api_key,
        base_url=gateway_base_url(),
        temperature=temperature,
    )

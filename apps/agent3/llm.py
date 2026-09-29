"""Shared LiteLLM-backed model client for Agent3 (ADR-0011: no direct provider calls)."""
from __future__ import annotations

import os

from autogen_core.models import ModelFamily, ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient

DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL = "deepseek"

# Windows system SOCKS proxy breaks loopback OpenAI-compatible clients.
_PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)

# LiteLLM aliases (deepseek, qwen, …) are not OpenAI-hosted names — model_info required.
_DEFAULT_MODEL_INFO: ModelInfo = {
    "vision": False,
    "function_calling": True,
    "json_output": False,
    "family": ModelFamily.UNKNOWN,
    "structured_output": False,
}


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
    return (os.environ.get("AGENT3_MODEL") or "").strip() or DEFAULT_MODEL


def make_model_client() -> OpenAIChatCompletionClient:
    """OpenAI-compatible client pointed at alexsoft LiteLLM proxy."""
    _disable_env_proxies()
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("LITELLM_MASTER_KEY")
        or "sk-unset"
    )
    return OpenAIChatCompletionClient(
        model=model_name(),
        api_key=api_key,
        base_url=gateway_base_url(),
        model_info=_DEFAULT_MODEL_INFO,
    )

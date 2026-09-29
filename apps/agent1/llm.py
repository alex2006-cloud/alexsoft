"""Shared LiteLLM-backed chat model for Agent1 graphs (ADR-0011: no direct provider calls)."""
from __future__ import annotations

import os

import httpx
from langchain_openai import ChatOpenAI

DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL = "deepseek"


def gateway_base_url() -> str:
    base = (os.environ.get("OPENAI_BASE_URL") or "").strip()
    if base:
        return base
    gateway = (os.environ.get("AI_GATEWAY_URL") or DEFAULT_GATEWAY_URL).rstrip("/")
    return f"{gateway}/v1"


def model_name() -> str:
    return (os.environ.get("AGENT1_MODEL") or "").strip() or DEFAULT_MODEL


def make_llm(temperature: float = 0) -> ChatOpenAI:
    api_key = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("LITELLM_MASTER_KEY")
        or "sk-unset"
    )
    return ChatOpenAI(
        model=model_name(),
        api_key=api_key,
        base_url=gateway_base_url(),
        temperature=temperature,
        # Windows registry SOCKS proxy would otherwise break the loopback call to LiteLLM;
        # empty socket options keep langchain-openai from re-injecting its own transport.
        http_client=httpx.Client(trust_env=False),
        http_async_client=httpx.AsyncClient(trust_env=False),
        http_socket_options=(),
    )

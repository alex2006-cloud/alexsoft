"""Build the LangFlow copy of the agent1 Q&A product.

Flow shape: Chat Input -> Agent -> Chat Output, with the Alexsoft Calculator component
wired into the Agent's tools. The Agent talks to LiteLLM through LangFlow's
"OpenAI Compatible" provider, so the gateway stays the single way out to models.

Math and prompts are not duplicated here: the calculator component loads
apps/agent1/calculator.py and this script reads the system prompt from
apps/agent1/prompts.py, the same files the LangGraph agent uses.

Runs with the LangFlow venv python (it imports lfx); call it through
infra\\agent1\\langflow-build-qa-flow.ps1.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
import sys
import uuid
from pathlib import Path

FLOW_NAME = "agent1_qa"
# Derived, not random: the flow keeps one id across rebuilds, so its UI link and its
# git snapshot filename (apps/agent1/langflow/flows/agent1_qa--<id>.json) stay put.
FLOW_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "alexsoft/apps/agent1/langflow/agent1_qa"))
FLOW_DESCRIPTION = "Q&A-агент с калькулятором (продукт 5.2) в LangFlow: LiteLLM + Alexsoft Calculator."
CALCULATOR_CLASS = "AlexsoftCalculatorComponent"
PROVIDER = "OpenAI Compatible"
BASE_URL_VARIABLE = "OPENAI_COMPATIBLE_BASE_URL"
API_KEY_VARIABLE = "OPENAI_COMPATIBLE_API_KEY"


def quiet_http_logs() -> None:
    """lfx turns on INFO logging, which buries this script's output in httpx traffic."""
    import logging

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def disable_proxies() -> None:
    """Windows registry SOCKS proxies break loopback calls; keep this process direct."""
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    for key in list(os.environ):
        if key.lower().endswith("_proxy") and key.lower() != "no_proxy":
            del os.environ[key]

    import httpx

    def wrap(orig):
        def init(self, *args, **kwargs):
            kwargs["trust_env"] = False
            kwargs["proxy"] = None
            return orig(self, *args, **kwargs)

        return init

    httpx.Client.__init__ = wrap(httpx.Client.__init__)
    httpx.AsyncClient.__init__ = wrap(httpx.AsyncClient.__init__)


def repo_root() -> Path:
    env_root = os.environ.get("ALEXSOFT_REPO_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parents[2]


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_prompts(agent1_dir: Path):
    path = agent1_dir / "prompts.py"
    spec = importlib.util.spec_from_file_location("alexsoft_agent1_prompts", path)
    if spec is None or spec.loader is None:
        msg = f"Не удалось загрузить {path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unwrap(tool):
    """FastMCP may hand back a tool wrapper; the plain coroutine lives on .fn."""
    return getattr(tool, "fn", tool)


def access_token(server_url: str) -> str:
    import httpx

    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{server_url}/api/v1/auto_login")
        response.raise_for_status()
        token = response.json().get("access_token")
    if not token:
        msg = "LangFlow не выдал токен через /api/v1/auto_login"
        raise RuntimeError(msg)
    return token


def ensure_variable(server_url: str, token: str, name: str, value: str, var_type: str) -> str:
    """Create or refresh a LangFlow global variable; returns what happened."""
    import httpx

    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=f"{server_url}/api/v1", headers=headers, timeout=60.0) as client:
        existing = client.get("/variables/")
        existing.raise_for_status()
        for item in existing.json():
            if item.get("name") != name:
                continue
            response = client.patch(
                f"/variables/{item['id']}",
                json={"id": item["id"], "name": name, "value": value, "type": var_type},
            )
            response.raise_for_status()
            return "обновлена"

        response = client.post(
            "/variables/",
            json={"name": name, "value": value, "type": var_type, "default_fields": []},
        )
        response.raise_for_status()
        return "создана"


async def pin_flow_id(client, temp_id: str) -> str:
    """Re-upload the built flow under FLOW_ID (LangFlow assigns a fresh id on create)."""
    if temp_id == FLOW_ID:
        return temp_id

    flow = await client.get(f"/flows/{temp_id}")
    await client.delete(f"/flows/{temp_id}")
    payload = {
        "id": FLOW_ID,
        "name": FLOW_NAME,
        "description": FLOW_DESCRIPTION,
        "data": flow["data"],
    }
    if flow.get("folder_id"):
        payload["folder_id"] = flow["folder_id"]
    created = await client.post("/flows/", json_data=payload)
    return created["id"]


def flow_spec(calculator_type: str) -> str:
    return f"""name: {FLOW_NAME}
description: {FLOW_DESCRIPTION}

nodes:
  input: ChatInput
  agent: Agent
  calc: {calculator_type}
  output: ChatOutput

edges:
  input.message -> agent.input_value
  calc.component_as_tool -> agent.tools
  agent.response -> output.input_value
"""


async def build(args: argparse.Namespace) -> int:
    from lfx.mcp import server as lf
    from lfx.mcp.client import LangflowClient

    quiet_http_logs()  # after lfx: importing it installs the noisy INFO handlers

    server_url = f"http://{args.host}:{args.port}"
    root = repo_root()
    agent1_dir = root / "apps" / "agent1"
    env_values = read_env_file(root / ".env")

    gateway_url = (env_values.get("AI_GATEWAY_URL") or "http://127.0.0.1:8080").rstrip("/")
    base_url = f"{gateway_url}/v1"
    api_key = env_values.get("LITELLM_MASTER_KEY", "")
    model = args.model or env_values.get("AGENT1_MODEL") or "deepseek"
    prompts = load_prompts(agent1_dir)

    token = access_token(server_url)
    print(f"LangFlow: {server_url} (авторизация через auto_login)")

    print(f"{BASE_URL_VARIABLE} -> {base_url}: " + ensure_variable(server_url, token, BASE_URL_VARIABLE, base_url, "Generic"))
    if api_key:
        print(f"{API_KEY_VARIABLE} (LITELLM_MASTER_KEY): " + ensure_variable(server_url, token, API_KEY_VARIABLE, api_key, "Credential"))
    else:
        print(f"ВНИМАНИЕ: LITELLM_MASTER_KEY пуст в .env, {API_KEY_VARIABLE} не задана")

    client = LangflowClient(server_url=server_url, access_token=token)
    lf._set_client(client)  # noqa: SLF001 - the MCP tools read this module-level client

    registry = await lf._get_registry()  # noqa: SLF001
    matches = [name for name in registry if CALCULATOR_CLASS in name]
    if not matches:
        print(
            f"ОШИБКА: компонент {CALCULATOR_CLASS} не найден в LangFlow. "
            "Запустите start-langflow.ps1 (он задаёт LANGFLOW_COMPONENTS_PATH).",
            file=sys.stderr,
        )
        return 1
    calculator_type = matches[0]
    print(f"Компонент калькулятора: {calculator_type}")

    for flow in await unwrap(lf.list_flows)(FLOW_NAME):
        if flow.get("name") == FLOW_NAME:
            await unwrap(lf.delete_flow)(flow["id"])
            print(f"Удалён прежний флоу {FLOW_NAME} ({flow['id']})")

    info = await unwrap(lf.create_flow_from_spec)(flow_spec(calculator_type), validate=False)
    flow_id = info["id"]
    agent_id = info["node_id_map"]["agent"]
    print(f"Создан флоу {FLOW_NAME}: {flow_id}")

    await unwrap(lf.configure_component)(
        flow_id,
        agent_id,
        {
            "system_prompt": prompts.SYSTEM_PROMPT,
            "model": [{"name": model, "provider": PROVIDER, "metadata": {}}],
            "add_calculator_tool": False,
            "add_current_date_tool": False,
        },
    )
    print(f"Agent настроен: модель {model} через {PROVIDER}, промпт из apps/agent1/prompts.py")

    flow_id = await pin_flow_id(client, flow_id)

    validation = await unwrap(lf.validate_flow)(flow_id)
    if not validation.get("valid", False):
        errors = "; ".join(e.get("error", "?") for e in validation.get("errors", []))
        print(f"ОШИБКА валидации: {errors}", file=sys.stderr)
        return 1
    print("Валидация графа пройдена")

    if args.ask:
        result = await unwrap(lf.run_flow)(flow_id, input_value=args.ask)
        print(f"\nВопрос: {args.ask}\nОтвет: {extract_text(result)}")

    print(f"\nОткрыть в UI: {server_url}/flow/{flow_id}")
    return 0


def extract_text(result: dict) -> str:
    """Pull the chat text out of a /run response."""
    for output in result.get("outputs", []) or []:
        for item in output.get("outputs", []) or []:
            results = item.get("results") or {}
            message = results.get("message") or {}
            if isinstance(message, dict):
                text = message.get("text") or (message.get("data") or {}).get("text")
                if text:
                    return text
    return str(result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the agent1_qa flow in LangFlow")
    parser.add_argument("--host", default=os.environ.get("LANGFLOW_HOST", "127.0.0.1"))
    parser.add_argument("--port", default=os.environ.get("LANGFLOW_PORT", "7860"))
    parser.add_argument("--model", default=None, help="LiteLLM model name (default: AGENT1_MODEL or deepseek)")
    parser.add_argument("--ask", default=None, help="Optional smoke question to run after building")
    args = parser.parse_args()

    disable_proxies()
    return asyncio.run(build(args))


if __name__ == "__main__":
    sys.exit(main())

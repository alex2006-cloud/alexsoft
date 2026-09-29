"""Ask the LangFlow flow a question from the CLI (smoke check for the agent1_qa product).

LangFlow's /run endpoint needs an API key even with auto-login, so the key is created
once and cached next to the LangFlow install (never in the repo).

Runs with the LangFlow venv python; call it through infra\\agent1\\langflow-ask.ps1.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

DEFAULT_FLOW = "agent1_qa"
KEY_NAME = "alexsoft-agent1-cli"


def disable_proxies() -> None:
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    for key in list(os.environ):
        if key.lower().endswith("_proxy") and key.lower() != "no_proxy":
            del os.environ[key]


def key_cache_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home()))
    return Path(local_app_data) / "LangFlow" / "cli-api-key.txt"


def create_api_key(client, bearer: dict[str, str]) -> str:
    response = client.post("/api_key/", headers=bearer, json={"name": KEY_NAME})
    response.raise_for_status()
    api_key = response.json().get("api_key")
    if not api_key:
        msg = "LangFlow не вернул api_key"
        raise RuntimeError(msg)
    cache = key_cache_path()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(api_key, encoding="ascii")
    return api_key


def flow_id_by_name(client, bearer: dict[str, str], name: str) -> str:
    response = client.get("/flows/", headers=bearer, params={"get_all": "true", "header_flows": "true"})
    response.raise_for_status()
    for flow in response.json():
        if flow.get("name") == name:
            return flow["id"]
    msg = f"Флоу '{name}' не найден. Соберите его: infra\\agent1\\langflow-build-qa-flow.ps1"
    raise RuntimeError(msg)


def answer_text(result: dict) -> str:
    for output in result.get("outputs", []) or []:
        for item in output.get("outputs", []) or []:
            message = (item.get("results") or {}).get("message") or {}
            if isinstance(message, dict):
                text = message.get("text") or (message.get("data") or {}).get("text")
                if text:
                    return text
    return str(result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the LangFlow agent1_qa flow")
    parser.add_argument("questions", nargs="+", help="One or more questions, asked in the same session")
    parser.add_argument("--flow", default=DEFAULT_FLOW)
    parser.add_argument("--session", default="cli", help="Session id: same id keeps the conversation context")
    parser.add_argument("--host", default=os.environ.get("LANGFLOW_HOST", "127.0.0.1"))
    parser.add_argument("--port", default=os.environ.get("LANGFLOW_PORT", "7860"))
    args = parser.parse_args()

    disable_proxies()
    import httpx

    base_url = f"http://{args.host}:{args.port}/api/v1"
    with httpx.Client(base_url=base_url, timeout=600.0, trust_env=False) as client:
        token = client.get("/auto_login").json().get("access_token")
        bearer = {"Authorization": f"Bearer {token}"} if token else {}

        cache = key_cache_path()
        api_key = cache.read_text(encoding="ascii").strip() if cache.is_file() else ""
        if not api_key:
            api_key = create_api_key(client, bearer)

        flow_id = flow_id_by_name(client, bearer, args.flow)

        for question in args.questions:
            payload = {
                "input_value": question,
                "input_type": "chat",
                "output_type": "chat",
                "session_id": args.session,
            }
            response = client.post(f"/run/{flow_id}", headers={**bearer, "x-api-key": api_key}, json=payload)
            if response.status_code in (401, 403):
                api_key = create_api_key(client, bearer)
                response = client.post(f"/run/{flow_id}", headers={**bearer, "x-api-key": api_key}, json=payload)
            if response.status_code != 200:
                print(f"HTTP {response.status_code}: {response.text[:800]}", file=sys.stderr)
                return 1
            print(f"> {question}")
            print(answer_text(response.json()))
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Agent 1 (LangGraph stack)

Этап **5.2**: LangChain + LangGraph + LangSmith Studio + LangFlow.  
Все LLM-вызовы только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0012](../../artifacts/adr/0012-agent1-langgraph-stack.md)).

## Локально

Скрипты: [`infra/agent1/README.md`](../../infra/agent1/README.md).

| Сервис | URL |
|--------|-----|
| LiteLLM | http://127.0.0.1:8080 |
| Studio Agent Server | http://127.0.0.1:2024 |
| Studio UI | https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024 |
| LangFlow | http://127.0.0.1:7860 |

## Графы

- `graph.py` — echo без LLM (smoke Studio).
- `graph_llm.py` — chat через LiteLLM (`AGENT1_MODEL`, по умолчанию `qwen`).

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\smoke-litellm.ps1
```

## LangFlow → LiteLLM

В UI добавьте OpenAI-compatible модель:

- Base URL: `http://127.0.0.1:8080/v1`
- API key: значение `LITELLM_MASTER_KEY`
- Model: `qwen`

Не указывайте DashScope напрямую.

## LangFlow → git

Snapshots of your flows: [`langflow/flows/`](langflow/flows/).  
Enable once: `powershell -ExecutionPolicy Bypass -File infra\githooks\install-hooks.ps1` — then every `git commit` auto-exports and stages them.

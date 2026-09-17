# Agent 1 stack (LangChain / LangGraph / Studio / LangFlow)

Нативная установка этапа **5.2** (Windows). LLM только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md)).  
Порядок: LangChain → LangGraph → LangSmith Studio → LangFlow → связка с LiteLLM. AI-продукт — отдельно.

## Где лежит на машине

| Компонент | Путь |
|-----------|------|
| Venv LangChain + LangGraph + CLI | `%LOCALAPPDATA%\AlexsoftAgent1\venv\` |
| Venv LangFlow | `%LOCALAPPDATA%\LangFlow\venv\` |
| Граф / `langgraph.json` | [`apps/agent1`](../../apps/agent1/) |

Порты (loopback): Studio/Agent Server **2024**, LangFlow **7860**, LiteLLM **8080**.

## Шаг 1 — LangChain

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\install-langchain.ps1
```

## Шаг 2 — LangGraph

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\install-langgraph.ps1
```

## Шаг 3 — LangSmith Studio (local Agent Server)

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\install-studio.ps1
powershell -ExecutionPolicy Bypass -File infra\agent1\start-studio.ps1
```

API: http://127.0.0.1:2024  
Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024  
Для GUI нужен `LANGSMITH_API_KEY` в `.env` (бесплатный аккаунт smith.langchain.com). Без ключа локальный сервер всё равно работает.

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\stop-studio.ps1
```

## Шаг 4 — LangFlow

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\install-langflow.ps1
powershell -ExecutionPolicy Bypass -File infra\agent1\start-langflow.ps1
```

UI: http://127.0.0.1:7860  

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\stop-langflow.ps1
```

При ошибках сборки на Windows установите [MSVC Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

## LangFlow → git

Снимки твоих flow: `apps/agent1/langflow/flows/`.  
Один раз: `powershell -ExecutionPolicy Bypass -File infra\githooks\install-hooks.ps1`  
Дальше при обычном `git commit` export идёт сам (Starter Projects-шаблоны не копируются; ключи в JSON затираются).

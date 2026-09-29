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

`stop-studio.ps1` снимает всё дерево сервера (воркеры раньше лаунчера) и дочищает воркеров, чей
лаунчер уже умер: такой воркер наследует слушающий сокет 2024 и продолжает отдавать старый набор
графов. `start-studio.ps1` вызывает ту же очистку перед запуском, поэтому новые графы из
`langgraph.json` подхватываются без ручного вмешательства.

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

## Продукт: Q&A-агент с калькулятором

Граф `agent1_qa` в терминале (нужны LiteLLM и venv Agent1):

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\chat-qa.ps1
powershell -ExecutionPolicy Bypass -File infra\agent1\chat-qa.ps1 --once "2^10 + sqrt(16)"
```

Тот же продукт в LangFlow — флоу `agent1_qa` с компонентом Alexsoft Calculator
(нужен запущенный LangFlow):

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-build-qa-flow.ps1
powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-ask.ps1 -Ask "sqrt(144) + 2**10"
powershell -ExecutionPolicy Bypass -File infra\agent1\langflow-ask.ps1 -Session s1 -Ask "а раздели это на 4"
```

`langflow-build-qa-flow.ps1` пересоздаёт флоу и пишет глобальные переменные LangFlow для LiteLLM.
`langflow-ask.ps1` спрашивает флоу из терминала; `/run` требует API-ключ даже при auto-login,
поэтому ключ создаётся один раз и кешируется в `%LOCALAPPDATA%\LangFlow\cli-api-key.txt`
(вне репозитория). Один `-Session` = один диалог с памятью.

Описание продукта: [`apps/agent1/README.md`](../../apps/agent1/README.md).

## LangFlow → git

Снимки твоих flow: `apps/agent1/langflow/flows/`.  
Один раз: `powershell -ExecutionPolicy Bypass -File infra\githooks\install-hooks.ps1`  
Дальше при обычном `git commit` export идёт сам (Starter Projects-шаблоны не копируются; ключи в JSON затираются).

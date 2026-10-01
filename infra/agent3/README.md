# Agent 3 (AutoGen)

Нативная установка этапа **5.4** (Windows). LLM только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md)).  
Локального Studio нет — smoke через CLI. Отдельный продукт агента 3 не в 5.4; первый AI-агент с RAG — ROADMAP **5.7** после **5.5**/**5.6**.

## Где лежит на машине

| Компонент | Путь |
|-----------|------|
| Venv AutoGen | `%LOCALAPPDATA%\AlexsoftAgent3\venv\` |
| Код | [`apps/agent3`](../../apps/agent3/) |

LiteLLM: **8080** (общий шлюз).

## Шаг 1 — установить AutoGen

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent3\install-autogen.ps1
```

## Шаг 2 — smoke через LiteLLM

LiteLLM должен быть запущен (`infra/litellm` / `scripts/dev-up.ps1`).

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent3\smoke-litellm.ps1
```

Модель: `AGENT3_MODEL` в `.env` (по умолчанию `deepseek`).

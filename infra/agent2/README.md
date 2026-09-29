# Agent 2 (CrewAI)

Нативная установка этапа **5.3** (Windows). LLM только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0013](../../artifacts/adr/0013-agent2-crewai.md)).  
Официального локального GUI нет — продукт через CLI.

## Где лежит на машине

| Компонент | Путь |
|-----------|------|
| Venv CrewAI | `%LOCALAPPDATA%\AlexsoftAgent2\venv\` |
| Код crew | [`apps/agent2`](../../apps/agent2/) |

LiteLLM: **8080** (общий шлюз).

## Шаг 1 — установить CrewAI

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent2\install-crewai.ps1
```

## Шаг 2 — smoke через LiteLLM

LiteLLM должен быть запущен (`infra/litellm` / `scripts/dev-up.ps1`).

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent2\smoke-litellm.ps1
```

## Продукт: черновик поста

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent2\run-post.ps1
powershell -ExecutionPolicy Bypass -File infra\agent2\run-post.ps1 --once "Анонс мини-игры Контур"
```

Описание: [`apps/agent2/README.md`](../../apps/agent2/README.md).

Модель: `AGENT2_MODEL` в `.env` (по умолчанию `deepseek`).

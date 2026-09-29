# Agent 3 (AutoGen)

Этап **5.4**: Microsoft AutoGen AgentChat.  
Все LLM-вызовы только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md)).

Локального Studio нет — smoke через CLI (`infra/agent3`). AI-продукт агента 3 — после установки AutoGen, n8n и Dify.

## Локально

Скрипты: [`infra/agent3/README.md`](../../infra/agent3/README.md).

| Сервис | URL |
|--------|-----|
| LiteLLM | http://127.0.0.1:8080 |

Модель: `AGENT3_MODEL` (по умолчанию `deepseek`) → `OpenAIChatCompletionClient` на шлюз.

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent3\smoke-litellm.ps1
```

## Продукт

Пока не реализован (ROADMAP 5.4 — стек сначала).

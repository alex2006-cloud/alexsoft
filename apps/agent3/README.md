# Agent 3 (AutoGen)

Этап **5.4**: Microsoft AutoGen AgentChat.  
> **Lab этапа 5**, выполнено. В целевую архитектуру ([ADR-0015](../../artifacts/adr/0015-target-architecture-stacks.md)) не входит.

Все LLM-вызовы только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md)).

Локального Studio нет — smoke через CLI (`infra/agent3`). Отдельный продукт агента 3 снят с 5.4; первый AI-агент с RAG — этап **5.7** (после **5.5** docs и **5.6** RAG).

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

Не в 5.4. Первый AI-агент с RAG — [ROADMAP](../../ROADMAP.md) **5.7** (после **5.5** docs и **5.6** RAG).

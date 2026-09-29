# Agent 2 (CrewAI)

Этап **5.3**: CrewAI multi-agent crew.  
Все LLM-вызовы только через **LiteLLM** ([ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md), [ADR-0013](../../artifacts/adr/0013-agent2-crewai.md)).

Официального локального GUI нет — продукт запускается из CLI (`infra/agent2`).

## Локально

Скрипты: [`infra/agent2/README.md`](../../infra/agent2/README.md).

| Сервис | URL |
|--------|-----|
| LiteLLM | http://127.0.0.1:8080 |

Модель: `AGENT2_MODEL` (по умолчанию `deepseek`) → в коде `openai/{AGENT2_MODEL}` на шлюз.

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent2\smoke-litellm.ps1
```

## Продукт: черновик поста

Crew `Researcher → Writer → Editor` (`Process.sequential`):

1. **Researcher** — краткий бриф по теме (аудитория, тезисы, угол).
2. **Writer** — черновик поста по брифу.
3. **Editor** — финальный текст поста.

Вход — тема/бриф (строка), выход — итоговый текст Editor. Внешних tools пока нет; детали сценария (тон, канал, длина) уточняются позже — промпты в [`prompts.py`](prompts.py).

CLI:

```powershell
powershell -ExecutionPolicy Bypass -File infra\agent2\run-post.ps1 --once "Анонс мини-игры Контур на osipcraft.ru"
```

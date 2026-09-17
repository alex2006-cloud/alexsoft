# AI Gateway

По [CONCEPT.md](../../CONCEPT.md) и [ADR-0011](../../artifacts/adr/0011-ai-gateway-litellm.md): **LiteLLM** — единый шлюз к облачным LLM (**DeepSeek** подключён; Qwen в конфиге; далее ChatGPT и др.).

Не путать с **API Gateway** / **IAM** (этап облака, инструмент TBD).

Локальный запуск (Windows): [infra/litellm/README.md](../../infra/litellm/README.md).

## Модели через шлюз

| Алиас | Статус | Ключ |
|-------|--------|------|
| `deepseek` | подключён | `DEEPSEEK_API_KEY` |
| `qwen` | в `config.yaml` | `DASHSCOPE_API_KEY` |

## Порядок этапа 5 (ROADMAP)

| Шаг | Что |
|-----|-----|
| 5.1 | **LiteLLM** + DeepSeek (+ Qwen в конфиге) |
| 5.2 | Агент 1 LangGraph + LangSmith Studio (IDE) + LangFlow → AI-продукт |
| 5.3 | Агент 2 **CrewAI** → AI-продукт |
| 5.4 | Агент 3 **AutoGen** → AI-продукт |
| 5.5 | ВБД (Qdrant\|Weaviate) + RAG (3 слоя) → продукт с RAG |
| 5.6 | LangSmith (**платформа**, не Studio) |
| 5.7 | Redis-кеш ответов + RabbitMQ (**после** ИИ-блока, не критично сейчас) |

Все агенты ходят в модели **через LiteLLM**.

**Статус:** 5.1 — LiteLLM + DeepSeek (smoke через шлюз ок). 5.2 — стек Agent1 установлен и связан с LiteLLM (AI-продукт ещё нет). См. [ROADMAP.md](../../ROADMAP.md), [infra/agent1](../../infra/agent1/), [ADR-0012](../../artifacts/adr/0012-agent1-langgraph-stack.md).

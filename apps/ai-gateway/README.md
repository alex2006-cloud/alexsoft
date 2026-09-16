# AI Gateway

По [CONCEPT.md](../../CONCEPT.md): **LiteLLM** — единый шлюз к облачным LLM (Qwen, DeepSeek, ChatGPT и др.).

Не путать с **API Gateway** / **IAM** (этап облака, инструмент TBD).

## Порядок этапа 5 (ROADMAP)

| Шаг | Что |
|-----|-----|
| 5.1 | **LiteLLM** + Qwen |
| 5.2 | Агент 1 LangGraph + LangSmith Studio (IDE) + LangFlow → AI-продукт |
| 5.3 | Агент 2 **CrewAI** → AI-продукт |
| 5.4 | Агент 3 **AutoGen** → AI-продукт |
| 5.5 | ВБД (Qdrant\|Weaviate) + RAG (3 слоя) → продукт с RAG |
| 5.6 | LangSmith (**платформа**, не Studio) |
| 5.7 | Redis-кеш ответов + RabbitMQ (**после** ИИ-блока, не критично сейчас) |

Все агенты ходят в модели **через LiteLLM**.

**Статус:** этап 5 — в работе. См. [ROADMAP.md](../../ROADMAP.md).

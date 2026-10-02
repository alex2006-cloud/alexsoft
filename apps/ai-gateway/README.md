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
| 5.3 | Второй агент → AI-продукт (lab, выполнено) |
| 5.4 | Стек агентов через LiteLLM (lab, выполнено; **без** продукта агента 3; в целевой остаётся **Dify**) |
| 5.5 | **Architecture and documentation** (БК1, draw.io, Structurizr, C4, Component Diagram, OpenAPI RAG, ADR-0015, sync docs) |
| 5.6 | ВБД + RAG (`apps/rag`) |
| 5.7 | **Первый AI-агент с RAG** |

Все агенты ходят в модели **через LiteLLM**.

**Статус:** 5.1 — LiteLLM + DeepSeek. 5.2 — Agent1 + продукт Q&A/калькулятор. 5.3 — Agent2 + черновик поста (lab). 5.4 — стек агентов (lab, [ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md)); продукт агента 3 снят с 5.4 — RAG в **5.6**, первый AI-агент с RAG в **5.7** (после **5.5**). См. [ROADMAP.md](../../ROADMAP.md).

### Клиенты 5.4 → LiteLLM

В целевой архитектуре LiteLLM — единственный путь к LLM для Agent Platform, RAG и LLM Guard ([ADR-0015](../../artifacts/adr/0015-target-architecture-stacks.md)).

| Клиент | Base URL | Ключ | Модель |
|--------|----------|------|--------|
| Lab-агент 3 (`apps/agent3`) | `AI_GATEWAY_URL/v1` | `LITELLM_MASTER_KEY` | `AGENT3_MODEL` |
| Lab n8n (`infra/n8n`) | `http://127.0.0.1:8080/v1` | master key | `deepseek` |
| Dify (из контейнера) | `http://host.docker.internal:8080/v1` | master key | `deepseek` |

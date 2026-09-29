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
| 5.4 | AutoGen + **n8n** + **Dify** (через LiteLLM) → затем AI-продукт агента 3 |
| 5.5 | **Architecture and documentation** (Structurizr, ADR, CONCEPT/ROADMAP/AGENTS) |
| 5.6 | ВБД (Qdrant\|Weaviate) + RAG (3 слоя) → продукт с RAG |
| 5.7 | LangSmith (**платформа**, не Studio) |

Все агенты ходят в модели **через LiteLLM**.

**Статус:** 5.1 — LiteLLM + DeepSeek. 5.2 — Agent1 + продукт Q&A/калькулятор. 5.3 — Agent2 CrewAI + черновик поста. 5.4 — стек AutoGen + n8n + Dify ([ADR-0014](../../artifacts/adr/0014-agent3-autogen-n8n-dify.md): [`infra/agent3`](../../infra/agent3/), [`infra/n8n`](../../infra/n8n/), [`infra/dify`](../../infra/dify/)); продукт агента 3 ещё нет. См. [ROADMAP.md](../../ROADMAP.md).

### Клиенты 5.4 → LiteLLM

| Клиент | Base URL | Ключ | Модель |
|--------|----------|------|--------|
| Agent3 AutoGen | `AI_GATEWAY_URL/v1` | `LITELLM_MASTER_KEY` | `AGENT3_MODEL` |
| n8n (OpenAI cred) | `http://127.0.0.1:8080/v1` | master key | `deepseek` |
| Dify (из контейнера) | `http://host.docker.internal:8080/v1` | master key | `deepseek` |

# Руководство для агентов (alexsoft)

Это монорепозиторий персональной платформы **alexsoft — Personal Ecosystem Lab**.

## Принципы

- Architecture-as-code: источник правды по архитектуре — `artifacts/structurizr/workspace.dsl`. Диаграммы не рисовать «вручную в вакууме»; сначала DSL, потом экспорт.
- ADR обязательны для решений, которые меняют стек, границы сервисов или данные. Шаблон: `artifacts/adr/0000-template.md`.
- Секреты только в `.env` (локально) и в GitHub Secrets. В репозиторий — `.env.example`.
- Новый продукт = отдельный сервис в `apps/` + запись в Structurizr + ссылка с лендинга.
- Стек и этапы — `CONCEPT.md` и `ROADMAP.md`. Не внедрять k3s/Kafka/векторную БД раньше этапа.
- Игры: код в `apps/games`, не в лендинге ([ADR-0010](artifacts/adr/0010-games-static-app.md)).

## Стек (не подменять без ADR)

Лендинг: Next.js. Игры: Next.js в `apps/games` (`basePath: /games`), статика мержится в CI с лендингом ([ADR-0010](artifacts/adr/0010-games-static-app.md)). CI: GitHub Actions. Оркестрация: нативно → Docker Compose (VPS) → k3s. Данные: PostgreSQL, MinIO, Redis (Memurai локально). BI: Metabase ([ADR-0009](artifacts/adr/0009-metabase-native-local.md)). Брокер: RabbitMQ — **после** ИИ-блока этапа 5. Наблюдаемость инфра: Grafana, Loki, Prometheus, Alloy ([ADR-0008](artifacts/adr/0008-observability-native-local.md)). **AI Gateway (LLM): LiteLLM.** LLM: Qwen, DeepSeek, ChatGPT. Агент 1: LangGraph + LangSmith Studio (IDE) + LangFlow. Агент 2: CrewAI. Агент 3: AutoGen. ВБД: Qdrant или Weaviate. RAG: `apps/rag`. LangSmith (платформа) — LLM-трейсы/evals. Redis-кеш ответов AI — после ИИ-блока. **API Gateway** / **IAM** — этап 6, TBD. Не обходить LiteLLM.

## Что не делать

- Не коммитить `.env`, ключи, дампы БД.
- Не класть бизнес-логику продуктов в лендинг — лендинг витрина и маршрутизация.
- Не класть логику игр в `apps/landing` — только ссылка Lab → `/games`.
- Не плодить второй прод-шлюз к моделям в обход **LiteLLM**; AutoGen/CrewAI — только как агент 2 после первого продукта.

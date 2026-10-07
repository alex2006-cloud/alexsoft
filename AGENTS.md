# Руководство для агентов (alexsoft)

Это монорепозиторий персональной платформы **alexsoft — Personal Ecosystem Lab**.

## Принципы

- Architecture-as-code: источник правды — `artifacts/architecture/c4-l1-l2-l3.dsl` (C4 L1–L3). Structurizr Local читает `artifacts/workspace.dsl` (полная копия модели; volume Docker = `artifacts/`). После правок C4 синхронизируй: `Copy-Item artifacts/architecture/c4-l1-l2-l3.dsl artifacts/workspace.dsl -Force`. Диаграммы не рисовать «вручную в вакууме»; сначала DSL, потом экспорт. Целевая схема (draw.io): `artifacts/architecture/architecture-in-drawio.drawio` ([ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)).
- Контракт RAG-сервиса — `artifacts/api/rag.openapi.yaml` (contract-first): сначала меняем контракт, потом `apps/rag`.
- Портфолио лендинга — только `artifacts/portfolio/` (файлы + `portfolio.yaml`, [ADR-0016](artifacts/adr/0016-portfolio-from-artifacts.md)). Лендинг собирает их при build; в `apps/landing/public/portfolio` ничего вручную не копировать.
- База знаний о проекте (docs + код + PDF/Excel) живёт в Qdrant: коллекции `project-docs` и `project-code`, источники — `apps/rag/kb/sources.yaml`, синхронизация — `infra/rag/kb-sync.ps1` ([ADR-0018](artifacts/adr/0018-rag-multiformat-ingest-and-project-kb.md)). После крупных правок документации или кода — перезапусти sync; секреты в индекс не попадают (сканер + исключения по имени).
- ADR обязательны для решений, которые меняют стек, границы сервисов или данные. Шаблон: `artifacts/adr/0000-template.md`.
- Секреты только в `.env` (локально) и в GitHub Secrets. В репозиторий — `.env.example`.
- Новый продукт = отдельный сервис в `apps/` + запись в Structurizr + ссылка с лендинга.
- Стек и этапы — `CONCEPT.md` и `ROADMAP.md`. Не внедрять k3s/Kafka раньше этапа. ВБД/RAG — по ROADMAP после документации архитектуры.
- Игры: код в `apps/games`, не в лендинге ([ADR-0010](artifacts/adr/0010-games-static-app.md)).

## Стек (не подменять без ADR)

Лендинг: Next.js. Игры: Next.js в `apps/games` (`basePath: /games`), статика мержится в CI с лендингом ([ADR-0010](artifacts/adr/0010-games-static-app.md)). CI: GitHub Actions. Оркестрация: нативно → Docker Compose (VPS) → k3s. Edge: **Nginx** (+ Nginx Proxy Manager при RAM/Docker, [ADR-0007](artifacts/adr/0007-edge-nginx-npm.md)). IAM: **Authentik** (стек утверждён; внедрение — этап 6, [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)). Данные: PostgreSQL, MinIO, Redis (локально Memurai). BI: Metabase ([ADR-0009](artifacts/adr/0009-metabase-native-local.md)). Брокер: RabbitMQ — при **целевой архитектуре** (этап 6 / облако), не в локальном ИИ-блоке этапа 5; до него BL вызывает Agent Platform напрямую (временная связь). Наблюдаемость инфра: Grafana, Loki, Prometheus, Alloy ([ADR-0008](artifacts/adr/0008-observability-native-local.md)). **AI Gateway: LiteLLM** — не обходить. LLM: Qwen, DeepSeek, ChatGPT, Claude, Gemini. Agent Platform (целевой): код — LangGraph + LangSmith Studio + LangFlow; UI без кода — Dify (Compose на ноутбуке — исключение). ВБД: **Qdrant**. RAG: LlamaIndex + hybrid в Qdrant; embedding **`text-embedding-3-small`** через LiteLLM (`apps/rag`). LangSmith (платформа) — LLM-трейсы/evals (не путать со Studio). Redis-кеш ответов AI — целевая архитектура (этап 6). BL API (целевой): FastAPI. Guardrails (целевой): LLM Guard.

## Что не делать

- Не коммитить `.env`, ключи, дампы БД.
- Не класть бизнес-логику продуктов в лендинг — лендинг витрина и маршрутизация.
- Не класть логику игр в `apps/landing` — только ссылка Lab → `/games`.
- Не плодить второй прод-шлюз к моделям в обход **LiteLLM**.

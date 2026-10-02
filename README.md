# alexsoft — Personal Ecosystem Lab

Персональная мультисервисная платформа: лендинг-визитка, набор mini-SaaS / ботов / инструментов, платформа данных (БД + BI) и слой AI-агентов. Развёртывается как контейнерная система с полным DevOps-циклом.

**Цель.** Практическое освоение полного цикла разработки и эксплуатации ПО — от идеи до CI/CD, мониторинга, BI и AI-агентов.

**Ценность.** Личное пространство проектов, репозиторий-портфолио с артефактами (C4/UML, Terraform, Docker, Grafana).

## Что внутри (контур продукта)

- Публичный лендинг с портфолио и живыми демо
- Независимые микросервисы-продукты (игры, RAG, AI-агенты и др.)
- Единая платформа данных: PostgreSQL, MinIO, ETL, BI
- AI-шлюз / оркестратор для сервисов
- Инфраструктура: логи, метрики, версии, CI/CD
- Architecture-as-code: диаграммы Structurizr собираются из репозитория

## Структура монорепозитория

### Документы в корне

| Путь | Назначение |
|------|------------|
| `README.md` | Витрина репозитория: что это за проект, как устроен, как начать |
| `CONCEPT.md` | Полная концепция: цель, функции, сервисы, стек, этапы |
| `ROADMAP.md` | Дорожная карта реализации с чекбоксами по этапам |
| `AGENTS.md` | Правила для агентов Cursor: стек, границы сервисов, чего не делать |
| `.env.example` | Шаблон переменных окружения (без секретов). Локальный `.env` в git не кладётся |
| `.gitignore` | Список файлов, которые git не отслеживает (`node_modules`, сборки, `.env`) |

### Папки

| Путь | Назначение |
|------|------------|
| `apps/landing` | Публичный SPA (Next.js), витрина |
| `apps/games` | Мини-игры (Next.js, `basePath: /games`) |
| `apps/rag` | RAG-сервис (FastAPI + LlamaIndex + Qdrant; контракт `artifacts/api/rag.openapi.yaml`) |
| `apps/ai-gateway` | Документация AI-шлюза (LiteLLM) |
| `packages/` | Общие библиотеки |
| `infra/` | Docker Compose, позже k3s / Terraform |
| `artifacts/architecture` | C4 DSL, draw.io, UML Component Diagram |
| `artifacts/api` | OpenAPI-контракты (`rag.openapi.yaml`) |
| `artifacts/adr` | Architecture Decision Records |
| `artifacts/business-cases` | User Stories, Use Cases, BPMN, Sequence |
| `artifacts/generated` | Экспорт PNG/SVG из CI |

## Текущий этап

**Этап 5 — AI-контур.** LiteLLM+DeepSeek → агенты с продуктами и стек агентов (lab, выполнено) → **Architecture and documentation** (целевая архитектура: [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md)) → RAG → **первый AI-агент с RAG**. Redis-кеш AI, RabbitMQ, FastAPI, LLM Guard, Authentik — при целевой архитектуре (этап 6); до брокера BL вызывает Agent Platform напрямую. См. [ROADMAP.md](ROADMAP.md), [CONCEPT.md](CONCEPT.md).

## Быстрый старт

1. Скопировать `.env.example` → `.env` и задать локальные значения (в т.ч. `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`).
2. PostgreSQL (локально): установить PostgreSQL 16, создать БД `alexsoft` — [infra/postgres/README.md](infra/postgres/README.md), [ADR-0004](artifacts/adr/0004-postgresql-native-local.md).
3. Redis (локально): Memurai + Redis Insight — [infra/redis/README.md](infra/redis/README.md), [ADR-0005](artifacts/adr/0005-redis-native-local.md).
4. MinIO (локально): `minio.exe` + Console — [infra/minio/README.md](infra/minio/README.md), [ADR-0006](artifacts/adr/0006-minio-native-local.md).
5. Observability (локально, по одному компоненту): Loki → Prometheus → Alloy → Grafana — [ADR-0008](artifacts/adr/0008-observability-native-local.md), каталоги `infra/loki`, `infra/prometheus`, `infra/alloy`, `infra/grafana`.
6. Metabase (локально, JAR + Java): [infra/metabase/README.md](infra/metabase/README.md) → http://127.0.0.1:3002
7. LiteLLM AI Gateway (локально, Python venv): [infra/litellm/README.md](infra/litellm/README.md) → http://127.0.0.1:8080 ([ADR-0011](artifacts/adr/0011-ai-gateway-litellm.md))
7a. Qdrant + RAG (локально): [infra/qdrant/README.md](infra/qdrant/README.md), [apps/rag/README.md](apps/rag/README.md) → http://127.0.0.1:8200/docs ([ADR-0017](artifacts/adr/0017-rag-service-implementation.md)). Для embeddings нужен `OPENAI_API_KEY` в `.env`.
8. Архитектурная модель: правим `artifacts/architecture/c4-l1-l2-l3.dsl`, копируем в `artifacts/workspace.dsl` → Structurizr Local http://127.0.0.1:8070 (volume `artifacts/`). См. [artifacts/README.md](artifacts/README.md).
9. Лендинг: `cd apps/landing && npm install && npm run dev` → http://localhost:3000.
10. Игры: `cd apps/games && npm install && npm run dev` → http://localhost:3010/games (лендинг в dev проксирует `/games`).

### Порты локальной лаборатории

| Порт | Сервис |
|------|--------|
| 3000 | Лендинг (Next.js) |
| 3001 | Grafana |
| 3002 | Metabase |
| 3010 | Игры (Next.js, локально; путь `/games`) |
| 3100 / 9096 | Loki HTTP / gRPC |
| 9090 | Prometheus |
| 12345 | Alloy HTTP UI |
| 5432 | PostgreSQL |
| 6379 | Redis (Memurai) |
| 9000 / 9001 | MinIO S3 / Console |
| 6333 / 6334 | Qdrant REST / gRPC |
| 8200 | RAG-сервис (`apps/rag`, FastAPI) |
| 8070 | Structurizr Local (C4 UI) |
| 8071 | Swagger UI (контракт RAG, опционально) |
| 8080 | LiteLLM AI Gateway |

Источник правды по значениям — `.env` (шаблон `.env.example`).

### Observability — быстрый просмотр

```powershell
powershell -ExecutionPolicy Bypass -File infra\loki\start-loki.ps1
powershell -ExecutionPolicy Bypass -File infra\prometheus\start-prometheus.ps1
powershell -ExecutionPolicy Bypass -File infra\alloy\start-alloy.ps1
powershell -ExecutionPolicy Bypass -File infra\alloy\seed-demo-log.ps1
powershell -ExecutionPolicy Bypass -File infra\grafana\start-grafana.ps1
```

- Grafana: http://127.0.0.1:3001 (`admin` / `GRAFANA_ADMIN_PASSWORD`)
- Explore → Loki: `{job="alexsoft-demo"}`
- Explore → Prometheus: `alloy_build_info`

## Стек (целевой)

Next.js · FastAPI · GitHub monorepo · GitHub Actions · Nginx (+NPM) · Authentik · Docker Compose → k3s · PostgreSQL · MinIO · Redis · RabbitMQ (этап 6) · Metabase · Grafana · Loki · Prometheus · Grafana Alloy · LiteLLM · LangGraph + LangSmith Studio + LangFlow · Dify · LlamaIndex · Qdrant · LLM Guard · LangSmith. Подробнее — [ADR-0015](artifacts/adr/0015-target-architecture-stacks.md).

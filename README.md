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
| `apps/rag` | RAG-сервис |
| `apps/ai-gateway` | Единый AI-шлюз / оркестратор |
| `packages/` | Общие библиотеки |
| `infra/` | Docker Compose, позже k3s / Terraform |
| `artifacts/structurizr` | Источник диаграмм (DSL) |
| `artifacts/adr` | Architecture Decision Records |
| `artifacts/generated` | Экспорт PNG/SVG из CI |
| `docs/` | Рабочие документы (спеки, гайды, заметки) |

## Текущий этап

**Этап 5 — AI-контур.** LiteLLM+DeepSeek (Qwen в конфиге) → LangGraph+продукт → CrewAI+продукт → AutoGen+продукт → RAG+продукт → LangSmith; Redis-кеш и RabbitMQ — после ИИ-блока. См. [ROADMAP.md](ROADMAP.md), [CONCEPT.md](CONCEPT.md).

## Быстрый старт

1. Скопировать `.env.example` → `.env` и задать локальные значения (в т.ч. `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`).
2. PostgreSQL (локально): установить PostgreSQL 16, создать БД `alexsoft` — [infra/postgres/README.md](infra/postgres/README.md), [ADR-0004](artifacts/adr/0004-postgresql-native-local.md).
3. Redis (локально): Memurai + Redis Insight — [infra/redis/README.md](infra/redis/README.md), [ADR-0005](artifacts/adr/0005-redis-native-local.md).
4. MinIO (локально): `minio.exe` + Console — [infra/minio/README.md](infra/minio/README.md), [ADR-0006](artifacts/adr/0006-minio-native-local.md).
5. Observability (локально, по одному компоненту): Loki → Prometheus → Alloy → Grafana — [ADR-0008](artifacts/adr/0008-observability-native-local.md), каталоги `infra/loki`, `infra/prometheus`, `infra/alloy`, `infra/grafana`.
6. Metabase (локально, JAR + Java): [infra/metabase/README.md](infra/metabase/README.md) → http://127.0.0.1:3002
7. LiteLLM AI Gateway (локально, Python venv): [infra/litellm/README.md](infra/litellm/README.md) → http://127.0.0.1:8080 ([ADR-0011](artifacts/adr/0011-ai-gateway-litellm.md))
8. Архитектурная модель: `artifacts/structurizr/workspace.dsl` (Structurizr Lite или Structurizr CLI).
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

Next.js · GitHub monorepo · GitHub Actions · Docker Compose → k3s · PostgreSQL · MinIO · Redis · Metabase → Superset/ClickHouse · RabbitMQ · Grafana · Loki · Prometheus · Grafana Alloy · LangChain/LangGraph или AutoGen.

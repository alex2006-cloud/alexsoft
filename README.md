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
| `apps/landing` | Публичный SPA (Next.js) |
| `apps/games` | Мини-игры |
| `apps/rag` | RAG-сервис |
| `apps/ai-gateway` | Единый AI-шлюз / оркестратор |
| `packages/` | Общие библиотеки |
| `infra/` | Docker Compose, позже k3s / Terraform |
| `artifacts/structurizr` | Источник диаграмм (DSL) |
| `artifacts/adr` | Architecture Decision Records |
| `artifacts/generated` | Экспорт PNG/SVG из CI |
| `docs/` | Рабочие документы (спеки, гайды, заметки) |

## Текущий этап

**Этап 0 — каркас репозитория и C4 Level 1.** Лендинг, DNS, GitHub Actions, БД и observability — следующие шаги (см. [ROADMAP.md](ROADMAP.md), замысел — [CONCEPT.md](CONCEPT.md)).

## Быстрый старт (пока без сервисов)

1. Скопировать `.env.example` → `.env` и задать локальные значения.
2. Открыть архитектурную модель: `artifacts/structurizr/workspace.dsl` (Structurizr Lite или Structurizr CLI).
3. Дальше — `apps/landing` и `infra/compose`.

## Стек (целевой)

Next.js · GitHub monorepo · GitHub Actions · Docker Compose → k3s · PostgreSQL · MinIO · Redis · Metabase → Superset/ClickHouse · RabbitMQ · Grafana · Loki · Prometheus · LangChain/LangGraph или AutoGen.

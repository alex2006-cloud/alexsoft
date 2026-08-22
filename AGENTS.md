# Руководство для агентов (alexsoft)

Это монорепозиторий персональной платформы **alexsoft — Personal Ecosystem Lab**.

## Принципы

- Architecture-as-code: источник правды по архитектуре — `artifacts/structurizr/workspace.dsl`. Диаграммы не рисовать «вручную в вакууме»; сначала DSL, потом экспорт.
- ADR обязательны для решений, которые меняют стек, границы сервисов или данные. Шаблон: `artifacts/adr/0000-template.md`.
- Секреты только в `.env` (локально) и в GitHub Secrets. В репозиторий — `.env.example`.
- Новый продукт = отдельный сервис в `apps/` + запись в Structurizr + ссылка с лендинга.
- Стек и этапы — `docs/CONCEPT.md` и `docs/ROADMAP.md`. Не внедрять k3s/Kafka/векторную БД раньше этапа.

## Стек (не подменять без ADR)

Лендинг: Next.js. CI: GitHub Actions. Оркестрация: Docker Compose, позже k3s. Данные: PostgreSQL, MinIO, Redis. BI: Metabase (позже Superset/ClickHouse). Брокер: RabbitMQ. Наблюдаемость: Grafana, Loki, Prometheus. AI: LangChain/LangGraph или AutoGen через `apps/ai-gateway`.

## Что не делать

- Не коммитить `.env`, ключи, дампы БД.
- Не класть бизнес-логику продуктов в лендинг — лендинг витрина и маршрутизация.
- Не плодить второй AI-стек в обход шлюза, когда шлюз уже появится.

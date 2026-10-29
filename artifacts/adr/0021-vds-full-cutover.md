# ADR-0021: Полный переезд runtime на VDS (cutover)

- **Статус:** accepted
- **Дата:** 2026-10-28
- **Контекст:** Локальный lab (Windows native) собран; целевая топология — [`architecture-in-drawio.drawio`](../architecture/architecture-in-drawio.drawio), [ADR-0015](0015-target-architecture-stacks.md). Нужен единый режим переезда на Fornex VDS без гибрида «данные на ноутбуке». План работ: [`vds-cutover-plan.md`](../architecture/vds-cutover-plan.md).

- **Рассмотренные альтернативы:**
  - **Гибрид** (лендинг на VDS, БД/AI на ноутбуке) — отклонён владельцем.
  - **k3s day-1** — рано; сначала Docker Compose.
  - **Перенос lab-агентов** (CrewAI / AutoGen / n8n) и тестовых данных — не делаем; Q&A/RAG-агент поднимаем из monorepo или создаём заново.
  - **Dump Authentik с локалки** — отклонено; своя БД Authentik, пользователи заново.
  - **Qdrant snapshot** — отклонено; пустые коллекции, переиндексация только по команде владельца.
  - **Бэкапы Fornex / скрипты volume на старте** — отложены; позже на ноутбук по отдельной задаче.

- **Решение:**
  ### Режим
  - Полный cutover runtime на VDS, **включая все БД**.
  - Оркестрация day-1: **Docker Compose** (`infra/compose/vds/`). k3s / Kafka / РКН — после стабилизации.
  - Edge: **host Nginx + Certbot** ([ADR-0007](0007-edge-nginx-npm.md)); JWT проверяет FastAPI, не Nginx ([ADR-0019](0019-cabinet-ssr-bff-authentik.md)).
  - RabbitMQ — с первого прод-контура запуска агентов (убрать временный прямой BL → Agent).

  ### Публичные имена (prod)
  | Имя | Назначение |
  |-----|------------|
  | `alexsoft.space` / `www` | Лендинг + игры (статика), канонический HTTPS |
  | `alexsoft.space/app` | Кабинет Next.js SSR (`basePath: /app`) |
  | `auth.alexsoft.space` | Authentik (OIDC) |
  | Внутренние сервисы | Только Docker network / `127.0.0.1` — не публиковать BL, RAG, LiteLLM, Qdrant, Postgres, Redis, MinIO, RabbitMQ |

  ### Данные на VDS
  - PostgreSQL (приложение + отдельная БД Authentik), Redis, MinIO, Qdrant, RabbitMQ — новые инстансы.
  - Секреты: `/etc/alexsoft/.env` на сервере + GitHub Secrets для CI; в git только `.env.example` / `infra/compose/vds/.env.example`.

  ### Хостинг (старт)
  - Fornex DE, Ubuntu, Docker; IP VDS: `31.172.71.231` (обновлять при смене).
  - DNS A `alexsoft.space` / `www` / `auth` → этот IP; TLS — Let's Encrypt (certbot).

- **Последствия:**
  - Ноутбук перестаёт быть runtime продукта после cutover; остаётся Cursor + git + (позже) бэкапы.
  - Фазы внедрения — в [`vds-cutover-plan.md`](../architecture/vds-cutover-plan.md) и ROADMAP этап 6.
  - Смена домена/edge/IAM — новый ADR или правка этого.

- **Ссылки:**
  - [ADR-0015](0015-target-architecture-stacks.md), [ADR-0019](0019-cabinet-ssr-bff-authentik.md), [ADR-0007](0007-edge-nginx-npm.md)
  - [`infra/compose/vds/`](../../infra/compose/vds/)

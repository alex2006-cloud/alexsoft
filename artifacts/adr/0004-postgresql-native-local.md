# ADR-0004: PostgreSQL 16 — локальная нативная установка (Windows)

- **Статус:** accepted
- **Дата:** 2026-08-31
- **Контекст:** ADR-0003 предполагал Postgres в Docker Compose. На машине разработки Docker Desktop не установлен; для локальной разработки проще поставить PostgreSQL 16 напрямую в Windows и подключаться через DBeaver. VPS/облако и перенос данных — по-прежнему позже.
- **Решение:**
  - **Где:** только локально (Windows), установщик с [postgresql.org](https://www.postgresql.org/download/windows/) (EDB), версия **16**.
  - **Топология:** один инстанс PostgreSQL, одна БД **`alexsoft`**, роль **`alexsoft`**, отдельные **схемы** на продукт по мере появления сервисов.
  - **Сеть:** слушает `localhost:5432`; в интернет не публикуем.
  - **Инициализация:** SQL в `infra/postgres/setup/` (роль и БД) и `infra/postgres/init/` (расширения). Пароль роли совпадает с `POSTGRES_PASSWORD` в `.env`.
  - **Клиент:** DBeaver Community (или `psql` из состава установщика).
  - **Docker Compose:** `infra/compose/docker-compose.data.yml` остаётся как **опциональная** альтернатива, не основной путь для локальной разработки.
- **Последствия:**
  - Пошаговая инструкция — `infra/postgres/README.md`.
  - ADR-0003 помечен как **superseded** этим ADR для локального контура.
  - Служба PostgreSQL стартует с Windows (или вручную через «Службы»); отдельный `docker compose up` не нужен.
  - При переезде на VPS/облако — новый ADR: бэкапы (`pg_dump`), сеть, миграция данных.

# ADR-0009: Metabase — нативный BI на Windows (JAR + Java)

- **Статус:** accepted
- **Дата:** 2026-09-14
- **Контекст:** Этап 3 дорожной карты — observability и BI. Observability закрыта ([ADR-0008](0008-observability-native-local.md)). Нужен BI поверх локального PostgreSQL `alexsoft` ([ADR-0004](0004-postgresql-native-local.md)) без Docker Compose на ноутбуке: цель обучения — поставить и понять Metabase как end-user. Docker Engine + Compose отложены на этап VPS/облака.
- **Решение:**
  - **Где:** только локально (Windows), OSS **JAR** + **Eclipse Temurin JRE 25+** (требование upstream Metabase).
  - **Версия:** Metabase OSS **v0.63.17** (зафиксирована в `infra/metabase/install-metabase.ps1`). **Не** использовать `v0.63.16.x` на Windows: регрессия пути к JAR (`Illegal char <:>` / `/C:/…`) ломает старт.
  - **Расположение:** `%LOCALAPPDATA%\Metabase\` (`metabase.jar`, H2 application DB, plugins, логи процесса). Пользовательский процесс (не Windows Service); start/stop — `infra/metabase/*.ps1`.
  - **Сеть / UI:** loopback, порт **`3002`** (`MB_JETTY_PORT` / `METABASE_PORT`) — **3000** занят лендингом, **3001** Grafana.
  - **Application DB:** встроенный **H2** (достаточно для локальной лаборатории). Прод-app-DB в Postgres — отдельное решение при переносе.
  - **Data source:** PostgreSQL `localhost:5432`, БД/роль `alexsoft` из `.env` (`POSTGRES_*`). Первый учебный просмотр — таблица `demo_items` (`infra/postgres/demo/`).
  - **Порты и секреты:** `.env` / `.env.example` (`METABASE_HOST`, `METABASE_PORT`). Пароль admin Metabase задаётся в Setup UI, в `.env` не дублируем.
  - **Docker Compose:** не основной путь для локального BI; перенос на VPS — отдельный ADR.
- **Последствия:**
  - Инструкция: `infra/metabase/README.md`.
  - Без Java 25+ JAR не стартует; без живого Postgres datasource пуст.
  - H2 не для продакшена — при переезде мигрировать application DB или начать с Postgres app-DB.
  - Следующий этап ROADMAP: первый продукт в контейнере (этап 4).

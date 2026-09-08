# Docker Compose

Локальный контур и публичная витрина.

Порядок появления сервисов данных: PostgreSQL → Redis → MinIO → Loki/Prometheus/Grafana → продукты → RabbitMQ.

## PostgreSQL (локально)

См. [ADR-0004](../../artifacts/adr/0004-postgresql-native-local.md) и [infra/postgres/README.md](../postgres/README.md) — **нативная установка PostgreSQL 16 на Windows**, подключение через DBeaver.

Опционально (если есть Docker Desktop): `docker-compose.data.yml` — [ADR-0003](../../artifacts/adr/0003-postgresql-local-docker-compose.md) (superseded для локальной разработки).

## Redis (локально)

См. [ADR-0005](../../artifacts/adr/0005-redis-native-local.md) и [infra/redis/README.md](../redis/README.md) — **Memurai** (нативный Redis на Windows) + GUI **Redis Insight**.

## MinIO (локально)

См. [ADR-0006](../../artifacts/adr/0006-minio-native-local.md) и [infra/minio/README.md](../minio/README.md) — **нативный `minio.exe`**, S3 API `:9000`, встроенная **Console** `:9001`. Docker — не основной путь.

## Лендинг (osipcraft.ru)

Статика Next.js + Caddy с Let’s Encrypt. Сборка на машине разработчика (на VPS 1 ГБ `next build` не помещается).

```bash
cd apps/landing
set LANDING_URL=https://osipcraft.ru
npm ci
npm run build
```

На VPS: nginx раздаёт `/var/www/osipcraft`. После push в `main` статика выкладывается автоматически (workflow **Landing**, секрет `LANDING_SSH_KEY` в GitHub).

`docker-compose.yml` в этой папке — тот же контур, когда на сервере будет Docker и запас RAM.

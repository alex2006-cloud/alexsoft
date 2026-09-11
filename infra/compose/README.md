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

Статика Next.js. Сборка на машине разработчика или в GitHub Actions (на VPS 1 ГиБ `next build` не помещается).

```bash
cd apps/landing
set LANDING_URL=https://osipcraft.ru
npm ci
npm run build
```

### Прод сейчас (VPS)

**Host Nginx + Certbot** — [ADR-0007](../../artifacts/adr/0007-edge-nginx-npm.md), конфиг [`infra/nginx/osipcraft.ru.conf`](../nginx/osipcraft.ru.conf). После push в `main` статика выкладывается в `/var/www/osipcraft` (workflow **Landing**, секрет `LANDING_SSH_KEY`).

### Docker + Nginx Proxy Manager (когда есть Docker и ~≥2 ГиБ RAM)

`docker-compose.yml` в этой папке: **nginx** (`landing`) раздаёт статику, **Nginx Proxy Manager** — HTTPS и GUI.

```bash
# из корня репо, с собранным apps/landing/out
cd infra/compose
docker compose up -d
```

- UI: `http://127.0.0.1:81` (с VPS — только SSH-туннель: `ssh -L 81:127.0.0.1:81 root@VPS`).
- Первый вход NPM: `admin@example.com` / `changeme` — сразу сменить.
- Proxy Host: Domain `osipcraft.ru` → Forward `http://landing:80` → SSL Let’s Encrypt в UI.
- На VPS с rsync: в `.env` рядом с compose — `LANDING_STATIC_PATH=/var/www/osipcraft`.

aaPanel не используем (тяжёлая панель, чужой стек) — см. ADR-0007.

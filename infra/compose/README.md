# Docker Compose

Локальный контур и публичная витрина.

Порядок появления сервисов данных: PostgreSQL → Redis → MinIO → Loki/Prometheus/Grafana → продукты → RabbitMQ.

## Лендинг (osipcraft.ru)

Статика Next.js + Caddy с Let’s Encrypt. Сборка на машине разработчика (на VPS 1 ГБ `next build` не помещается).

```bash
cd apps/landing
set LANDING_URL=https://osipcraft.ru
npm ci
npm run build
```

На VPS: Caddy ставится из пакета (см. выкладку), корень сайта — `/var/www/osipcraft`.

`docker-compose.yml` в этой папке — тот же контур, когда на сервере будет Docker и запас RAM.

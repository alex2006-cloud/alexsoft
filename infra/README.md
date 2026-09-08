# Инфраструктура

- `postgres/` — PostgreSQL локально ([ADR-0004](../artifacts/adr/0004-postgresql-native-local.md)): setup, init, README
- `redis/` — Memurai + Redis Insight ([ADR-0005](../artifacts/adr/0005-redis-native-local.md))
- `minio/` — MinIO + встроенная Console ([ADR-0006](../artifacts/adr/0006-minio-native-local.md)): start/stop, demo-объекты
- `compose/` — Docker Compose (лендинг на VPS; Postgres в Docker — опционально)
  - `docker-compose.data.yml` — Postgres в контейнере (альтернатива, [ADR-0003](../artifacts/adr/0003-postgresql-local-docker-compose.md))
  - `docker-compose.yml` — Caddy + статика лендинга (VPS)
- Позже: манифесты k3s, Terraform, конфиги Grafana/Loki/Prometheus

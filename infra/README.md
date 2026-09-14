# Инфраструктура

- `postgres/` — PostgreSQL локально ([ADR-0004](../artifacts/adr/0004-postgresql-native-local.md)): setup, init, README
- `redis/` — Memurai + Redis Insight ([ADR-0005](../artifacts/adr/0005-redis-native-local.md))
- `minio/` — MinIO + встроенная Console ([ADR-0006](../artifacts/adr/0006-minio-native-local.md)): start/stop, demo-объекты
- `loki/` — Loki нативно ([ADR-0008](../artifacts/adr/0008-observability-native-local.md)): install/start/stop, README
- `prometheus/` — Prometheus нативно ([ADR-0008](../artifacts/adr/0008-observability-native-local.md)): install/start/stop, README
- `alloy/` — Grafana Alloy нативно ([ADR-0008](../artifacts/adr/0008-observability-native-local.md)): install/start/stop, README
- `grafana/` — Grafana OSS нативно ([ADR-0008](../artifacts/adr/0008-observability-native-local.md)): install/start/stop, provisioning, README
- `metabase/` — Metabase OSS нативно (JAR + Java, [ADR-0009](../artifacts/adr/0009-metabase-native-local.md)): install/start/stop, README
- `nginx/` — host Nginx для `osipcraft.ru` ([ADR-0007](../artifacts/adr/0007-edge-nginx-npm.md))
- `compose/` — Docker Compose
  - `docker-compose.data.yml` — Postgres в контейнере (альтернатива, [ADR-0003](../artifacts/adr/0003-postgresql-local-docker-compose.md))
  - `docker-compose.yml` — Nginx (статика) + Nginx Proxy Manager (когда Docker и запас RAM)
- Позже: манифесты k3s, Terraform

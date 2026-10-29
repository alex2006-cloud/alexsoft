# Compose на VDS (alexsoft)

Целевой data-plane для полного cutover: [ADR-0021](../../../artifacts/adr/0021-vds-full-cutover.md), [vds-cutover-plan.md](../../../artifacts/architecture/vds-cutover-plan.md).

## Сервисы (фаза 2)

| Сервис | Порт на хосте | Назначение |
|--------|---------------|------------|
| postgres | `127.0.0.1:5432` | РСУБД приложения (+ позже БД Authentik) |
| redis | `127.0.0.1:6379` | Кэш |
| minio | `127.0.0.1:9000` / `:9001` | S3 + Console (туннель) |
| qdrant | `127.0.0.1:6333` | Векторная БД |
| rabbitmq | `127.0.0.1:5672` / `:15672` | Брокер + management (туннель) |

Сеть Docker: `alexsoft`. Edge (Nginx) — **host**, не в этом файле.

## На сервере

```bash
# секреты
cp infra/compose/vds/.env.example /etc/alexsoft/.env   # один раз; заменить пароли
chmod 600 /etc/alexsoft/.env

# volumes уже: /var/lib/alexsoft/{postgres,redis,minio,qdrant,rabbitmq}

cd /path/to/repo/infra/compose/vds
set -a && source /etc/alexsoft/.env && set +a
docker compose pull
docker compose up -d
docker compose ps
```

Не поднимать, пока не заполнены пароли в `/etc/alexsoft/.env`.

### Authentik (фаза 3)

```bash
# БД
bash setup-authentik-db.sh   # или уже выполнено

# старт (рядом с data compose)
set -a && . /etc/alexsoft/.env && set +a
docker compose -f docker-compose.yml -f docker-compose.authentik.yml up -d authentik-server authentik-worker
```

Публично: https://auth.alexsoft.space — admin `/if/admin/`, логин `akadmin`, пароль `AUTHENTIK_BOOTSTRAP_PASSWORD` из `/etc/alexsoft/.env`.  
Если `docker pull` с ghcr.io рвётся по IPv6 — временно `sysctl net.ipv6.conf.all.disable_ipv6=1` (см. `pull-authentik.sh`).

### AI (фаза 5)

```bash
# LiteLLM DB + gateway
bash setup-litellm-db.sh
docker compose -f docker-compose.yml -f docker-compose.litellm.yml up -d litellm
bash smoke-litellm.sh

# RAG (+ Qdrant v1.15+)
docker compose -f docker-compose.yml -f docker-compose.litellm.yml -f docker-compose.rag.yml \
  up -d --build rag
# ключи AI: powershell -File infra/compose/vds/sync-ai-env.ps1
bash run-kb-sync.sh --no-summaries
bash smoke-rag.sh

# Agent1 + RabbitMQ worker; BL_AGENT_TRANSPORT=rabbitmq в /etc/alexsoft/.env
# (BL_AGENT_SERVER_URL=http://agent1:2024)
docker compose -f docker-compose.yml -f docker-compose.litellm.yml -f docker-compose.rag.yml \
  -f docker-compose.agent1.yml up -d --build agent1 agent-worker
# BL API с publish (после правок apps/api):
docker compose -f docker-compose.yml -f docker-compose.authentik.yml -f docker-compose.apps.yml \
  up -d --build bl-api
bash smoke-bp1.sh                  # прямой HTTP к agent1
python3 smoke-rmq-bp1.py           # полный путь: кабинет → BL → RabbitMQ → worker → bp1_qa
```

Публично наружу не открывать — только `127.0.0.1` + сеть `alexsoft`.

### BL API + Cabinet (фаза 4)

Нужен checkout с `apps/api`, `apps/cabinet` и этим compose (обычно `/opt/alexsoft`).

**CI (предпочтительно):** workflow [`.github/workflows/apps.yml`](../../../.github/workflows/apps.yml) на `main` собирает образы → GHCR (`alexsoft-bl-api`, `alexsoft-cabinet`) → SSH на VDS → `deploy-apps.sh`. Секрет тот же, что у лендинга: `LANDING_SSH_KEY`.

Ручной первый/аварийный bring-up (build на сервере):

```bash
cd /opt/alexsoft/infra/compose/vds
set -a && . /etc/alexsoft/.env && set +a
docker compose -f docker-compose.yml -f docker-compose.authentik.yml -f docker-compose.apps.yml \
  up -d --build bl-api cabinet
curl -sS http://127.0.0.1:8100/health/live
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3020/app
```

Nginx: `location /app` → `127.0.0.1:3020` (см. `infra/nginx/alexsoft.space.conf`).  
Cabinet ходит в BL по `BL_URL=http://bl-api:8100` (override в compose); JWKS — через `authentik-server:9000`.

### MinIO (Chainguard)

Официальный `minio/minio` с Docker Hub/Quay недоступен (2026). В compose — `cgr.dev/chainguard/minio` (nonroot uid **65532**):

```bash
mkdir -p /var/lib/alexsoft/minio
chown -R 65532:65532 /var/lib/alexsoft/minio
```

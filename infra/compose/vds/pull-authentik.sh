#!/usr/bin/env bash
set -euo pipefail
cd /opt/alexsoft/infra/compose/vds
set -a
# shellcheck disable=SC1091
. /etc/alexsoft/.env
set +a

sysctl -w net.ipv6.conf.all.disable_ipv6=1
sysctl -w net.ipv6.conf.default.disable_ipv6=1
cleanup() {
  sysctl -w net.ipv6.conf.all.disable_ipv6=0 || true
  sysctl -w net.ipv6.conf.default.disable_ipv6=0 || true
}
trap cleanup EXIT

docker compose -f docker-compose.yml -f docker-compose.authentik.yml pull authentik-server authentik-worker
docker compose -f docker-compose.yml -f docker-compose.authentik.yml up -d authentik-server authentik-worker
docker compose -f docker-compose.yml -f docker-compose.authentik.yml ps
echo PULL_UP_OK

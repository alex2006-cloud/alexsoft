#!/usr/bin/env bash
# Pull/restart BL API + Cabinet on VDS (фаза 4 CI).
# Usage:
#   BL_API_IMAGE=ghcr.io/…/alexsoft-bl-api:sha-abc \
#   CABINET_IMAGE=ghcr.io/…/alexsoft-cabinet:sha-abc \
#   bash deploy-apps.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -f /etc/alexsoft/.env ]]; then
  echo "missing /etc/alexsoft/.env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
. /etc/alexsoft/.env
set +a

: "${BL_API_IMAGE:?set BL_API_IMAGE}"
: "${CABINET_IMAGE:?set CABINET_IMAGE}"
export BL_API_IMAGE CABINET_IMAGE

COMPOSE=(docker compose
  -f docker-compose.yml
  -f docker-compose.authentik.yml
  -f docker-compose.apps.yml)

echo "pull ${BL_API_IMAGE}"
echo "pull ${CABINET_IMAGE}"
"${COMPOSE[@]}" pull bl-api cabinet
"${COMPOSE[@]}" up -d --no-build bl-api cabinet

# Wait for health
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8100/health/ready >/dev/null \
    && code=$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:3020/app) \
    && [[ "$code" == "200" || "$code" == "302" || "$code" == "307" ]]; then
    echo "OK: bl-api ready, cabinet http=${code}"
    "${COMPOSE[@]}" ps bl-api cabinet
    exit 0
  fi
  sleep 2
done

echo "FAIL: apps not healthy" >&2
"${COMPOSE[@]}" ps bl-api cabinet || true
docker logs alexsoft-vds-bl-api-1 --tail 40 || true
docker logs alexsoft-vds-cabinet-1 --tail 40 || true
exit 1

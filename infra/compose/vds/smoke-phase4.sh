#!/usr/bin/env bash
set -euo pipefail
echo "== login redirect =="
curl -sS -D- -o /dev/null http://127.0.0.1:3020/app/api/auth/login | head -20
echo "== public /app =="
curl -sS -D- -o /dev/null https://alexsoft.space/app | head -15
echo "== public login =="
curl -sS -D- -o /dev/null https://alexsoft.space/app/api/auth/login | head -20
echo "== bl agents unauthorized =="
curl -sS -o /tmp/agents.json -w "http:%{http_code}\n" http://127.0.0.1:8100/v1/agents
head -c 300 /tmp/agents.json; echo
echo "== postgres schemas/agents =="
docker exec alexsoft-vds-postgres-1 psql -U alexsoft -d alexsoft -c '\dn' \
  -c "SELECT id, slug, name FROM bl.agents ORDER BY slug LIMIT 10;"
echo "== cabinet schema =="
docker exec alexsoft-vds-postgres-1 psql -U alexsoft -d alexsoft -c '\dt cabinet.*' || true

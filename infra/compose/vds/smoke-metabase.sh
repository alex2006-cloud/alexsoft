#!/usr/bin/env bash
# Smoke Metabase health (фаза 6).
set -euo pipefail
code=$(curl -sS -o /tmp/mb-health.json -w '%{http_code}' http://127.0.0.1:3002/api/health || true)
echo "http=$code body=$(cat /tmp/mb-health.json)"
grep -q '"status":"ok"' /tmp/mb-health.json
echo "OK: metabase health"

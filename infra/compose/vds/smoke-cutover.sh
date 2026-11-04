#!/usr/bin/env bash
# Phase 7 smoke: public path still on VDS.
set -euo pipefail
echo "=== DNS hint (from this host) ==="
getent hosts alexsoft.space www.alexsoft.space auth.alexsoft.space || true
echo "=== HTTPS ==="
curl -fsS -o /dev/null -w "apex=%{http_code}\n" https://alexsoft.space/
curl -fsS -o /dev/null -w "app=%{http_code}\n" https://alexsoft.space/app
curl -fsS -o /dev/null -w "auth=%{http_code}\n" https://auth.alexsoft.space/
echo "=== BL health localhost ==="
curl -fsS http://127.0.0.1:8100/health/live
echo
echo "OK: cutover smoke"

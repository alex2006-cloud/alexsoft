#!/usr/bin/env bash
set -euo pipefail
echo "=== NPM UI api ==="
curl -fsS -o /tmp/npm-api.json -w "http=%{http_code}\n" http://127.0.0.1:81/api/
head -c 200 /tmp/npm-api.json; echo
# Host Nginx still owns public 80/443
curl -fsS -o /dev/null -w "public_apex=%{http_code}\n" https://alexsoft.space/
echo "OK: npm smoke (UI :81; public edge still host Nginx)"

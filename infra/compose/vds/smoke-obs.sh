#!/usr/bin/env bash
# Smoke observability stack (фаза 6).
set -euo pipefail

echo "=== loki ready ==="
curl -fsS http://127.0.0.1:3100/ready
echo
echo "=== prometheus ready ==="
curl -fsS http://127.0.0.1:9090/-/ready
echo
echo "=== grafana health ==="
curl -fsS http://127.0.0.1:3001/api/health
echo
echo "=== alloy /-/ready ==="
curl -fsS http://127.0.0.1:12345/-/ready || curl -fsS http://127.0.0.1:12345/metrics >/dev/null
echo
echo "=== prometheus has node metrics? ==="
curl -fsS 'http://127.0.0.1:9090/api/v1/query?query=node_memory_MemAvailable_bytes' \
  | grep -q '"result":\[' && echo "node metrics OK" || echo "WARN: no node_memory yet (wait ~30s)"
echo "=== loki has docker streams? ==="
curl -fsS -G 'http://127.0.0.1:3100/loki/api/v1/label/job/values' \
  | tee /dev/stderr | grep -q docker && echo "loki job=docker OK" || echo "WARN: no docker label yet"
echo "OK: obs smoke"

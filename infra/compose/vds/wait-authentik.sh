#!/usr/bin/env bash
set -euo pipefail
for i in $(seq 1 36); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:9100/-/health/ready/ || echo 000)
  echo "try=$i code=$code"
  if [[ "$code" == "204" || "$code" == "200" ]]; then
    echo AUTHENTIK_READY
    exit 0
  fi
  sleep 10
done
echo AUTHENTIK_NOT_READY
docker logs alexsoft-vds-authentik-server-1 2>&1 | tail -40
exit 1

#!/usr/bin/env bash
# Enable LangSmith tracing on agent1 (+ optional litellm) when LANGSMITH_API_KEY is set.
set -euo pipefail
ENV_FILE="${ENV_FILE:-/etc/alexsoft/.env}"
# shellcheck disable=SC1090
set -a && . "$ENV_FILE" && set +a

if [[ -z "${LANGSMITH_API_KEY:-}" ]]; then
  echo "SKIP: LANGSMITH_API_KEY empty — add key to $ENV_FILE then re-run"
  exit 0
fi

grep -q '^LANGSMITH_TRACING=' "$ENV_FILE" \
  && sed -i 's/^LANGSMITH_TRACING=.*/LANGSMITH_TRACING=true/' "$ENV_FILE" \
  || echo 'LANGSMITH_TRACING=true' >> "$ENV_FILE"

if ! grep -q '^LANGSMITH_PROJECT=' "$ENV_FILE"; then
  echo 'LANGSMITH_PROJECT=alexsoft-vds' >> "$ENV_FILE"
fi

cd /opt/alexsoft/infra/compose/vds
set -a && . "$ENV_FILE" && set +a
docker compose -f docker-compose.yml -f docker-compose.litellm.yml -f docker-compose.rag.yml \
  -f docker-compose.agent1.yml up -d agent1 agent-worker
echo "OK: LANGSMITH_TRACING=true; restart agent1/agent-worker"

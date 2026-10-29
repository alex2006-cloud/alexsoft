#!/usr/bin/env bash
# Smoke BP1 graph via LangGraph Agent Server (localhost:2024).
set -euo pipefail
export BP1_Q="${1:-Какой шлюз к LLM используется в проекте alexsoft и почему?}"

BODY=$(python3 - <<'PY'
import json, os
print(json.dumps({
  "assistant_id": "bp1_qa",
  "input": {"messages": [{"role": "user", "content": os.environ["BP1_Q"]}]},
}))
PY
)

echo "=== /ok ==="
curl -fsS http://127.0.0.1:2024/ok
echo
echo "=== run bp1_qa ==="
curl -sS -X POST "http://127.0.0.1:2024/runs/wait" \
  -H "Content-Type: application/json" \
  -d "$BODY" \
  | python3 -c '
import sys, json
raw=sys.stdin.read()
try:
    d=json.loads(raw)
except Exception:
    print(raw[:500]); raise SystemExit(1)
msgs=d.get("messages") or []
print("messages", len(msgs))
for m in reversed(msgs):
    t=m.get("type") or m.get("role")
    c=m.get("content")
    if t in ("ai","assistant") and c:
        print("A:", (c if isinstance(c,str) else str(c))[:900])
        break
else:
    print(raw[:900])
'

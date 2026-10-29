#!/usr/bin/env bash
set -euo pipefail
# shellcheck disable=SC1091
set -a; . /etc/alexsoft/.env; set +a
TOKEN="${AUTHENTIK_BL_TOKEN:?}"
BASE="http://127.0.0.1:${AUTHENTIK_PORT_HTTP:-9100}/api/v3"
# Find OAuth2 provider for cabinet
curl -sS -H "Authorization: Bearer ${TOKEN}" \
  "${BASE}/providers/oauth2/?search=alexsoft-cabinet" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin);
results=d.get("results") or [];
print("providers:", len(results));
[print(p.get("name"), p.get("client_id"), [u.get("url") if isinstance(u,dict) else u for u in (p.get("redirect_uris") or [])]) for p in results]'

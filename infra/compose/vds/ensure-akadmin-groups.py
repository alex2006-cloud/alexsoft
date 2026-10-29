#!/usr/bin/env python3
"""Ensure akadmin is in alexsoft-users and alexsoft-admins."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

for line in Path("/etc/alexsoft/.env").read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

token = os.environ["AUTHENTIK_BL_TOKEN"]
base = f"http://127.0.0.1:{os.environ.get('AUTHENTIK_PORT_HTTP', '9100')}/api/v3"


def api(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"FAIL: {method} {path} {e.code} {e.read()[:300]!r}", file=sys.stderr)
        raise SystemExit(1) from e


users = api("GET", "/core/users/?" + urllib.parse.urlencode({"search": "akadmin"}))["results"]
if not users:
    print("FAIL: akadmin not found", file=sys.stderr)
    raise SystemExit(1)
user_pk = users[0]["pk"]

groups = api("GET", "/core/groups/?" + urllib.parse.urlencode({"search": "alexsoft"}))["results"]
by_name = {g["name"]: g["pk"] for g in groups}
wanted = {"alexsoft-users", "alexsoft-admins"}
missing = wanted - set(by_name)
if missing:
    print(f"FAIL: groups missing {missing}", file=sys.stderr)
    raise SystemExit(1)

u = api("GET", f"/core/users/{user_pk}/")
raw = u.get("groups") or []
if raw and isinstance(raw[0], dict):
    current_pks = {g["pk"] for g in raw}
else:
    current_pks = set(raw)

need = {by_name[n] for n in wanted}
if need <= current_pks:
    print("OK: akadmin already in alexsoft-users/admins")
    raise SystemExit(0)

api("PATCH", f"/core/users/{user_pk}/", {"groups": list(current_pks | need)})
print("OK: akadmin added to alexsoft-users/admins")

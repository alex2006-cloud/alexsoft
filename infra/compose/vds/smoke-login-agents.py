#!/usr/bin/env python3
"""Phase-4 smoke: OIDC login as akadmin → BFF → /v1/agents. Secrets never printed."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

for line in Path("/etc/alexsoft/.env").read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

password = os.environ.get("AUTHENTIK_BOOTSTRAP_PASSWORD") or ""
if not password:
    print("FAIL: AUTHENTIK_BOOTSTRAP_PASSWORD missing", file=sys.stderr)
    raise SystemExit(1)

site = (os.environ.get("PUBLIC_SITE_URL") or "https://alexsoft.space").rstrip("/")
auth = (os.environ.get("AUTH_PUBLIC_URL") or "https://auth.alexsoft.space").rstrip("/")

c = httpx.Client(timeout=40.0, follow_redirects=False, trust_env=False)


def abs_url(base: str, loc: str) -> str:
    if loc.startswith("http"):
        return loc
    p = urlparse(base)
    return f"{p.scheme}://{p.netloc}{loc}"


r = c.get(f"{site}/app/api/auth/login")
if r.status_code not in (302, 303, 307):
    print(f"FAIL: login start {r.status_code}", file=sys.stderr)
    raise SystemExit(1)
auth_url = abs_url(site, r.headers["location"])

url = auth_url
flow_url = auth_url
for _ in range(10):
    r = c.get(url)
    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
        url = abs_url(str(r.url), r.headers["location"])
        continue
    flow_url = str(r.url)
    break

m = re.search(r"/if/flow/([^/?]+)/", flow_url)
flow_slug = m.group(1) if m else "default-authentication-flow"
# Keep OAuth query on the executor so Authentik continues authorize after login
qs = urlparse(flow_url).query
api = f"{auth}/api/v3/flows/executor/{flow_slug}/"
if qs:
    api = f"{api}?{qs}"


def flow_headers() -> dict:
    return {"Referer": flow_url, "X-authentik-CSRF": c.cookies.get("authentik_csrf") or ""}


r = c.get(api, headers=flow_headers())
r = c.post(api, headers=flow_headers(), json={"component": "ak-stage-identification", "uid_field": "akadmin"})
data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
if r.status_code in (302, 303) or not data:
    r = c.get(api, headers=flow_headers())
    data = r.json() if r.status_code == 200 else {}

for _ in range(8):
    comp = data.get("component") or ""
    if comp == "ak-stage-password":
        r = c.post(api, headers=flow_headers(), json={"component": "ak-stage-password", "password": password})
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code in (302, 303) or not data:
            r = c.get(api, headers=flow_headers())
            data = r.json() if r.status_code == 200 else {}
        continue
    if comp == "xak-flow-redirect" or data.get("to"):
        break
    r = c.get(api, headers=flow_headers())
    data = r.json() if r.status_code == 200 else {}
    if not data:
        break

# After session established, resume authorize (in case flow redirected to /)
url = data.get("to") if data.get("to") and data.get("to") not in ("/", "/if/user/") else auth_url
if url.startswith("/"):
    url = abs_url(auth, url)

callback = False
for _ in range(25):
    r = c.get(url)
    here = str(r.url)
    if "/app/api/auth/callback" in here or "/app/api/auth/callback" in url:
        callback = True
    loc = r.headers.get("location")
    if r.status_code in (301, 302, 303, 307, 308) and loc:
        url = abs_url(here if "://" in here else auth, loc)
        continue
    break

r = c.get(f"{site}/app/api/bl/v1/agents", headers={"Accept": "application/json"})
text = r.text
if r.status_code == 200 and ("echo-demo" in text or "Эхо" in text):
    print(f"OK: agents via BFF http={r.status_code} callback={callback} body={text[:160]!r}")
    raise SystemExit(0)

print(
    f"FAIL: agents http={r.status_code} callback={callback} flow={data.get('component')!r} "
    f"to={str(data.get('to'))[:120]!r} body={text[:240]!r}",
    file=sys.stderr,
)
raise SystemExit(1)

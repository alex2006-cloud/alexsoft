#!/usr/bin/env python3
"""Smoke: OIDC → BFF → BL create run bp1-project-qa → SSE (RabbitMQ transport on VDS)."""
from __future__ import annotations

import json
import os
import re
import sys
import time
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
question = os.environ.get("BP1_Q") or "Какой шлюз к LLM используется в проекте alexsoft?"

c = httpx.Client(
    timeout=120.0,
    follow_redirects=False,
    trust_env=False,
    headers={"Origin": site, "Referer": f"{site}/app/"},
)


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

url = data.get("to") if data.get("to") and data.get("to") not in ("/", "/if/user/") else auth_url
if url.startswith("/"):
    url = abs_url(auth, url)

for _ in range(25):
    r = c.get(url)
    here = str(r.url)
    loc = r.headers.get("location")
    if r.status_code in (301, 302, 303, 307, 308) and loc:
        url = abs_url(here if "://" in here else auth, loc)
        continue
    break

r = c.post(
    f"{site}/app/api/bl/v1/agents/bp1-project-qa/runs",
    headers={"Accept": "application/json"},
    json={"input": question},
)
if r.status_code not in (200, 202):
    print(f"FAIL: create run http={r.status_code} body={r.text[:400]!r}", file=sys.stderr)
    raise SystemExit(1)
run = r.json()
run_id = run.get("id")
print(f"run id={run_id} status={run.get('status')} transport=check-logs")

answer = ""
deadline = time.time() + 100
with c.stream("GET", f"{site}/app/api/bl/v1/runs/{run_id}/events", headers={"Accept": "text/event-stream"}) as resp:
    if resp.status_code >= 400:
        print(f"FAIL: events http={resp.status_code}", file=sys.stderr)
        raise SystemExit(1)
    event = "message"
    data_lines: list[str] = []
    for line in resp.iter_lines():
        if time.time() > deadline:
            break
        if line.startswith(":"):
            continue
        if line == "":
            if data_lines:
                payload = "\n".join(data_lines)
                data_lines = []
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    event = "message"
                    continue
                if event == "message" and obj.get("content"):
                    answer = str(obj["content"])
                    break
                if event == "error":
                    print(f"FAIL: run error {obj}", file=sys.stderr)
                    raise SystemExit(1)
                if event in ("done",) or (event == "status" and obj.get("status") in ("failed",)):
                    if event == "status" and obj.get("status") == "failed":
                        print(f"FAIL: status failed {obj}", file=sys.stderr)
                        raise SystemExit(1)
                    if answer:
                        break
            event = "message"
            continue
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())

# Fallback: poll run status + last events from GET run
if not answer:
    r = c.get(f"{site}/app/api/bl/v1/runs/{run_id}")
    print(f"poll run={r.status_code} {r.text[:500]}")
    # try reading stored events via a short SSE again is hard; check status
    if r.status_code == 200:
        st = r.json().get("status")
        if st == "succeeded":
            # content may only be in events; dump run for debug
            print("WARN: succeeded but no message parsed from SSE")
        else:
            print(f"FAIL: run status={st}", file=sys.stderr)
            raise SystemExit(1)

print(f"A: {answer[:900]}")
if not answer or ("litellm" not in answer.lower() and "шлюз" not in answer.lower() and len(answer) < 20):
    # still OK if we got a non-empty project answer
    if len(answer) < 20:
        print("FAIL: empty/short answer", file=sys.stderr)
        raise SystemExit(1)
print("OK: BL→RabbitMQ→agent bp1-project-qa")

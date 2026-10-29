#!/usr/bin/env python3
"""Replace phase-4 503 stub with /app proxy in Certbot-managed nginx site."""
from pathlib import Path

p = Path("/etc/nginx/sites-available/alexsoft.space.http-stub")
text = p.read_text(encoding="utf-8")
old = (
    "\t# кабинет (фаза 4) — пока заглушка\n"
    "\tlocation /app {\n"
    "\t\tdefault_type text/plain;\n"
    "\t\treturn 503 'cabinet not deployed yet (phase 4)\\n';\n"
    "\t}"
)
new = (
    "\t# Cabinet SSR (фаза 4)\n"
    "\tlocation = /app {\n"
    "\t\tproxy_http_version 1.1;\n"
    "\t\tproxy_set_header Host $host;\n"
    "\t\tproxy_set_header X-Real-IP $remote_addr;\n"
    "\t\tproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "\t\tproxy_set_header X-Forwarded-Proto $scheme;\n"
    "\t\tproxy_pass http://127.0.0.1:3020;\n"
    "\t}\n"
    "\tlocation /app/ {\n"
    "\t\tproxy_http_version 1.1;\n"
    "\t\tproxy_set_header Host $host;\n"
    "\t\tproxy_set_header X-Real-IP $remote_addr;\n"
    "\t\tproxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "\t\tproxy_set_header X-Forwarded-Proto $scheme;\n"
    "\t\tproxy_buffering off;\n"
    "\t\tproxy_read_timeout 300s;\n"
    "\t\tproxy_pass http://127.0.0.1:3020;\n"
    "\t}"
)
if old not in text:
    if "proxy_pass http://127.0.0.1:3020" in text:
        print("already patched")
        raise SystemExit(0)
    raise SystemExit("stub location block not found — edit manually")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("nginx stub patched")

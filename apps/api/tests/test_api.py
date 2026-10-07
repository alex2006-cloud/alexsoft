"""BL API: JWT/roles, quota, runs + SSE, admin. Mirrors artifacts/api/bl.openapi.yaml."""

from __future__ import annotations

import asyncio
import json

import pytest

from .conftest import BoomRunner, SlowRunner, bearer


async def wait_done(client, token, run_id, tries=100):
    for _ in range(tries):
        r = await client.get(f"/v1/runs/{run_id}", headers=bearer(token))
        if r.json()["status"] in ("succeeded", "failed"):
            return r.json()
        await asyncio.sleep(0.02)
    raise AssertionError("run did not finish")


def parse_sse(text: str) -> list[tuple[str, dict]]:
    out = []
    for frame in text.strip().split("\n\n"):
        ev, data = None, None
        for line in frame.splitlines():
            if line.startswith("event:"):
                ev = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
        if ev:
            out.append((ev, data))
    return out


# ------------------------------------------------------------------ auth
async def test_health_live_without_token(client):
    assert (await client.get("/health/live")).json() == {"status": "ok", "checks": {}}


async def test_missing_token_is_401(client):
    r = await client.get("/v1/me")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("kw", [
    {"exp_in": -100},
    {"aud": "someone-else"},
    {"iss": "http://evil.example/"},
    {"kid": "unknown"},
])
async def test_bad_tokens_are_401(client, make_token, kw):
    r = await client.get("/v1/me", headers=bearer(make_token(**kw)))
    assert r.status_code == 401


async def test_token_signed_by_foreign_key_is_401(client, make_token, other_key):
    r = await client.get("/v1/me", headers=bearer(make_token(key=other_key)))
    assert r.status_code == 401


async def test_hs256_and_none_are_rejected(client):
    import jwt as pyjwt

    forged = pyjwt.encode({"sub": "x", "aud": "alexsoft-cabinet"}, "secret", algorithm="HS256", headers={"kid": "test-key"})
    assert (await client.get("/v1/me", headers=bearer(forged))).status_code == 401


async def test_user_without_group_is_403(client, make_token):
    r = await client.get("/v1/me", headers=bearer(make_token(groups=[])))
    assert r.status_code == 403


async def test_me_roles_and_quota(client, make_token):
    r = await client.get("/v1/me", headers=bearer(make_token()))
    body = r.json()
    assert r.status_code == 200
    assert body["roles"] == ["user"] and body["username"] == "alice"
    assert body["quota"]["daily_limit"] == 3 and body["quota"]["remaining"] == 3

    admin = await client.get("/v1/me", headers=bearer(make_token(sub="a-1", groups=["alexsoft-admins"])))
    assert admin.json()["roles"] == ["user", "admin"]


# ------------------------------------------------------------------ agents + runs
async def test_agents_list_hides_disabled(client, make_token):
    r = await client.get("/v1/agents", headers=bearer(make_token()))
    ids = [a["id"] for a in r.json()["items"]]
    assert ids == ["echo-demo", "agent1-qa"]  # bp1-project-qa is disabled by default
    assert "config" not in r.json()["items"][0]


async def test_disabled_agent_cannot_run(client, make_token):
    r = await client.post("/v1/agents/bp1-project-qa/runs", json={"input": "hi"}, headers=bearer(make_token()))
    assert r.status_code == 404


async def test_run_echo_and_sse(client, make_token):
    token = make_token()
    r = await client.post("/v1/agents/echo-demo/runs", json={"input": "привет"}, headers=bearer(token))
    assert r.status_code == 202
    assert r.headers["x-quota-remaining"] == "2"
    run = r.json()
    assert run["status"] == "queued" and run["user_sub"] == "u-1"

    sse = await client.get(f"/v1/runs/{run['id']}/events", headers=bearer(token))
    assert sse.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(sse.text)
    names = [e for e, _ in events]
    assert names[0] == "status" and names[-1] == "done"
    assert "step" in names and "message" in names
    done = events[-1][1]["run"]
    assert done["status"] == "succeeded" and done["output"] == "Эхо: привет"
    assert done["trace_id"] == run["id"] and done["thread_id"]


async def test_sse_replay_with_last_event_id(client, make_token):
    token = make_token()
    run = (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(token))).json()
    await wait_done(client, token, run["id"])
    full = parse_sse((await client.get(f"/v1/runs/{run['id']}/events", headers=bearer(token))).text)
    tail = await client.get(f"/v1/runs/{run['id']}/events", headers={**bearer(token), "Last-Event-ID": "2"})
    assert len(parse_sse(tail.text)) == len(full) - 2


async def test_langgraph_kind_records_thread_and_trace(client, make_token):
    token = make_token()
    run = (await client.post("/v1/agents/agent1-qa/runs", json={"input": "2+2"}, headers=bearer(token))).json()
    done = await wait_done(client, token, run["id"])
    assert done["output"] == "4" and done["thread_id"] == "t-1" and done["trace_id"] == "trace-xyz"

    # continue the conversation in the same thread
    again = await client.post("/v1/agents/agent1-qa/runs", json={"input": "x3", "thread_id": "t-1"}, headers=bearer(token))
    assert again.status_code == 202 and again.json()["thread_id"] == "t-1"


async def test_foreign_thread_is_rejected(client, make_token):
    r = await client.post("/v1/agents/agent1-qa/runs", json={"input": "x", "thread_id": "nope"}, headers=bearer(make_token()))
    assert r.status_code == 422


async def test_failed_run_reports_error_event(client, make_token, services):
    services.runs._runners["echo"] = BoomRunner()
    token = make_token()
    run = (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(token))).json()
    done = await wait_done(client, token, run["id"])
    assert done["status"] == "failed" and done["error"] == "Агент временно недоступен"
    names = [e for e, _ in parse_sse((await client.get(f"/v1/runs/{run['id']}/events", headers=bearer(token))).text)]
    assert names[-1] == "error"


async def test_run_timeout(client, make_token, services):
    services.runs._runners["echo"] = SlowRunner()
    token = make_token()
    run = (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(token))).json()
    done = await wait_done(client, token, run["id"], tries=300)
    assert done["status"] == "failed" and "вовремя" in done["error"]


async def test_validation(client, make_token):
    token = make_token()
    assert (await client.post("/v1/agents/echo-demo/runs", json={"input": ""}, headers=bearer(token))).status_code == 422
    assert (await client.post("/v1/agents/echo-demo/runs", json={"input": "   "}, headers=bearer(token))).status_code == 422
    big = "a" * 9000
    assert (await client.post("/v1/agents/echo-demo/runs", json={"input": big}, headers=bearer(token))).status_code == 422


async def test_quota_429_and_isolation(client, make_token):
    token = make_token()
    for _ in range(3):
        assert (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(token))).status_code == 202
    r = await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(token))
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) >= 1
    assert r.headers["content-type"].startswith("application/problem+json")
    me = (await client.get("/v1/me", headers=bearer(token))).json()
    assert me["quota"]["remaining"] == 0

    other = make_token(sub="u-2", username="bob")  # another user is not affected
    assert (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(other))).status_code == 202


async def test_runs_are_private(client, make_token):
    alice, bob = make_token(), make_token(sub="u-2", username="bob")
    run = (await client.post("/v1/agents/echo-demo/runs", json={"input": "secret"}, headers=bearer(alice))).json()
    assert (await client.get(f"/v1/runs/{run['id']}", headers=bearer(bob))).status_code == 404
    assert (await client.get(f"/v1/runs/{run['id']}/events", headers=bearer(bob))).status_code == 404
    assert (await client.get("/v1/runs", headers=bearer(bob))).json()["total"] == 0
    assert (await client.get("/v1/runs", headers=bearer(alice))).json()["total"] == 1

    admin = make_token(sub="a-1", groups=["alexsoft-admins"], username="root")
    assert (await client.get(f"/v1/runs/{run['id']}", headers=bearer(admin))).status_code == 200


# ------------------------------------------------------------------ admin
async def test_admin_endpoints_require_admin(client, make_token):
    token = make_token()
    for path in ("/v1/admin/users", "/v1/admin/runs", "/v1/admin/stats", "/v1/admin/agents", "/v1/admin/settings"):
        assert (await client.get(path, headers=bearer(token))).status_code == 403, path


async def test_admin_settings_change_quota(client, make_token):
    admin = make_token(sub="a-1", groups=["alexsoft-admins"], username="root")
    r = await client.put("/v1/admin/settings", json={"daily_run_quota": 1}, headers=bearer(admin))
    assert r.status_code == 200 and r.json() == {"daily_run_quota": 1}
    user = make_token()
    assert (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(user))).status_code == 202
    assert (await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(user))).status_code == 429
    assert (await client.put("/v1/admin/settings", json={"daily_run_quota": -1}, headers=bearer(admin))).status_code == 422


async def test_admin_toggle_agent_and_stats(client, make_token):
    admin = make_token(sub="a-1", groups=["alexsoft-admins"], username="root")
    r = await client.patch("/v1/admin/agents/bp1-project-qa", json={"enabled": True}, headers=bearer(admin))
    assert r.status_code == 200 and r.json()["enabled"] is True
    assert "bp1-project-qa" in [a["id"] for a in (await client.get("/v1/agents", headers=bearer(make_token()))).json()["items"]]
    assert (await client.patch("/v1/admin/agents/nope", json={"enabled": True}, headers=bearer(admin))).status_code == 404
    assert (await client.patch("/v1/admin/agents/echo-demo", json={}, headers=bearer(admin))).status_code == 422

    await client.post("/v1/agents/echo-demo/runs", json={"input": "x"}, headers=bearer(make_token()))
    stats = (await client.get("/v1/admin/stats", headers=bearer(admin))).json()
    assert stats["runs_total"] == 1 and stats["active_users_today"] == 1
    assert stats["by_agent"] == [{"agent_id": "echo-demo", "runs": 1}]
    runs = (await client.get("/v1/admin/runs?user_sub=u-1", headers=bearer(admin))).json()
    assert runs["total"] == 1
    assert (await client.get("/v1/admin/runs?status=bogus", headers=bearer(admin))).status_code == 422


async def test_admin_users_via_authentik(client, make_token, authentik_calls):
    admin = make_token(sub="admin-1", groups=["alexsoft-admins"], username="root")
    r = await client.get("/v1/admin/users?search=ali", headers=bearer(admin))
    assert r.status_code == 200
    assert r.json()["items"][0]["username"] == "alice" and r.json()["items"][0]["groups"] == ["alexsoft-users"]
    assert any("search=ali" in q for _, _, q in authentik_calls)

    r = await client.patch("/v1/admin/users/7", json={"is_active": False}, headers=bearer(admin))
    assert r.status_code == 200 and r.json()["is_active"] is False

    # an admin cannot deactivate themselves (user 9 has uid == the admin's sub)
    r = await client.patch("/v1/admin/users/9", json={"is_active": False}, headers=bearer(admin))
    assert r.status_code == 409

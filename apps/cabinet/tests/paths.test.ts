import assert from "node:assert/strict";
import test from "node:test";
import { groupsFromClaims, isSameOrigin, jwtPayload, rolesFromGroups, safeReturnTo } from "../src/lib/paths.ts";

test("safeReturnTo keeps local /app paths", () => {
  assert.equal(safeReturnTo("/app"), "/app");
  assert.equal(safeReturnTo("/app/agents/echo-demo"), "/app/agents/echo-demo");
  assert.equal(safeReturnTo("/app?x=1"), "/app?x=1");
});

test("safeReturnTo rejects open redirects", () => {
  for (const bad of ["https://evil.example", "//evil.example", "/other", "/appx", "/app\\evil", "/app/\r\nSet-Cookie: a=b", "", null, undefined]) {
    assert.equal(safeReturnTo(bad as string), "/app", String(bad));
  }
});

test("rolesFromGroups: admin includes user", () => {
  assert.deepEqual(rolesFromGroups(["alexsoft-admins"], "alexsoft-admins", "alexsoft-users"), ["user", "admin"]);
  assert.deepEqual(rolesFromGroups(["alexsoft-users"], "alexsoft-admins", "alexsoft-users"), ["user"]);
  assert.deepEqual(rolesFromGroups(["other"], "alexsoft-admins", "alexsoft-users"), []);
});

test("jwtPayload / groupsFromClaims", () => {
  const body = Buffer.from(JSON.stringify({ groups: ["a", "b"] })).toString("base64url");
  const token = `x.${body}.y`;
  assert.deepEqual(groupsFromClaims(undefined, jwtPayload(token)), ["a", "b"]);
  assert.deepEqual(jwtPayload("garbage"), {});
  assert.deepEqual(groupsFromClaims({}, undefined), []);
});

test("isSameOrigin", () => {
  assert.equal(isSameOrigin("http://alexsoft.localhost:8000", "http://alexsoft.localhost:8000"), true);
  assert.equal(isSameOrigin("http://evil.example", "http://alexsoft.localhost:8000"), false);
  assert.equal(isSameOrigin(null, "http://alexsoft.localhost:8000"), false);
});

import { createHmac, randomBytes } from "node:crypto";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ready } from "./db";
import { env } from "./env";
import { groupsFromClaims, jwtPayload, rolesFromGroups } from "./paths";
import { refresh } from "./oidc";

export const SESSION_COOKIE = "alexsoft_session";
export const LOGIN_COOKIE = "alexsoft_login";
const SESSION_TTL_MS = 30 * 24 * 3600 * 1000; // matches the refresh token validity in the Authentik blueprint
const LOGIN_TTL_MS = 10 * 60 * 1000;
const SKEW_MS = 30 * 1000;

export interface Session {
  sub: string;
  username: string;
  name: string;
  email: string;
  groups: string[];
  roles: string[];
  accessToken: string;
  refreshToken?: string;
  idToken?: string;
  /** access token expiry, epoch ms */
  expiresAt: number;
}

interface LoginRecord {
  verifier: string;
  nonce: string;
  returnTo: string;
}

const hashKey = (prefix: string, id: string) =>
  `${prefix}:${createHmac("sha256", env.sessionSecret).update(id).digest("hex")}`;

async function put(key: string, data: unknown, ttlMs: number) {
  const db = await ready();
  await db.query(
    `INSERT INTO cabinet.sessions (key, data, expires_at) VALUES ($1, $2, now() + ($3 || ' milliseconds')::interval)
     ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, expires_at = EXCLUDED.expires_at`,
    [key, JSON.stringify(data), String(ttlMs)],
  );
}

async function get<T>(key: string): Promise<T | null> {
  const db = await ready();
  const r = await db.query("SELECT data FROM cabinet.sessions WHERE key = $1 AND expires_at > now()", [key]);
  return r.rows[0]?.data ?? null;
}

async function del(key: string) {
  const db = await ready();
  await db.query("DELETE FROM cabinet.sessions WHERE key = $1", [key]);
}

// ---------------------------------------------------------------- login state (state -> PKCE verifier, nonce)
export async function saveLogin(state: string, rec: LoginRecord) {
  const db = await ready();
  await db.query("DELETE FROM cabinet.sessions WHERE expires_at < now()"); // opportunistic cleanup
  await put(hashKey("login", state), rec, LOGIN_TTL_MS);
}

export async function takeLogin(state: string): Promise<LoginRecord | null> {
  const key = hashKey("login", state);
  const rec = await get<LoginRecord>(key);
  if (rec) await del(key); // single use
  return rec;
}

// ---------------------------------------------------------------- sessions
export function newSessionId(): string {
  return randomBytes(32).toString("base64url");
}

export function sessionFrom(tokens: {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
  expiresIn: number | undefined;
  claims?: Record<string, unknown>;
}): Session {
  const access = jwtPayload(tokens.access_token);
  const claims = tokens.claims ?? {};
  const groups = groupsFromClaims(claims, access);
  return {
    sub: String(claims.sub ?? access.sub ?? ""),
    username: String(claims.preferred_username ?? access.preferred_username ?? ""),
    name: String(claims.name ?? access.name ?? ""),
    email: String(claims.email ?? access.email ?? ""),
    groups,
    roles: rolesFromGroups(groups, env.groupAdmin, env.groupUser),
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    idToken: tokens.id_token,
    expiresAt: Date.now() + (tokens.expiresIn ?? 300) * 1000,
  };
}

export async function createSession(session: Session): Promise<string> {
  const sid = newSessionId();
  await put(hashKey("sess", sid), session, SESSION_TTL_MS);
  return sid;
}

export const sessionCookieOptions = (maxAgeMs: number) => ({
  httpOnly: true,
  sameSite: "lax" as const,
  secure: env.secureCookies,
  path: "/app",
  maxAge: Math.floor(maxAgeMs / 1000),
});
export const SESSION_MAX_AGE_MS = SESSION_TTL_MS;
export const LOGIN_MAX_AGE_MS = LOGIN_TTL_MS;

export async function destroySession(sid: string): Promise<Session | null> {
  const key = hashKey("sess", sid);
  const s = await get<Session>(key);
  await del(key);
  return s;
}

type G = typeof globalThis & { __refreshing?: Map<string, Promise<Session | null>> };
const g = globalThis as G;

/** Refresh the access token (one in-flight refresh per session). Drops the session if the IdP refuses. */
async function refreshSession(sid: string, s: Session): Promise<Session | null> {
  g.__refreshing ??= new Map();
  const inflight = g.__refreshing.get(sid);
  if (inflight) return inflight;
  const p = (async () => {
    if (!s.refreshToken) {
      await destroySession(sid);
      return null;
    }
    try {
      const t = await refresh(s.refreshToken);
      const next = sessionFrom({
        access_token: t.access_token,
        refresh_token: t.refresh_token ?? s.refreshToken,
        id_token: t.id_token ?? s.idToken,
        expiresIn: t.expiresIn(),
        claims: (t.claims() as Record<string, unknown> | undefined) ?? undefined,
      });
      // keep identity fields if the refresh response carried no id_token
      const merged: Session = {
        ...next,
        sub: next.sub || s.sub,
        username: next.username || s.username,
        name: next.name || s.name,
        email: next.email || s.email,
        groups: next.groups.length ? next.groups : s.groups,
      };
      merged.roles = rolesFromGroups(merged.groups, env.groupAdmin, env.groupUser);
      await put(hashKey("sess", sid), merged, SESSION_TTL_MS);
      return merged;
    } catch (e) {
      console.warn("token refresh failed, dropping session:", (e as Error).message);
      await destroySession(sid);
      return null;
    }
  })().finally(() => g.__refreshing?.delete(sid));
  g.__refreshing.set(sid, p);
  return p;
}

export async function getSessionId(): Promise<string | null> {
  return (await cookies()).get(SESSION_COOKIE)?.value ?? null;
}

/** Current session with a fresh access token, or null. */
export async function getSession(opts: { forceRefresh?: boolean } = {}): Promise<Session | null> {
  const sid = await getSessionId();
  if (!sid) return null;
  const s = await get<Session>(hashKey("sess", sid));
  if (!s) return null;
  if (opts.forceRefresh || s.expiresAt - SKEW_MS < Date.now()) return refreshSession(sid, s);
  return s;
}

/** For pages: redirect to login when there is no session. */
export async function requireSession(returnTo = "/app"): Promise<Session> {
  const s = await getSession();
  if (!s) redirect(`/api/auth/login?returnTo=${encodeURIComponent(returnTo)}`);
  return s;
}

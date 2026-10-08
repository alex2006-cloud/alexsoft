import { NextRequest, NextResponse } from "next/server";
import { env } from "@/lib/env";
import { exchangeCode } from "@/lib/oidc";
import { safeReturnTo } from "@/lib/paths";
import {
  LOGIN_COOKIE,
  SESSION_COOKIE,
  SESSION_MAX_AGE_MS,
  createSession,
  sessionCookieOptions,
  sessionFrom,
  takeLogin,
} from "@/lib/session";

export const dynamic = "force-dynamic";

function fail(reason: string) {
  const res = NextResponse.redirect(`${env.siteUrl}/app/login-error?reason=${reason}`, 303);
  res.cookies.delete({ name: LOGIN_COOKIE, path: "/app" });
  return res;
}

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const state = params.get("state");
  const cookieState = req.cookies.get(LOGIN_COOKIE)?.value;
  if (params.get("error")) {
    // Authentik maps many failures (empty grant_types, bad redirect, cancel) to error=...
    console.error("oidc callback error:", params.get("error"), params.get("error_description"));
    return fail(params.get("error") === "access_denied" ? "denied" : "exchange");
  }
  if (!state || !cookieState || state !== cookieState) return fail("state");

  const login = await takeLogin(state);
  if (!login) return fail("expired");

  try {
    const tokens = await exchangeCode(req.nextUrl.search, { verifier: login.verifier, state, nonce: login.nonce });
    const session = sessionFrom({
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
      id_token: tokens.id_token,
      expiresIn: tokens.expiresIn(),
      claims: tokens.claims() as Record<string, unknown> | undefined,
    });
    if (!session.sub) return fail("claims");
    const sid = await createSession(session);
    const res = NextResponse.redirect(`${env.siteUrl}${safeReturnTo(login.returnTo)}`, 303);
    res.cookies.set(SESSION_COOKIE, sid, sessionCookieOptions(SESSION_MAX_AGE_MS));
    res.cookies.delete({ name: LOGIN_COOKIE, path: "/app" });
    return res;
  } catch (e) {
    console.error("code exchange failed:", e);
    return fail("exchange");
  }
}

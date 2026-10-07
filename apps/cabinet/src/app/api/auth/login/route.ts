import { NextRequest, NextResponse } from "next/server";
import { env } from "@/lib/env";
import { buildLoginUrl, newPkce } from "@/lib/oidc";
import { safeReturnTo } from "@/lib/paths";
import { LOGIN_COOKIE, LOGIN_MAX_AGE_MS, saveLogin, sessionCookieOptions } from "@/lib/session";

export const dynamic = "force-dynamic";

// GET /app/api/auth/login?returnTo=/app/...&screen=register
export async function GET(req: NextRequest) {
  const returnTo = safeReturnTo(req.nextUrl.searchParams.get("returnTo"));
  const register = req.nextUrl.searchParams.get("screen") === "register";
  try {
    const { verifier, state, nonce } = newPkce();
    await saveLogin(state, { verifier, nonce, returnTo });
    const authorize = await buildLoginUrl({ state, nonce, verifier });

    let target: string;
    if (register) {
      // Self-registration flow in Authentik; afterwards it continues to the authorize URL (already signed in)
      const next = encodeURIComponent(authorize.pathname + authorize.search);
      target = `${env.authUrl}/if/flow/alexsoft-enrollment/?next=${next}`;
    } else {
      target = authorize.toString();
    }
    const res = NextResponse.redirect(target, 303);
    res.cookies.set(LOGIN_COOKIE, state, sessionCookieOptions(LOGIN_MAX_AGE_MS));
    return res;
  } catch (e) {
    console.error("login failed:", e);
    return NextResponse.redirect(`${env.siteUrl}/app/login-error?reason=idp`, 303);
  }
}

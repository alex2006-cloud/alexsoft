import { NextRequest, NextResponse } from "next/server";
import { env } from "@/lib/env";
import { endSessionUrl } from "@/lib/oidc";
import { isSameOrigin } from "@/lib/paths";
import { SESSION_COOKIE, destroySession } from "@/lib/session";

export const dynamic = "force-dynamic";

// POST only: a GET logout link would let any page sign the user out (CSRF).
export async function POST(req: NextRequest) {
  if (!isSameOrigin(req.headers.get("origin"), env.siteUrl)) {
    return NextResponse.json({ error: "bad origin" }, { status: 403 });
  }
  const sid = req.cookies.get(SESSION_COOKIE)?.value;
  const session = sid ? await destroySession(sid) : null;

  // End the Authentik SSO session too, otherwise "sign in" would silently log the user back in.
  let target = `${env.siteUrl}/app/signed-out`;
  try {
    const idp = await endSessionUrl(session?.idToken);
    if (idp) target = idp.toString();
  } catch (e) {
    console.warn("end_session unavailable:", (e as Error).message);
  }
  const res = NextResponse.redirect(target, 303);
  res.cookies.delete({ name: SESSION_COOKIE, path: "/app" });
  return res;
}

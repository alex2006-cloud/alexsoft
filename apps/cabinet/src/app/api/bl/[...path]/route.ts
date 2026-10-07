import { NextRequest, NextResponse } from "next/server";
import { blFetch } from "@/lib/bl";
import { env } from "@/lib/env";
import { isSameOrigin } from "@/lib/paths";
import { getSession } from "@/lib/session";

export const dynamic = "force-dynamic";

// BFF: the browser talks to the cabinet only; the cabinet forwards to the BL with the user's Bearer token.
// Authorization is decided by the BL (it validates the JWT and roles itself). SSE is streamed through.

const FORWARD_REQ = ["content-type", "accept", "last-event-id", "x-request-id"];
const FORWARD_RES = ["content-type", "cache-control", "retry-after", "x-quota-remaining", "x-request-id"];

async function handle(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  if (path[0] !== "v1") return NextResponse.json({ title: "Not found", status: 404 }, { status: 404 });

  if (!["GET", "HEAD"].includes(req.method) && !isSameOrigin(req.headers.get("origin"), env.siteUrl)) {
    return NextResponse.json({ title: "Bad origin", status: 403 }, { status: 403 });
  }
  const session = await getSession();
  if (!session) return NextResponse.json({ title: "Not signed in", status: 401 }, { status: 401 });

  const headers = new Headers();
  for (const h of FORWARD_REQ) {
    const v = req.headers.get(h);
    if (v) headers.set(h, v);
  }
  const hasBody = !["GET", "HEAD"].includes(req.method);
  const upstream = await blFetch(
    `/${path.map(encodeURIComponent).join("/")}${req.nextUrl.search}`,
    { method: req.method, headers, body: hasBody ? await req.text() : undefined, signal: req.signal },
    session,
  ).catch(() => null);
  if (!upstream) return NextResponse.json({ title: "BL unavailable", status: 503 }, { status: 503 });

  const out = new Headers();
  for (const h of FORWARD_RES) {
    const v = upstream.headers.get(h);
    if (v) out.set(h, v);
  }
  if ((upstream.headers.get("content-type") || "").startsWith("text/event-stream")) {
    out.set("cache-control", "no-cache, no-transform");
    out.set("x-accel-buffering", "no");
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export const GET = handle;
export const POST = handle;
export const PATCH = handle;
export const PUT = handle;

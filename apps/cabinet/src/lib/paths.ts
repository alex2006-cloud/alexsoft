// Pure helpers (no Next imports) so they can be unit-tested with `node --test`.

/** Only same-site paths under /app are accepted as post-login targets (no open redirects). */
export function safeReturnTo(raw: string | null | undefined): string {
  const fallback = "/app";
  if (!raw) return fallback;
  if (!raw.startsWith("/app")) return fallback;
  if (raw.startsWith("//") || raw.includes("\\") || /[\r\n]/.test(raw)) return fallback;
  if (raw !== "/app" && !raw.startsWith("/app/") && !raw.startsWith("/app?")) return fallback;
  return raw;
}

/** Roles for UI gating. The authority is the BL API (it validates the JWT itself). */
export function rolesFromGroups(groups: string[], groupAdmin: string, groupUser: string): string[] {
  if (groups.includes(groupAdmin)) return ["user", "admin"];
  if (groups.includes(groupUser)) return ["user"];
  return [];
}

/** Decode the payload of a JWT without verifying it (used only to read the `groups` claim for the UI). */
export function jwtPayload(token: string): Record<string, unknown> {
  try {
    const part = token.split(".")[1];
    if (!part) return {};
    const json = Buffer.from(part.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8");
    const v = JSON.parse(json);
    return v && typeof v === "object" ? (v as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

export function groupsFromClaims(...sources: Array<Record<string, unknown> | undefined>): string[] {
  for (const s of sources) {
    const g = s?.groups;
    if (Array.isArray(g)) return g.map(String);
  }
  return [];
}

/** Same-origin check for state-changing BFF requests (CSRF defence in addition to SameSite=Lax). */
export function isSameOrigin(originHeader: string | null, siteUrl: string): boolean {
  if (!originHeader) return false;
  try {
    return new URL(originHeader).origin === new URL(siteUrl).origin;
  } catch {
    return false;
  }
}

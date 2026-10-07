// Server-side configuration. Values come from the repo-root .env (loaded in next.config.ts).

function req(name: string, fallback?: string): string {
  const v = process.env[name] || fallback;
  if (!v) throw new Error(`${name} is not set (see .env.example, run infra/authentik/init-env.ps1)`);
  return v;
}

export const env = {
  /** Public origin of the site, e.g. http://alexsoft.localhost:8000 */
  get siteUrl(): string {
    return req("PUBLIC_SITE_URL", "http://alexsoft.localhost:8000").replace(/\/$/, "");
  },
  /** Public origin of Authentik, e.g. http://auth.alexsoft.localhost:8000 */
  get authUrl(): string {
    return req("AUTH_PUBLIC_URL", "http://auth.alexsoft.localhost:8000").replace(/\/$/, "");
  },
  get issuer(): string {
    return `${this.authUrl}/application/o/${req("OIDC_APP_SLUG", "alexsoft-cabinet")}/`;
  },
  get clientId(): string {
    return req("OIDC_CLIENT_ID", "alexsoft-cabinet");
  },
  get clientSecret(): string {
    return req("OIDC_CLIENT_SECRET");
  },
  get sessionSecret(): string {
    return req("AUTH_SECRET");
  },
  get blUrl(): string {
    return req("BL_URL", `http://127.0.0.1:${process.env.BL_PORT || "8100"}`).replace(/\/$/, "");
  },
  get secureCookies(): boolean {
    return this.siteUrl.startsWith("https://");
  },
  get redirectUri(): string {
    return `${this.siteUrl}/app/api/auth/callback`;
  },
  groupAdmin: process.env.BL_GROUP_ADMIN || "alexsoft-admins",
  groupUser: process.env.BL_GROUP_USER || "alexsoft-users",
  /** Links shown in the admin panel (local defaults from the port table in README). */
  adminLinks: {
    get authentik(): string {
      return `${env.authUrl}/if/admin/`;
    },
    grafana: process.env.GRAFANA_URL || `http://127.0.0.1:${process.env.GRAFANA_PORT || "3001"}`,
    metabase: process.env.METABASE_URL || `http://127.0.0.1:${process.env.METABASE_PORT || "3002"}`,
    litellm: process.env.LITELLM_UI_URL || `http://127.0.0.1:${process.env.LITELLM_PORT || "8080"}/ui`,
  },
};

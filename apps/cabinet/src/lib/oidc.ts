import * as client from "openid-client";
import { env } from "./env";

// OIDC client for Authentik: Authorization Code + PKCE, exchanged on the server (ADR-0019).
// Discovery goes through the public auth host, so the gateway (or Authentik via *.localhost) must be reachable.

type G = typeof globalThis & { __oidcConfig?: Promise<client.Configuration> };
const g = globalThis as G;

export function oidcConfig(): Promise<client.Configuration> {
  g.__oidcConfig ??= client
    .discovery(new URL(env.issuer), env.clientId, env.clientSecret, undefined, {
      // local dev runs over http://*.localhost; production is https and ignores this
      execute: env.authUrl.startsWith("http://") ? [client.allowInsecureRequests] : [],
    })
    .catch((e) => {
      g.__oidcConfig = undefined;
      throw e;
    });
  return g.__oidcConfig;
}

export const SCOPE = "openid profile email offline_access";

export async function buildLoginUrl(args: { state: string; nonce: string; verifier: string }): Promise<URL> {
  const cfg = await oidcConfig();
  const challenge = await client.calculatePKCECodeChallenge(args.verifier);
  return client.buildAuthorizationUrl(cfg, {
    redirect_uri: env.redirectUri,
    scope: SCOPE,
    code_challenge: challenge,
    code_challenge_method: "S256",
    state: args.state,
    nonce: args.nonce,
  });
}

export async function exchangeCode(search: string, checks: { verifier: string; state: string; nonce: string }) {
  const cfg = await oidcConfig();
  // The URL the browser came back to (through the gateway), not the internal localhost:3020 one.
  const current = new URL(env.redirectUri + search);
  return client.authorizationCodeGrant(cfg, current, {
    pkceCodeVerifier: checks.verifier,
    expectedState: checks.state,
    expectedNonce: checks.nonce,
    idTokenExpected: true,
  });
}

export async function refresh(refreshToken: string) {
  const cfg = await oidcConfig();
  return client.refreshTokenGrant(cfg, refreshToken);
}

export async function endSessionUrl(idToken: string | undefined): Promise<URL | null> {
  const cfg = await oidcConfig();
  if (!cfg.serverMetadata().end_session_endpoint) return null;
  return client.buildEndSessionUrl(cfg, {
    post_logout_redirect_uri: `${env.siteUrl}/app`,
    ...(idToken ? { id_token_hint: idToken } : {}),
  });
}

export const newPkce = () => ({
  verifier: client.randomPKCECodeVerifier(),
  state: client.randomState(),
  nonce: client.randomNonce(),
});

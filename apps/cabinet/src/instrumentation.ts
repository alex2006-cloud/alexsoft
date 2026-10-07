// Runs once in the server process. The repo-root .env is the source of truth (see .env.example);
// next.config.ts loads it for the build tooling, but the render/route runtime can be a separate process
// (Turbopack dev), so load it here too. Real environment variables always win over .env.

export async function register() {
  if (process.env.NEXT_RUNTIME === "edge") return;
  const path = await import("node:path");
  const { loadEnvConfig } = await import("@next/env");
  loadEnvConfig(path.resolve(process.cwd(), "../.."));
}

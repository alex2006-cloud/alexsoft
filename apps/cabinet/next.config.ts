import path from "node:path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// Source of truth is the repo-root .env (see .env.example); load it before anything reads process.env.
loadEnvConfig(path.resolve(process.cwd(), "../.."));

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  agentRules: false,
  // Cabinet lives under /app behind the Nginx gateway (ADR-0019/0020); BFF is /app/api/*.
  basePath: "/app",
  // The gateway serves the dev server under *.localhost:8000
  allowedDevOrigins: ["alexsoft.localhost", "auth.alexsoft.localhost"],
};

export default nextConfig;

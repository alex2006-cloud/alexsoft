import type { NextConfig } from "next";

const devRewrites =
  process.env.NODE_ENV === "development"
    ? {
        async rewrites() {
          return [
            { source: "/games", destination: "http://127.0.0.1:3010/games" },
            {
              source: "/games/:path*",
              destination: "http://127.0.0.1:3010/games/:path*",
            },
          ];
        },
      }
    : {};

const nextConfig: NextConfig = {
  reactStrictMode: true,
  agentRules: false,
  output: "export",
  ...devRewrites,
};

export default nextConfig;

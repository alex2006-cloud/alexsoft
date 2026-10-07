import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  allowedDevOrigins: ["alexsoft.localhost", "auth.alexsoft.localhost"],
  agentRules: false,
  output: "export",
  basePath: "/games",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

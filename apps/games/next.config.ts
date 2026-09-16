import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  agentRules: false,
  output: "export",
  basePath: "/games",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;

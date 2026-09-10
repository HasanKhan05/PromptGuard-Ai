import type { NextConfig } from "next";

const isGitHubPages = process.env.GITHUB_ACTIONS === "true";
const repositoryBasePath = "/PromptGuard-Ai";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath: isGitHubPages ? repositoryBasePath : "",
  assetPrefix: isGitHubPages ? `${repositoryBasePath}/` : "",
};

export default nextConfig;

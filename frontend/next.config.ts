import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enables smaller Docker images via .next/standalone
  output: "standalone",
  images: {
    // User-generated media from API / CDN / object storage
    remotePatterns: [
      { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" },
      { protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" },
      { protocol: "https", hostname: "**" },
    ],
    formats: ["image/avif", "image/webp"],
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "@radix-ui/react-avatar", "@radix-ui/react-dialog"],
  },
};

export default nextConfig;

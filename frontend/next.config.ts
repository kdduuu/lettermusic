import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  async headers() {
    return [
      {
        source: "/redefinir-senha",
        headers: [
          { key: "Referrer-Policy", value: "no-referrer" },
        ],
      },
      {
        source: "/confirmar-email",
        headers: [
          { key: "Referrer-Policy", value: "no-referrer" },
        ],
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "coverartarchive.org",
        pathname: "/release-group/**",
      },
    ],
  },
};

export default nextConfig;
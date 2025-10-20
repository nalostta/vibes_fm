import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    domains: ["i.ytimg.com", "img.youtube.com", "images.soundcloud.com"],
    remotePatterns: [
      { protocol: "https", hostname: "i.ytimg.com" },
      { protocol: "https", hostname: "img.youtube.com" },
      // add more if you host covers elsewhere, e.g. SoundCloud CDN
      { protocol: "https", hostname: "images.soundcloud.com" },
    ],
  },
};

export default nextConfig;

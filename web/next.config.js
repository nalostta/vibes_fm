/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export only in production (dev uses default behavior)
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,

  images: {
    unoptimized: true,
    domains: ['i.ytimg.com', 'img.youtube.com', 'images.soundcloud.com'],
  },

  reactStrictMode: true,
  swcMinify: true,
  trailingSlash: true,

  productionBrowserSourceMaps: false,

  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: true },
};

module.exports = nextConfig;

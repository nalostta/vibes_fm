/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for GitHub Pages (served at custom domain root)
  output: 'export',

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

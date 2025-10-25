/** @type {import('next').NextConfig} */
const nextConfig = {
  // Only enable output: 'export' in production
  ...(process.env.NODE_ENV === 'production' ? { output: 'export' } : {}),
  
  images: {
    unoptimized: true,
    domains: ['i.ytimg.com', 'img.youtube.com', 'images.soundcloud.com'],
    remotePatterns: [
      { protocol: 'https', hostname: 'i.ytimg.com' },
      { protocol: 'https', hostname: 'img.youtube.com' },
      // add more if you host covers elsewhere, e.g. SoundCloud CDN
      { protocol: 'https', hostname: 'images.soundcloud.com' },
    ],
  },
  basePath: process.env.NODE_ENV === 'production' ? '/vibes_fm' : '',
  assetPrefix: process.env.NODE_ENV === 'production' ? '/vibes_fm' : '',
  // Enable React Strict Mode
  reactStrictMode: true,
  // Enable SWC minification
  swcMinify: true,
};

module.exports = nextConfig;

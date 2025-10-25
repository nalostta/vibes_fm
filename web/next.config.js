/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === 'production';
const isGHPages = process.env.GITHUB_ACTIONS === 'true';

const nextConfig = {
  // Only enable output: 'export' in production
  ...(isProd ? { output: 'export' } : {}),
  
  images: {
    unoptimized: true,
    domains: ['i.ytimg.com', 'img.youtube.com', 'images.soundcloud.com'],
    remotePatterns: [
      { protocol: 'https', hostname: 'i.ytimg.com' },
      { protocol: 'https', hostname: 'img.youtube.com' },
      { protocol: 'https', hostname: 'images.soundcloud.com' },
    ],
  },
  
  // Only add basePath and assetPrefix for GitHub Pages deployment, not for custom domain
  ...(isGHPages ? {
    basePath: '/vibes_fm',
    assetPrefix: '/vibes_fm/'
  } : {
    basePath: '',
    assetPrefix: ''
  }),
  
  // Ensure trailing slash for static exports
  trailingSlash: true,
  
  // Enable React Strict Mode
  reactStrictMode: true,
  
  // Enable SWC minification
  swcMinify: true,
};

module.exports = nextConfig;

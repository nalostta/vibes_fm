/** @type {import('next').NextConfig} */
const isGHPages = process.env.GITHUB_ACTIONS === 'true';

const nextConfig = {
  // Enable static export
  output: 'export',
  
  // Configure base path for GitHub Pages
  ...(isGHPages && {
    basePath: '/vibes_fm',
    assetPrefix: '/vibes_fm/',
  }),
  
  // Image optimization configuration
  images: {
    unoptimized: true,
    domains: ['i.ytimg.com', 'img.youtube.com', 'images.soundcloud.com'],
  },
  
  // Enable React Strict Mode
  reactStrictMode: true,
  
  // Enable SWC minification
  swcMinify: true,
  
  // Add trailing slash for static exports
  trailingSlash: true,
  
  // Custom webpack configuration
  webpack: (config) => {
    // Add file-loader for static files
    config.module.rules.push({
      test: /\.(png|jpg|gif|svg|eot|ttf|woff|woff2)$/,
      type: 'asset/resource',
    });
    
    return config;
  },
};

module.exports = nextConfig;

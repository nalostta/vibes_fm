/** @type {import('next').NextConfig} */
const isGHPages = process.env.GITHUB_ACTIONS === 'true';

const nextConfig = {
  // Enable static export
  output: 'export',
  
  // Configure base path for GitHub Pages
  ...(isGHPages && {
    basePath: '/vibes_fm',
    assetPrefix: '/vibes_fm',
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
  webpack: (config, { isServer }) => {
    // Add file-loader for static files
    config.module.rules.push({
      test: /\.(png|jpg|gif|svg|eot|ttf|woff|woff2)$/,
      type: 'asset/resource',
      generator: {
        filename: 'static/media/[name].[hash][ext]',
      },
    });
    
    // Fix for webpack 5 and static exports
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
      };
    }
    
    return config;
  },
  
  // Customize the output directory for static export
  distDir: 'out',
  
  // Disable image optimization API (not needed for static export)
  images: {
    unoptimized: true,
  },
  
  // Ensure static export works with next/link
  experimental: {
    scrollRestoration: true,
  },
};

// Only enable assetPrefix in production
if (process.env.NODE_ENV === 'production' && isGHPages) {
  nextConfig.assetPrefix = '/vibes_fm';
}

module.exports = nextConfig;

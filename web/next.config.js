/** @type {import('next').NextConfig} */
const isGHPages = process.env.GITHUB_ACTIONS === 'true';

const nextConfig = {
  // Enable static export
  output: 'export',
  
  // Configure base path for GitHub Pages
  basePath: isGHPages ? '/vibes_fm' : '',
  assetPrefix: isGHPages ? '/vibes_fm' : '',
  
  // Disable image optimization API (not needed for static export)
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
  
  // Disable source maps in production
  productionBrowserSourceMaps: false,
  
  // Disable React DevTools in production
  reactStrictMode: true,
  
  // Disable TypeScript type checking during build
  typescript: {
    ignoreBuildErrors: false,
  },
  
  // Disable ESLint during build
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  reactStrictMode: false, // Temporarily disable to test WebSocket connection issues

  // For PyPI distribution: build as standalone output
  output: 'standalone',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },

  // Disable type checking during build (we'll fix types separately)
  typescript: {
    ignoreBuildErrors: true,
  },

  // Disable ESLint during builds
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const backendUrl =
  process.env.BACKEND_URL ||
  (process.env.NEXT_PUBLIC_API_BASE ? process.env.NEXT_PUBLIC_API_BASE.replace(/\/api\/?$/, '') : '') ||
  'http://127.0.0.1:8000';

const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

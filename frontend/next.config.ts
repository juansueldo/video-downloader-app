/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['i.ytimg.com', 'img.youtube.com'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://video-downloader-app-ic05.onrender.com/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

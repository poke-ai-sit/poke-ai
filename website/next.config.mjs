/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow larger request bodies for reference image uploads
  experimental: {
    serverActions: {
      bodySizeLimit: "4mb",
    },
  },
};

export default nextConfig;

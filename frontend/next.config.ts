import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname, // or process.cwd() if you always run from the frontend folder
  },
};

export default nextConfig;
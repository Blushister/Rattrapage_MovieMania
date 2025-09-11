/** @type {import('next').NextConfig} */
const nextConfig = {
   images: {
      remotePatterns: [
         {
            protocol: "https",
            hostname: "image.tmdb.org",
            pathname: "/t/p/**",
         },
      ],
      unoptimized: true, // Désactive l'optimisation des images
   },
   // Configuration pour proxy HTTPS local
   experimental: {
      serverActions: {
         allowedOrigins: ['localhost:8443', 'localhost']
      }
   }
};

export default nextConfig;

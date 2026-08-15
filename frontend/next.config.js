/** @type {import('next').NextConfig} */
const nextConfig = {
  // Il backend serve le thumbnail come file statici: se in futuro vuoi usare
  // next/image con ottimizzazione, aggiungi qui il dominio del backend.
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;

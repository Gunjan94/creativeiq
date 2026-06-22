import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api and /data to the local FastAPI backend (port 8000),
// so the frontend works with no env config out of the box.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: process.env.VITE_BACKEND ?? "http://localhost:8000", changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
      "/data": { target: process.env.VITE_BACKEND ?? "http://localhost:8000", changeOrigin: true },
    },
  },
});

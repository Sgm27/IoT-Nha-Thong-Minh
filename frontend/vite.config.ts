import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vitejs.dev/config/
const backendTarget = process.env.VITE_BACKEND_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/smart-home": {
        target: backendTarget,
        changeOrigin: true,
        ws: true
      },
      "/ws": {
        target: backendTarget,
        changeOrigin: true,
        ws: true
      }
    }
  }
});

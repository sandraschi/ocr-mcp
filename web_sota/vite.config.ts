import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { backendRestartPlugin } from "./vite-plugin-backend-restart";

export default defineConfig({
  plugins: [react(), backendRestartPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 10858,
    host: "127.0.0.1",
    proxy: {
      "/api": {
        target: "http://127.0.0.1:10859",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("error", () => {});
        },
      },
      "/static": {
        target: "http://127.0.0.1:10859",
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on("error", () => {});
        },
      },
    },
  },
});

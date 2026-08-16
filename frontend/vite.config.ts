import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// API_PROXY_TARGET — server-side only (deliberately not VITE_-prefixed, so
// it's never bundled into client JS). Defaults to the local backend so dev
// is unaffected; set on the deployed `web` service to api's real Railway
// domain. Used by both the dev server and `vite preview` (the production
// serving command) — same proxy mechanism, same relative /api/* paths the
// frontend code already calls, no frontend source code change needed.
const apiProxyTarget = process.env.API_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: true,
    // Railway assigns a dynamic *.up.railway.app domain not known until
    // after deploy; Vite 5.4+'s allowedHosts check would otherwise reject
    // it. Low-risk for a public static site being served here regardless.
    allowedHosts: true,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});

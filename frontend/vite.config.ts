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
      // Added 2026-09-15 (changes/2026-09-13-mcp-ai-agent-access.md) — the
      // OAuth consent step (/mcp/oauth/*, backend/src/mcp_access/oauth.py)
      // must be reached through this same origin, not api's domain
      // directly. The session cookie from logging in is scoped to this
      // origin (the SPA's own relative fetches land here); sending a user
      // straight to api's separate domain for consent meant that cookie
      // never arrived, and login appeared to silently do nothing — found
      // against a real Claude connection attempt. The real MCP endpoint
      // (/mcp itself) is included in this same prefix for simplicity, but
      // real MCP clients never reach it through this proxy — they connect
      // to api's domain directly, per VITE_MCP_ENDPOINT_URL.
      "/mcp": {
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
      // Added 2026-09-15 (changes/2026-09-13-mcp-ai-agent-access.md) — the
      // OAuth consent step (/mcp/oauth/*, backend/src/mcp_access/oauth.py)
      // must be reached through this same origin, not api's domain
      // directly. The session cookie from logging in is scoped to this
      // origin (the SPA's own relative fetches land here); sending a user
      // straight to api's separate domain for consent meant that cookie
      // never arrived, and login appeared to silently do nothing — found
      // against a real Claude connection attempt. The real MCP endpoint
      // (/mcp itself) is included in this same prefix for simplicity, but
      // real MCP clients never reach it through this proxy — they connect
      // to api's domain directly, per VITE_MCP_ENDPOINT_URL.
      "/mcp": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});

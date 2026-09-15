import { useState } from "react";

// This deployment's own MCP endpoint — a known constant, not fetched
// (frontend/specs/mcp-access/architecture.md — Data Requirements). Local
// dev default matches how the backend runs per this product's CLAUDE.md;
// override via env once this is ever deployed (not now).
// Trailing slash mandatory, not cosmetic — see backend/src/mcp_access/
// well_known.py's MCP_ENDPOINT_URL for why a bare /mcp silently fails for
// a real MCP client (confirmed against Claude, 2026-09-15).
const MCP_ENDPOINT_URL = import.meta.env.VITE_MCP_ENDPOINT_URL ?? "http://127.0.0.1:8000/mcp/";

const CLIENT_INSTRUCTIONS: { client: string; steps: string }[] = [
  {
    client: "Claude",
    steps: `In Claude, go to Settings → Connectors → Add custom connector, and paste: ${MCP_ENDPOINT_URL}`,
  },
  {
    client: "ChatGPT",
    steps: `In ChatGPT, go to Settings → Connectors → Add connector, and paste: ${MCP_ENDPOINT_URL}`,
  },
  {
    client: "Gemini CLI",
    steps: `Add a remote MCP server pointing at: ${MCP_ENDPOINT_URL}`,
  },
];

export function McpEndpointField() {
  const [copied, setCopied] = useState(false);
  const [expandedClient, setExpandedClient] = useState<string | null>(null);

  async function handleCopy() {
    await navigator.clipboard.writeText(MCP_ENDPOINT_URL);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="space-y-3">
      <div>
        <p className="text-[11px] text-gray-400 mb-1">MCP endpoint</p>
        <div className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2">
          <code className="flex-1 truncate text-xs font-mono text-gray-100">{MCP_ENDPOINT_URL}</code>
          <button
            type="button"
            onClick={handleCopy}
            className="shrink-0 text-xs text-gray-400 hover:text-gray-200 transition-colors duration-150"
          >
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>

      <div className="space-y-1">
        {CLIENT_INSTRUCTIONS.map(({ client, steps }) => {
          const isOpen = expandedClient === client;
          return (
            <div key={client}>
              <button
                type="button"
                onClick={() => setExpandedClient(isOpen ? null : client)}
                className="text-xs text-gray-300 hover:text-gray-100"
              >
                {isOpen ? "▾" : "▸"} {client}
              </button>
              {isOpen && (
                <p className="mt-1 pl-4 text-xs leading-relaxed text-gray-400 transition-all duration-200">
                  {steps}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";
import { useSession } from "../account/useSession";
import { McpEndpointField } from "./McpEndpointField";
import { ConnectionsList } from "./ConnectionsList";

/**
 * The Output Panel's Settings tab content — design/mcp-access/experience.md
 * Part 1. Account-level, not task-level: this looks identical regardless
 * of which Task the user was on when they switched here.
 */
export function SettingsTab() {
  const { user, isLoading } = useSession();

  return (
    <div className="p-3 space-y-4">
      <div>
        <h2 className="text-sm font-medium text-gray-100">Connect your AI</h2>
        <p className="text-[11px] text-gray-400 mt-0.5">
          Ask Claude, ChatGPT, or another AI assistant about the job market, using this
          platform's data.
        </p>
      </div>

      <McpEndpointField />

      {isLoading ? (
        <div className="h-16 rounded-lg bg-gray-700 animate-pulse" />
      ) : user ? (
        <ConnectionsList />
      ) : (
        // Not addressed by design/mcp-access/experience.md directly — Market
        // Health itself is anonymous-accessible, so a visitor can open this
        // tab without ever having signed in. A Connected Assistant needs a
        // real account to attach to, so this is the honest floor: point at
        // sign-in rather than showing a connections list that would just
        // 401.
        <div className="rounded-lg border border-gray-700 bg-gray-800/60 p-3 text-sm text-gray-300">
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300">
            Log in
          </Link>{" "}
          or{" "}
          <Link to="/signup" className="text-indigo-400 hover:text-indigo-300">
            create an account
          </Link>{" "}
          to connect an AI assistant to your own data.
        </div>
      )}
    </div>
  );
}

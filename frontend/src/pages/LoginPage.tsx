import { useSearchParams, Link } from "react-router-dom";
import { LoginForm } from "../features/account/LoginForm";

/**
 * Supports ?next= so the OAuth consent hand-off round-trips correctly —
 * see frontend/specs/mcp-access/architecture.md — Routing, and
 * backend/specs/mcp-access/api.md's GET /mcp/oauth/authorize, which
 * redirects here (a different service/origin) when no session exists yet.
 */
export function LoginPage() {
  const [params] = useSearchParams();
  const next = params.get("next");

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900 px-4">
      <div className="w-full max-w-[360px] rounded-lg border border-gray-700 bg-gray-800 p-6">
        <h1 className="text-2xl font-semibold text-gray-100 mb-1">Log in</h1>
        <p className="text-sm text-gray-400 mb-6">Tech Market Intelligence Platform</p>
        <LoginForm next={next} />
        <p className="mt-4 text-xs text-gray-500">
          Don't have an account?{" "}
          <Link to="/signup" className="text-gray-300 hover:text-gray-100">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}

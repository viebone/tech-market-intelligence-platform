import { useState } from "react";
import { useSessionStore } from "./useSession";

interface LoginFormProps {
  /** Where to send the browser after a successful login. Plain top-level
   * navigation (window.location), not react-router's navigate() — the
   * destination may be a different origin/service entirely (the backend's
   * OAuth consent screen, per frontend/specs/mcp-access/architecture.md —
   * Routing), so this must work the same way regardless of where `next`
   * points. */
  next: string | null;
}

export function LoginForm({ next }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/account/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        // Deliberately the same message regardless of which field was
        // wrong — matches the backend's own deliberate ambiguity
        // (backend/specs/mcp-access/api.md — POST /api/account/login).
        setError("Incorrect email or password.");
        return;
      }
      useSessionStore.getState().setUser(await res.json());
      window.location.href = next || "/";
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-xs font-medium text-gray-400 mb-1">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-gray-100 placeholder-gray-500 outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>
      <div>
        <label htmlFor="password" className="block text-xs font-medium text-gray-400 mb-1">
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-gray-100 placeholder-gray-500 outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-indigo-600 py-2 px-4 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {submitting ? "Signing in…" : "Log in"}
      </button>
    </form>
  );
}

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSessionStore } from "./useSession";

export function SignupForm() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/account/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        if (body.error === "email_already_registered") {
          setError("An account with this email already exists.");
        } else if (body.error === "weak_password") {
          setError("Password must be at least 8 characters.");
        } else if (body.error === "invalid_email") {
          setError("Enter a valid email address.");
        } else {
          setError("Something went wrong. Please try again.");
        }
        return;
      }
      // Signup, like login, stays a plain top-level navigation within this
      // app after success (no external `next` to honour here — a fresh
      // signup can't be mid-OAuth-flow) — react-router's navigate() is fine
      // for this one, since the destination is always "/" within this SPA.
      useSessionStore.getState().setUser(await res.json());
      navigate("/");
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
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-gray-100 placeholder-gray-500 outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <p className="mt-1 text-[11px] text-gray-500">At least 8 characters.</p>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-indigo-600 py-2 px-4 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
      >
        {submitting ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}

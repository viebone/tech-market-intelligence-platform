import { create } from "zustand";

/**
 * This app's first real Zustand store — see frontend/specs/mcp-access/
 * architecture.md — State Management for why. Session state is read from
 * OutputPanel (deep in the market-health tree) and from LoginPage/SignupPage
 * (separate route trees entirely) — no shared parent short of the app root,
 * so a store avoids threading a prop or provider through MarketHealthPage's
 * entire existing tree just for this.
 *
 * Populated once, on app load, by App.tsx calling GET /api/account/me — see
 * backend/specs/mcp-access/api.md.
 */

export interface SessionUser {
  id: number;
  email: string;
  plan: "free" | "premium";
}

interface SessionState {
  user: SessionUser | null;
  /** True until the initial GET /api/account/me on app load resolves — lets
   * a page distinguish "not signed in" from "don't know yet" so it never
   * flashes an unauthenticated state during that first check. */
  isLoading: boolean;
  setUser: (user: SessionUser | null) => void;
  finishLoading: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user }),
  finishLoading: () => set({ isLoading: false }),
}));

/** The one thing the rest of the app should import from this feature —
 * mcp-access never reaches into SignupForm/LoginForm directly. */
export function useSession() {
  return useSessionStore((state) => ({ user: state.user, isLoading: state.isLoading }));
}

export async function bootstrapSession(): Promise<void> {
  try {
    const res = await fetch("/api/account/me", { credentials: "include" });
    if (res.ok) {
      useSessionStore.getState().setUser(await res.json());
    } else {
      useSessionStore.getState().setUser(null);
    }
  } catch {
    // Network error on the very first check — treat as signed-out rather
    // than blocking the rest of the app (Market Health itself needs no
    // session at all).
    useSessionStore.getState().setUser(null);
  } finally {
    useSessionStore.getState().finishLoading();
  }
}

export async function logout(): Promise<void> {
  await fetch("/api/account/logout", { method: "POST", credentials: "include" });
  useSessionStore.getState().setUser(null);
}

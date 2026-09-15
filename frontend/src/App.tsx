import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { MarketHealthPage } from "./pages/MarketHealthPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { bootstrapSession } from "./features/account/useSession";

// First client-side routing in this app — see frontend/specs/mcp-access/
// architecture.md — Routing for why. "/" is MarketHealthPage, completely
// unchanged (it renders even before the session bootstrap below resolves —
// Market Health itself needs no session at all).
export function App() {
  useEffect(() => {
    bootstrapSession();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MarketHealthPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
      </Routes>
    </BrowserRouter>
  );
}

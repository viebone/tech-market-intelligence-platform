source: bug
date: 2026-07-02

Every chat submission in MarketHealthPage is intercepted by a demo simulation onSubmit
function. The real useChat hook is present in the file and already has streamProtocol: "data"
and api: "/api/chat" configured, but handleSubmit/input/handleInputChange are never
destructured or used. The ChatInput is wired to the demo's onSubmit instead.

The demo was intentionally built as a placeholder interaction pattern. Now that the real
Gemini backend is in place, the demo intercept needs to be removed and the form wired to
the real useChat handlers.

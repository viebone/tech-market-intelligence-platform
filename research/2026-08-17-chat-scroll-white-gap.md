---
source: user-feedback
date: 2026-08-17
---

Raw feedback (stakeholder, using the live deployed frontend,
https://web-production-03c43.up.railway.app):

> "everytime I send a chat, a white area appears at the bottom, and then the
> longer the conversation the bigger that gap will be, how can we fix it"

## Diagnosis (done before triage, not just the reported symptom)

Root cause: `MarketHealthPage.tsx`'s layout chain —

```
h-screen (root)
  → flex flex-1 overflow-hidden           (row, line 149)
    → flex flex-col flex-1 min-w-0 overflow-hidden   (centre column, line 155)
      → ConversationThread's flex-1 overflow-y-auto  (ConversationThread.tsx line 69)
```

— is missing `min-h-0` anywhere in the chain. Only `min-w-0` (horizontal) is present.
Flexbox items default to `min-height: auto`, so a flex child with `overflow-y-auto`
sizes to fit its *content* instead of respecting the intended internal-scroll
containment. The container grows taller than the viewport as messages accumulate,
rather than scrolling internally within its own bounds.

Confirmed `<body>` has no background colour set anywhere in the codebase (bare
`<body></body>` in `index.html`, no matching CSS rule) — so once the real page
height exceeds `100vh`, the browser's default white background shows through below
the app. That's the "white area" being reported, and it grows with every message
because each one adds height the layout never reclaims.

This is a real bug against already-implemented specs, not a spec gap —
`design/market-health/experience.md`'s three-zone fixed-layout intent and
`frontend/specs/market-health/architecture.md`'s CSS layout Tech Decision ("`TopBar`
and `ChatInput` use `position: fixed`... `ConversationThread` uses `padding-top` and
`padding-bottom` to clear both fixed zones") both already describe a container that's
supposed to stay fixed to the viewport with internal scrolling — the actual
implementation (a flexbox approach, not the fixed-positioning approach the frontend
spec describes) doesn't correctly achieve that intent due to the missing `min-h-0`.
Also confirms the frontend spec's own standing disclaimer (noted repeatedly in its
"Reviewed" log) that its documented implementation details have drifted from the real
code — worth reconciling as part of this fix, not just patching the CSS blind.

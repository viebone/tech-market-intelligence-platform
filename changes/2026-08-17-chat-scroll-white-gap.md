---
id: chat-scroll-white-gap
date: 2026-08-17
trigger-type: user-feedback
change-type: bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Fix Growing White Gap Below Chat

## Signal
See: `research/2026-08-17-chat-scroll-white-gap.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Directly affects the core chat experience this outcome depends on — a visibly broken
layout undermines "they spend less than 5 minutes to get a clear market read" by
actively degrading usability the longer a conversation runs.

## Change Type
`bug-fix` — the implemented layout doesn't achieve the fixed-viewport,
internally-scrolling intent already described (if imprecisely) by the frontend spec.
Root cause: `MarketHealthPage.tsx`'s flex layout chain is missing `min-h-0`, so the
scrollable conversation container grows to fit its content instead of scrolling
internally; combined with no background colour set on `<body>`, the browser's default
white shows through below the app once real page height exceeds the viewport.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | review — confirm the fixed-viewport/scrollable-middle *intent* is unaffected (it is; this bug doesn't change what the user is supposed to see, only fixes broken implementation of it) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — its CSS layout Tech Decision describes `position: fixed` for `TopBar`/`ChatInput` with padding-based clearing; the real implementation is a flexbox column layout instead. Same "spec describes stale implementation detail" pattern already flagged multiple times in this file's own Reviewed log (2026-08-09 entry) — correct it while fixing the bug, not leave it describing an approach that was never built. |
| Backend Spec | — | no-change — pure frontend CSS bug |
| Frontend Implementation | `frontend/src/pages/MarketHealthPage.tsx`, `ConversationThread.tsx`, `index.html`/global CSS | update — the actual fix |

## Execution Plan

- [x] Step 1: Reviewed `design/market-health/experience.md`'s Visual Design section in
      full. Confirmed no-change: "Top bar — fixed... Chat input — fixed, full width,
      pinned to the bottom" describes user-facing *behaviour* (both stay visible while
      the middle scrolls), not a specific CSS mechanism — identical either via
      `position: fixed` or a flexbox column with a properly-constrained scrollable
      middle. This bug fix doesn't change what the user is supposed to see, only
      corrects broken implementation of it.
- [x] Step 2: Updated `frontend/specs/market-health/architecture.md`'s CSS Tech
      Decision to describe the real flexbox layout instead of the never-built
      `position: fixed` approach, including the `min-h-0` requirement on every flex
      container between `h-screen` and the scrollable middle, and an explicit dark
      `<body>`/`html` background as defense in depth. `updated` bumped to 2026-08-17.
- [x] Step 3: `/implement-frontend` — added `min-h-0` to `MarketHealthPage.tsx`'s row
      (`flex flex-1 overflow-hidden` → `flex flex-1 min-h-0 overflow-hidden`) and
      centre-column (`flex flex-col flex-1 min-w-0 overflow-hidden` → adds `min-h-0`)
      divs — the two flex containers between `h-screen` and `ConversationThread`'s
      scrollable middle. Added an `@layer base` rule in `index.css` setting
      `html`/`body`/`#root` to `height: 100%` and the app's own `gray-900` background
      (`design/visual-design.md`'s page-background token) as defense in depth — the
      real fix is `min-h-0`, this is a backstop for if containment ever breaks again.
      Verified the production build compiles cleanly and the compiled CSS actually
      contains both `min-h-0{min-height:0px}` and the `#111827` background rule —
      not just that the source edit looks right.

## Decision Log
- 2026-08-17: Tracked against `understand-market-health-before-searching` — no new
  outcome needed, this is a defect in the existing chat experience, not new scope.
- 2026-08-17: Root cause diagnosed *before* triage (missing `min-h-0` in the flex
  chain + no `<body>` background) rather than triaging the raw symptom — the
  execution plan is scoped to the actual cause, not speculative layout changes.

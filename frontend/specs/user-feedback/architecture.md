---
id: user-feedback
experience: feedback
directive: low
status: ready
created: 2026-09-23
---

# User Feedback — Frontend Architecture Spec

## Experience this implements
See: `design/feedback/experience.md` (Feedback Panel) and
`design/market-health/data-stories.md` — "Feedback reaction" (Data Story thumbs).

## Component Breakdown

| Component | Responsibility | Location |
|---|---|---|
| `TaskPanel` (existing, extended) | Renders the new Footer row ("Give Feedback") below the existing task list; owns `isFeedbackPanelOpen` local state; renders `<FeedbackPanel>` via a portal when open. | `frontend/src/features/market-health/layout/TaskPanel.tsx` |
| `FeedbackPanel` | The overlay itself — backdrop, rating control, comment field, Submit, confirmation state. Self-contained: owns its own `rating`/`comment`/`phase` (`"form" \| "confirmed"`) local state, resets on each open. Portaled to `document.body` (escapes `TaskPanel`'s `overflow-y-auto` container — the same reason any fixed-position overlay in this codebase needs a portal rather than relying on CSS `position: fixed` inside a scrolling ancestor). | `frontend/src/features/feedback/FeedbackPanel.tsx` (new `features/feedback` folder — this capability isn't market-health-specific) |
| `RatingControl` | Presentational 1–5 button row + endpoint labels ("Not satisfied" / "Very satisfied"). Controlled: `value: number \| null`, `onChange`. No fetch logic — reused only inside `FeedbackPanel`, but kept as its own file since it's a real reusable visual unit, not a one-off. | `frontend/src/features/feedback/RatingControl.tsx` |
| `StoryFeedbackReaction` | The thumbs up/down control + inline comment reveal, rendered at the bottom of every Data Story. Takes `storyId: string`. Owns its own local state (`selected: "up" \| "down" \| null`, `showComment`, `comment`, `submitted`). | `frontend/src/features/feedback/StoryFeedbackReaction.tsx` |

**Existing component touched:** `DataStoryMessage.tsx` — the one place every Data Story already
routes through (`market-data-briefing` renders inline; `employment-risk-overview`,
`market-benchmark`, `beyond-tracked-roles` each delegate to their own component). Wrapping its
return value in a fragment that appends `<StoryFeedbackReaction storyId={story.story_id} />`
after whichever branch rendered is what makes the reaction generic across the whole catalogue
with a one-file change — matching this file's own "a thin router... as the catalogue grows"
precedent, and needing no change to any of the four individual story renderers or to any future
one added later.

## State Management

No new Zustand store. Every piece of state here is local to the component that owns it and
never needs to be read by a sibling or a distant ancestor — the same judgment call this
codebase already makes for `ConnectedAssistantCard`'s `confirming` state and
`MarketHealthPage`'s `activeTaskId`/`range`/`granularity`. Zustand in this app is reserved for
genuinely cross-cutting state (the session store, per `CLAUDE.md`); feedback UI state doesn't
qualify.

- `TaskPanel`: `isFeedbackPanelOpen: boolean`.
- `FeedbackPanel`: `rating: number | null`, `comment: string`, `phase: "form" | "submitting" |
  "confirmed" | "error"`. Reset to initial values every time it mounts (it unmounts on close,
  per the experience spec's "reopen ... opens fresh" rule — no need to manually reset on close).
- `StoryFeedbackReaction`: `selected: "up" | "down" | null`, `showCommentField: boolean`,
  `comment: string`, `commentSubmitted: boolean`. Lives for the lifetime of the Data Story
  message it's attached to — switching tasks unmounts it, which is fine per the experience
  spec's edge case (an in-flight capture completes in the background regardless — see Data
  Requirements, below, on not cancelling the fetch on unmount).

## Data Requirements

| Data | Source | When fetched |
|---|---|---|
| Submit platform rating | `POST /api/feedback/platform-rating` | On `FeedbackPanel` Submit click |
| Submit story reaction | `POST /api/feedback/story-reaction` | On thumbs up/down click |
| Submit story reaction comment | `POST /api/feedback/story-reaction` (a second, independent call — see Business Logic in the backend spec: reaction and comment are two separate captures) | On the inline comment field's Submit click, only reachable after a thumbs-down reaction has already been captured |

Neither surface reads any data on mount — there's nothing to fetch before rendering (unlike,
say, `ConnectedAssistantCard`, which reads the connections list). Both are pure write/mutation
flows.

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/feedback/platform-rating` | Submit a 1–5 rating + optional comment from the Feedback Panel. Body: `{ rating: number, comment?: string }`. |
| POST | `/api/feedback/story-reaction` | Submit a thumbs up/down (+ optional comment) for a Data Story. Body: `{ story_id: string, reaction: "up" \| "down", comment?: string }`. Called twice for a thumbs-down-then-comment flow — once with no `comment` at click time, once more with just the comment once the user submits it, per the backend spec's "two separate captures" rule. |

Both per `backend/specs/user-feedback/api.md` — anonymous, no `credentials: "include"` needed
(unlike `revokeConnection`, which sends the session cookie; these endpoints require no auth).

## Tech Decisions

- **Plain `fetch` + `useMutation`, no new HTTP client.** Matches `ConnectedAssistantCard`'s
  `revokeConnection` pattern exactly — a small `async function` per call, wrapped in
  `useMutation` from `@tanstack/react-query`. No `queryClient.invalidateQueries` call is needed
  on success for either mutation — nothing in this app's own UI reads feedback data back (it's
  admin-only, server-rendered separately), so there's no cache to invalidate.
- **`StoryFeedbackReaction`'s second (comment) request doesn't block or retry the first
  (reaction) request** — they're independent `useMutation` calls. If the comment POST fails,
  only the comment field shows a retry affordance (`design/market-health/data-stories.md`'s own
  edge case is silent on this — this is the natural mutation-per-action shape given the backend
  already treats them as separate captures).
- **`FeedbackPanel` portal target**: `document.body` via `createPortal` (React, already a
  dependency) — no new library. Backdrop `onClick` and `Escape` keydown both call the same
  close handler passed down from `TaskPanel`.
- **New `features/feedback/` folder**, not nested under `features/market-health/` — the
  platform-level Feedback Panel has nothing to do with market-health specifically (it's reachable
  from every Task), and `StoryFeedbackReaction`, while currently only used by market-health Data
  Stories, is written generically (`storyId: string`, no market-health-specific typing) so it
  isn't awkward to reuse if a future feature outside market-health ever grows its own
  story-like surface.
- **In-flight submissions are not cancelled on unmount** — per the experience spec's edge case
  ("navigates to a different Task before an in-flight capture finishes... still completes in the
  background"), `useMutation`'s default behaviour (the request isn't aborted just because the
  component unmounts) is correct as-is; no `AbortController` wiring needed.

## Out of scope

- No route change — the Feedback Panel is an overlay over the existing single-page app, not a
  new URL.
- No offline queueing or retry-on-reconnect for a failed submission beyond the inline "try
  again" affordance already specified in the experience specs.
- No analytics event wiring beyond what `design/feedback/experience.md`'s Evaluation Metrics
  table calls for — instrumentation choice (e.g. which analytics library) is not decided here,
  matching how the rest of this codebase's Evaluation Metrics tables don't prescribe a specific
  analytics implementation either.

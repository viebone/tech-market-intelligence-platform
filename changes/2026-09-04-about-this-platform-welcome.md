---
id: about-this-platform-welcome
date: 2026-09-04
trigger-type: stakeholder-request
change-type: ux-change, content-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Turn the first opening task into an "About this platform" welcome

## Signal

See: `research/2026-09-04-about-this-platform-welcome.md`

Related: `changes/2026-09-04-market-data-story-task-and-content.md` (created the briefing task
this sits above), `changes/2026-09-04-market-overview-default-task.md` (made that task the
default — now the welcome is the default instead).

## Outcome

`outcomes/understand-market-health-before-searching.md` — "they spend less than 5 minutes to
get a clear market read" and orienting a professional before they explore. The welcome makes
the first screen explain what the platform is, what data backs it, and what it can answer.
Confirmed with the stakeholder: existing outcome, no new one.

## Change Type

`ux-change` — a new opening surface and a Task Panel reorder.
`content-change` — new fixed welcome copy.
`api-change` — a new deterministic story (`about-this-platform`) in the market-health story
catalogue, supplying the welcome's live inventory figures and one headline fact.

## Decisions taken at refinement (2026-09-04)

- Task name: **"About this platform"**. It becomes the first task and the default selection on
  first load.
- The existing computed market briefing is **kept** as its own task, "What we know about the
  market", now the first (and currently only) entry in the story catalogue. Nothing removed.
- Live data in the welcome: **inventory figures + one headline fact** (e.g. the largest role
  group so far), not a full breakdown.
- No LLM. The welcome resolves entirely from owned-data aggregates, same as any story.
- **Revised for scale (second refinement pass, same day):** the welcome must not be written,
  or specced, around today's two specific examples ("About this platform" as intro,
  "What we know about the market" as the only story). The story catalogue is expected to grow;
  the welcome's "what you can ask" section is **generated from the live catalogue**
  (`design/market-health/data-stories.md`), not a fixed list of example questions. Selecting a
  catalogue shortcut in the welcome **opens that story's own task** (same as clicking it in the
  Task Panel) rather than sending a chat message — this scales to any number of stories with no
  new mechanism. The welcome itself is **not a catalogue entry**; it's a pinned index that reads
  the catalogue and always stays first/default regardless of catalogue size. This changes the
  `api-change`: no `about-this-platform` catalogue story; instead a dedicated welcome
  read (inventory + the current catalogue's questions) — see Steps 5, 7 below.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | update — Task Panel modelled as pinned welcome + growing story catalogue + pinned hiring-status (not an enumerated fixed list); "About this platform" first/default; new first-time-orientation pathway; correct the stale Entry Points → Default (still names the hiring-status task) |
| Visual Design | `design/visual-design.md` | no-change expected — welcome reuses the AI-message container and existing button style; confirm during the experience step |
| Experience Spec | `design/market-health/experience.md` | update — Opening Welcome section: purpose, fixed structure, catalogue-driven "what you can ask", data contract, honesty rules, edge cases; repoint "selected by default on first load"; framed generically so future catalogue growth needs no spec change |
| Data Stories Spec | `design/market-health/data-stories.md` | update — document the welcome as a pinned surface that reads the catalogue (not a catalogue entry itself); confirm the catalogue-addition process already supports this with no change |
| Backend Spec | `backend/specs/market-health/api.md` | update — new welcome read (platform inventory + current catalogue questions), separate from the story-execution endpoints; explicitly not a new catalogue entry |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — `WelcomeMessage` component rendering catalogue-driven shortcuts; Task Panel built from [pinned welcome] + [catalogue, fetched live] + [pinned hiring-status] instead of a hardcoded array, so a new backend story needs no frontend change |
| Frontend Implementation | `frontend/src/` | update — new `WelcomeMessage.tsx`; `TaskPanel.tsx` becomes catalogue-driven; `MarketHealthPage.tsx`, `ConversationThread.tsx` |
| Backend Implementation | `backend/src/market_stories.py` | update — new welcome builder (reuses existing inventory aggregates + `list_stories()`); no new `STORY_CATALOGUE` entry |

## Execution Plan

- [x] Step 1: `/new-experience` — updated `design/market-health/experience.md`: added an
      "Opening Welcome" section (structure, fixed + live copy, data contract, honesty rules,
      empty-data + empty-catalogue edge cases); repointed "default on first load" to the
      welcome; framed the story catalogue as open-ended (Task Panel = pinned welcome + growing
      catalogue + pinned hiring-status); "what you can ask" generated from the live catalogue,
      not hand-written examples; clicking a shortcut opens that story's own task. No new
      visual token/pattern needed — reuses the AI-message container and existing buttons.
- [x] Step 2: `/new-information-architecture` — added a "Task Panel structure" subsection
      (pinned welcome → story catalogue → pinned feature tasks); updated the current task
      table with a Panel-part column; added the first-time-orientation Key Pathway; corrected
      the stale Entry Points → Default entry (still named the hiring-status task); added
      Welcome / Data Story / Story Catalogue to the Content Taxonomy. Version 2.2 → 2.3.
- [x] Step 3: Updated `design/market-health/data-stories.md` — added "Relationship to the
      Welcome": the welcome is not a catalogue entry, reads the catalogue at request time via
      the same shape `list_stories()` returns, and needs no change when a story is added.
- [x] Step 4: `/new-visual-design` — skipped. No new token or pattern; welcome reuses the
      AI-message container and existing buttons.
- [x] Step 5: `/new-backend-spec` — added `GET /api/market-health/welcome` (inventory +
      `story_shortcuts`) to `backend/specs/market-health/api.md`, distinct from story
      execution; added `display_name` to the story-catalogue contract (`data-stories.md` and
      `GET /api/market-health/stories`) so the Task Panel needs no per-story frontend copy.
- [x] Step 6: `/new-frontend-spec` — added `TaskPanel` (now catalogue-driven) and
      `WelcomeMessage` to the component table, a "Welcome rendering rules" section, task
      selection + story-catalogue state, and the welcome/stories endpoints to the Data
      Requirements and API Contract tables in
      `frontend/specs/market-health/architecture.md`.
- [x] Step 7: `/implement-backend` — added `display_name` to `STORY_CATALOGUE`; added
      `build_welcome()` to `backend/src/market_stories.py` (reuses `PLOTTED_ROLE_CATEGORIES`
      from `market_openings` + `STORY_CATALOGUE`, no new catalogue entry); added
      `GET /api/market-health/welcome` in `backend/src/market_health.py`.
- [x] Step 8: `/implement-frontend` — `TaskPanel.tsx` rebuilt catalogue-driven (pinned welcome
      + `stories` prop + pinned hiring-status, no hardcoded task array); new
      `WelcomeMessage.tsx`; `ConversationThread.tsx` gained a welcome branch and a
      catalogue-derived `selectedStoryId` (no longer hardcoded to one story id);
      `MarketHealthPage.tsx` fetches the story catalogue once, fetches the welcome when
      active, derives `selectedStoryId` from the fetched catalogue, and defaults
      `activeTaskId` to the welcome.
- [x] Step 9: Validated — `GET /api/market-health/welcome` and `GET /api/market-health/stories`
      run against production data through a live uvicorn stack (postings 6,628, companies 27,
      collection start 2026-08-03, headline Engineer 2,833, one shortcut for
      "What we know about the market"); verified through the running `:5173` dev proxy;
      `npm run build` / `tsc` pass; `git diff --check` clean.

## Decision Log

- 2026-09-04: Kept against `understand-market-health-before-searching` rather than opening an
  onboarding outcome — the stakeholder confirmed the existing outcome covers "quick
  orientation before exploring".
- 2026-09-04: "Keep both" — the computed briefing stays as its own task. Task Panel order:
  About this platform (pinned) → the story catalogue (starts with "What we know about the
  market", grows over time) → Tech market hiring status (pinned).
- 2026-09-04 (revised after user feedback — account for scale): the welcome is **not** a
  catalogue entry. Initially it was modelled as a second `STORY_CATALOGUE` entry
  (`about-this-platform`) with fixed example questions in its copy. That doesn't scale: every
  future story would need the welcome's copy hand-edited to mention it. Redesigned so the
  welcome reads the catalogue at request time (reusing `list_stories()`) and renders one
  shortcut per current entry; adding a story is purely a `data-stories.md` + backend catalogue
  change, with zero experience-spec or welcome-copy change required.

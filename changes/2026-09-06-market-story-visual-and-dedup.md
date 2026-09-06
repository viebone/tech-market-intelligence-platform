---
id: market-story-visual-and-dedup
date: 2026-09-06
trigger-type: stakeholder-request
change-type: ux-change, visual-change, content-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Make "What we know about the market" visual, and stop it repeating the welcome

## Signal

See: `research/2026-09-06-market-story-visual-and-dedup.md`

Related: `changes/2026-09-04-market-data-story-task-and-content.md` (created the story),
`changes/2026-09-04-welcome-visual-data-points.md` (made the welcome visual — the source of
the overlap).

## Outcome

`outcomes/understand-market-health-before-searching.md` — "they can identify which roles and
skills are in demand vs. declining" and "spend less than 5 minutes to get a clear market
read". The story is where a professional sees the *substance* — which roles, which skills,
what pay looks like — so it needs to actually show that, at a glance.

## Change Type

- `content-change` — the story stops recapping the platform inventory (jobs/companies/since/
  largest role — all on the welcome now) and instead presents the market's shape.
- `visual-change` — prose lists become ranked horizontal bar charts (a new "Ranked bar list"
  aesthetic, one muted hue, value labels — the magnitude form from the `dataviz` method).
- `ux-change` — the story's structure changes; no new task, no new zone.

## The redesign

The **welcome** answers "what is this and what data backs it" (inventory). The **story**
answers "what does the data say about the market right now" (substance). No fact appears in
both.

Story blocks, all chart-first, from data the backend already returns:

1. **Framing line** — one sentence, e.g. "What ~2,900 tracked Engineer, Product, and Design
   postings are hiring for" (numbers as context, not as the headline).
2. **The roles being hired** — top job titles, ranked horizontal bars (`roles-offered.top_titles`).
   Genuinely new — the welcome only shows 3 category buckets.
3. **What employers ask for** — top skill groups, ranked bars, must-have emphasised
   (`employer-mentioned-skills.skills`).
4. **Pay transparency** — a single figure + bar: "~6% of postings state a salary"
   (`compensation-coverage.coverage_by_confidence`). An honest, useful market signal.
5. **Where the roles are** — top locations, ranked bars, with the "only N have a normalised
   location" caveat (`geographic-coverage`).
6. (optional, low priority) sources — one line naming the job boards.

Each block keeps its honesty qualifier (sample size / coverage caveat) and the whole thing
stays a no-model data story with the Reasoning Panel provenance.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — same task, same zone |
| Visual Design | `design/visual-design.md` | update — add a "Ranked bar list" component aesthetic |
| Experience Spec | `design/market-health/experience.md` | update — the story is chart-first and de-duplicated from the welcome |
| Data Stories Spec | `design/market-health/data-stories.md` | update — Story 1 "Visible answer shape" rewritten (visual blocks, no inventory recap) |
| Backend Spec | `backend/specs/market-health/api.md` | review — the existing story contract already returns everything; note only |
| Backend Implementation | `backend/src/market_stories.py` | update only if a derived field (e.g. salary-disclosure %) is cleaner computed server-side |
| Frontend Implementation | `frontend/src/features/market-health/DataStoryMessage.tsx` | rewrite |

## Execution Plan

- [x] Step 1: `/new-visual-design` — "Ranked bar list" aesthetic. `design/visual-design.md`
      v1.3 — added the component after "Shortcut Card".
- [x] Step 2: `/new-experience` — the story is chart-first, and every fact is one the welcome
      does not show. `design/market-health/experience.md` (Data stories note) and
      `design/market-health/data-stories.md` (Story 1 "Visible answer shape" rewritten).
- [x] Step 3: `/new-frontend-spec` — `frontend/specs/market-health/architecture.md` —
      "First story: market data briefing" rewritten; `RankedBarList` documented.
- [x] Step 4: `/implement-backend` — no-op. `POST /api/market-health/stories/market-data-briefing`
      already returns every section the redesign needs (`top_specializations`,
      `employer-mentioned-skills.skills`, `compensation-coverage.coverage_by_confidence`,
      `geographic-coverage.cities`). The pay-disclosure % is a one-line client-side ratio —
      not worth a server field.
- [x] Step 5: `/implement-frontend` — new `frontend/src/features/market-health/RankedBarList.tsx`
      (generic `{label, value, emphasis?}[]`); `DataStoryMessage.tsx` rewritten chart-first
      (framing line → roles being hired → what employers ask for → pay transparency → where
      the roles are). No inventory recap. Roles block uses `top_specializations` (the
      meaningful "role"), not the fragmented `top_titles` — noted as a `directive: low`
      judgement call within the spec's intent.
- [x] Step 6: Validate — `npx tsc --noEmit` clean, `vite build` clean (165 modules).
- [x] Step 7: Commit + push.

## Decision Log

- 2026-09-06: Split of responsibility — welcome = inventory ("what/how much data"), story =
  substance ("what the data shows"). The overlap came from the welcome getting visual
  figures (`welcome-visual-data-points`) that the story already had in prose; the fix is to
  move the story *past* the inventory, not to dial the welcome back.
- 2026-09-06: Ranked horizontal bars, one muted hue (magnitude comparison, `dataviz`
  choosing-a-form) — not the welcome's Category Share Bar (that is part-to-whole, a different
  form for a different job).

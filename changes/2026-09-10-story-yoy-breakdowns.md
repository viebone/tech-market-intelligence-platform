---
id: story-yoy-breakdowns
date: 2026-09-10
trigger-type: stakeholder-request
change-type: ux-change, api-change
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Year-on-year market breakdowns in "What we know about the market"

## Signal

See: `research/2026-09-10-story-yoy-breakdowns.md`. Add consumer-facing breakdowns — role
category, seniority (level), track, top specializations — to the `market-data-briefing`
story, each with a plain explanation and a clearly stated time frame, presented **year on
year** (current 12 months vs the 12 months a year earlier; no further back). Data isn't there
yet; the spec anticipates it.

## Outcome

`outcomes/understand-market-health-before-searching.md` — two of its success criteria are
delivered more directly by this: "identify which roles and skills are in demand **vs.
declining**" (a proportion that's shifting is exactly "in demand vs declining") and "see the
trends clearly, how the hiring market numbers **evolve through time**". No new criterion — the
existing ones move from "eventually, via the trend chart" to "in the story, per breakdown".

## Change Type

- `ux-change` — the story gains new blocks, a year-on-year comparison presentation, and a
  short "what this means" line per block. The de-dup rule vs. the welcome is reframed.
- `api-change` — new `market-data-briefing` sections; new backend aggregates (the admin's
  `classification_distribution` windowed to two 12-month periods + the delta between them);
  an explicit "insufficient history" state that is the **default at ship time**.

## The resolution: snapshot vs. trend

The 2026-09-06 rule ("welcome carries inventory, story carries substance"; the story does not
repeat the role-category split) is **refined, not reversed**:

- **The welcome shows the *current* proportions** — a snapshot of what the tracked data looks
  like right now (`WelcomeMessage`'s Category Share Bar, unchanged).
- **The story shows how those proportions are *shifting* year on year** — the trend, not the
  snapshot.

The same dimension (role category) can appear in both because they encode different things:
current state vs. change over time. The 2026-09-10 checklist item "no block renders the
role-category split" becomes "no block renders the *current* role-category split — a
year-on-year *shift* in it is the story's job."

## The breakdowns

Each is a proportion over classified postings, computed for two windows and compared:

| Block | Dimension | Source values |
|---|---|---|
| How the role mix is shifting | `role_category` | Designer / Product Manager / Engineer (+ `other` shown as context, never as a tracked trend) |
| How seniority is shifting | `level` | the `LEVEL_LADDER` from `design/market-health/job-classification.md` |
| IC vs. management | `track` | `ic` / `management` (`unknown` excluded) |
| Which specializations are rising and falling | `specialization` | top 10 by current-window volume, each with its year-on-year change |

All four reuse the aggregate the admin overview already computes
(`classification.get_classification_distribution()`), extended with a date window.

**Rules (per breakdown):**
- **Two windows, stated explicitly**: the trailing 12 months, and the 12 months ending one
  year before that. Every block shows both date ranges in words (e.g. "Sep 2026 – Sep 2027,
  compared with Sep 2025 – Sep 2026"). One year back, never more.
- **A plain "what this means" sentence** — e.g. "A rising management share means more of the
  new roles are for people who lead teams rather than do the work directly."
- **Proportions, never raw counts as the point**; each proportion carries its denominator and
  the sample size.
- **Insufficient history** (the state at ship time, until ~2027-08): the block shows only the
  current window's proportion and says plainly that a year-on-year comparison isn't available
  yet — "we've been tracking since 3 Aug 2026; the first year-on-year comparison is possible
  from Aug 2027." Never a fabricated prior-year figure, never a zero.
- **`other`** is shown as context where it helps read the tracked shares, but its own trend is
  never presented as a market signal (it's a sourcing artefact — see
  `changes/2026-09-06-market-story-visual-and-dedup.md` decision log).

## Where these blocks sit / the specialization overlap

The story already has **"The roles being hired"** — top ~7 specializations, current window
(`roles-offered.top_specializations`). That block stays as the current-state read; the new
**"Which specializations are rising and falling"** is the year-on-year view. To avoid two
near-identical specialization blocks, the current block may be trimmed or merged — decided in
the experience/data-stories spec work, not here.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | review — no-change (criteria already cover it; note only) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — `role_category` / `level` / `track` / `specialization` are all existing taxonomy (`design/market-health/job-classification.md`) |
| Visual Design | `design/visual-design.md` | **update** — add a **"Year-on-year comparison"** form to the Data Story composition vocabulary (how a proportion's shift between two windows is drawn — e.g. paired share bars with a delta call-out; and its "no prior window" state) |
| Experience Spec | `design/market-health/experience.md` | **update** — Data stories: the snapshot-vs-trend split; the story now carries year-on-year breakdowns |
| Data Stories Spec | `design/market-health/data-stories.md` | **update** — Story 1 "Visible answer shape" gains the four blocks; de-dup rule reframed; data contract gains the windowed aggregates + the two-window rule + the insufficient-history `no_data_state`; the visual-standard checklist item on inventory duplication reworded |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — the new blocks, a year-on-year comparison component, the "not enough history yet" state |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — `market-data-briefing` new sections; windowed `classification_distribution` + YoY delta; honesty rules (both windows stated, never blended, insufficient-history behaviour); reuse of the admin aggregate |
| Frontend Implementation | `frontend/src/` | update — `DataStoryMessage.tsx` new blocks + the comparison component |
| Backend Implementation | `backend/src/` | update — `market_stories.py` new sections; a date-windowed distribution helper (extend `classification.get_classification_distribution`) |

## Execution Plan

- [x] Step 1: Read the chain (2026-09-10) — experience.md Data stories, data-stories.md
      (Story 1 + checklist), visual-design.md Data Story composition, backend api.md Data
      stories, frontend architecture.md Data stories, `market_stories.build_market_data_briefing()`
      (`_section()` shape: `{id,title,status,content,qualifier,message?}`),
      `classification.get_classification_distribution()` (one `GROUP BY` per dimension over
      `classifications`, `DISTRIBUTION_DIMENSIONS = role_category/level/track/specialization/
      classification_confidence`, NULLs excluded), `LEVEL_LADDER`, `TRACKS = {ic, management}`.
      Design note: the YoY sections need a **third state** — `status: "ready"` but
      `content.comparison_available: false` — so the current window still renders while the
      prior-year window is absent (`insufficient_data` would blank the whole block).
- [x] Step 2: `outcomes/understand-market-health-before-searching.md` — reviewed,
      **no-change**. Its "identify which roles and skills are in demand vs. declining" and
      "see the trends clearly, how the hiring market numbers evolve through time" already
      cover this; the change delivers them more directly, it doesn't add a criterion.
- [x] Step 3: `/new-visual-design` (2026-09-10) — `design/visual-design.md` → v1.5. Added
      **"Year-on-year comparison"** to the Data Story composition vocabulary: two 12-month
      windows only; per-row shared track with a `gray-700` prior-year ghost behind an
      `indigo-500` current fill (the visible gap = the change); a `▲/▼/– +N pp` delta column
      where glyph+sign carry direction, not colour; both date ranges stated in words under
      the heading; a required "what this means" sentence; and the **"No prior window yet"**
      state — current window only + a muted "comparison starts {Month Year}" line, reading as
      "coming soon", not "broken".
- [x] Step 4: `/new-experience` (2026-09-10) —
      - `design/market-health/experience.md` — Data stories: the story divides from the
        welcome by **time, not topic** (welcome = snapshot, story = substance + YoY shift);
        two-movements structure; the two-window / "coming soon" rule; two "Revised
        2026-09-10" notes.
      - `design/market-health/data-stories.md` — checklist reworded (blocks → movements for a
        both-themes story, ~8 allowed; "no *current-snapshot* duplication" replaces "no
        inventory duplication"; a year-on-year checklist item). Story 1 "Visible answer
        shape" restructured into **Movement 1 (the market right now)** = framing + roles
        (top 10, delta column dormant) + skills + pay + locations, and **Movement 2 (how it's
        shifting)** = role mix / seniority / IC-vs-management, each a Year-on-year comparison,
        all in the "no prior window yet" state at launch. Specialization overlap resolved by
        **merging** — one "roles being hired" block, top 10, gains the delta column later.
        Data contract: two new rows (windowed distribution keyed on `fetched_at`; YoY
        availability from `min(fetched_at)`). Honesty & empty states: the "no prior window"
        state is distinct from "not enough data"; never estimate/zero-fill the prior year;
        `other`'s own YoY trend is never a signal.
      - `design/visual-design.md` — Reference implementation line + rules-out reworded for
        the two movements and snapshot-vs-shift.
- [ ] Step 5: `/new-backend-spec` — `backend/specs/market-health/api.md`: the new
      `market-data-briefing` sections and their `content` shape (current + prior window +
      delta, or an `insufficient_history` flag); the windowed distribution aggregate and its
      reuse of the admin helper; the honesty rules.
- [ ] Step 6: `/new-frontend-spec` — `frontend/specs/market-health/architecture.md`: the new
      `StoryBlock`s, the year-on-year comparison component, the "not enough history" render,
      and how the frontend reads the new section shape.
- [ ] Step 7: `/implement-backend` — `market_stories.py` new sections; the date-windowed
      distribution helper. Verify the story endpoint returns the new sections in the
      `insufficient_history` state against production (which has <1yr of data).
- [ ] Step 8: `/implement-frontend` — `DataStoryMessage.tsx` new blocks + the comparison
      component + the insufficient-history render. `npm run build` + `tsc`; eyeball.
- [ ] Step 9: Commit + push; mark `complete` when specs and the shipped story match (in its
      insufficient-history state — the year-on-year path can't be exercised until ~2027-08).

## Decision Log

- 2026-09-10: Tracked against `understand-market-health-before-searching` — same outcome as
  every prior story change. No success criterion moves; "in demand vs declining" and "evolve
  through time" are simply delivered more directly.
- 2026-09-10: `ux-change` + `api-change`, not `new-feature` — the story exists; this adds
  content and a comparison presentation to it, plus the aggregates behind them.
- 2026-09-10: **De-dup rule refined to snapshot vs. trend, not reversed.** Welcome = current
  proportions; story = year-on-year shift. Same dimension, different encoding.
- 2026-09-10: **One year back, exactly two 12-month windows.** Not multi-year, not a rolling
  sparkline — a single before/after per breakdown, per the stakeholder ("one year back nor
  more").
- 2026-09-10: **Insufficient-history is the default state at ship time** and must be a
  first-class, honestly-worded render — not an error, not hidden. The year-on-year path is
  specced now and lies dormant until the data supports it (~2027-08).
- 2026-09-10: Reuse `classification.get_classification_distribution()` (already built for the
  admin overview) with a date window rather than new bespoke SQL — same aggregate, consumer
  framing.

---
id: role-category-display-relabel
date: 2026-09-22
trigger-type: user-feedback
change-type: visual-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Relabel Role Category for display — "Design" / "Product Management" / "Engineering"

## Signal
User: "would it be renaming the to Design; Product Management; Engineering?" — following the
discussion of Story 4's real 51.3% "outside the 3 tracked categories" figure, which prompted
reconsidering whether "Designer/Product Manager/Engineer" still reads right now that
specialization sets under each cover far more than individual-contributor job titles (VPs,
Directors, Heads of, Managers all sit under these 3 via `track`). User confirmed: "ok go cheap
for now" — the display-only option, not a stored-value rename.

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — improves how the tracked 3
categories read to a professional, no new success criterion needed.

## Change Type
`visual-change` (product-wide) — display text only. **Not** a `technical-refactor` or
`api-change`: `classifications.role_category`'s stored values, `ROLE_CATEGORIES`, the trend
chart's data keys, and every filter/query parameter across the whole system are unchanged. This
is presentation only, per the two options laid out and the user's explicit choice of the cheap
one.

## Triage Notes

The internal "occupation family" reasoning for this exact relabel already existed in
`job-classification.md`, unused until now: *"'Product Manager' becomes an awkward parent
category for 'VP Product,' while 'Product' (the family) doesn't have that problem."* This
change promotes that existing internal reasoning to the actual displayed label, closing a gap
between "how the taxonomy already thinks about itself" and "what a user sees" — not inventing a
new naming decision from scratch.

**Where this was and wasn't applied — a deliberate boundary, not a partial job:**
- **Applied**: every place the 3 category names render as headline/story copy a user reads —
  the trend chart legend (`JobOpeningsChart.tsx`, already had a clean label/key seam), the
  Welcome's Category Share Bar (`WelcomeMessage.tsx`, added a label map since none existed),
  Story 1's role-mix-shift YoY block (`YearOnYearBars` is generic across 3 dimensions, so the
  relabel is applied only at the role-category call site in `DataStoryMessage.tsx`, never at
  the seniority/track call sites), Story 4's own framing copy (both frontend and backend, plus
  a pre-existing Story 1 "meaning" string that had the same abbreviation issue, unrelated to
  this session's earlier work), and `get_taxonomy`'s MCP labels (the one-line edit its own
  module docstring anticipated).
- **Deliberately NOT applied**: the Reasoning Panel's technical trace text
  (`MarketHealthPage.tsx`) and the chat opening prompt (`MarketBriefingMessage.tsx`'s
  `OPENING_PROMPT`) — both describe what was actually queried/filtered by, using the real
  stored values, which is the more honest choice for a technical provenance surface, not an
  oversight. Same reasoning for `get_job_function_breakdown`'s and other MCP tools' own
  docstrings, which correctly tell a calling AI the literal values it must use to filter —
  a display label there would actively mislead a machine caller.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Information Architecture | `design/information-architecture.md` | update — one-line clarifying note on the Role Category taxonomy entry; the term and its 3 values are unchanged |
| Visual Design | `design/visual-design.md` | no-change — the accent-colour system is still keyed by the same 3 stored values; no new colour, no structural change |
| Experience Spec | `design/market-health/data-stories.md` | update — Story 1's/Story 4's copy corrected to match |
| Backend Implementation | `backend/src/market_stories.py` | update — Story 4 catalogue/copy, Story 1's YoY "meaning" string |
| Backend Implementation | `backend/src/mcp_access/taxonomy.py` | update — `_ROLE_CATEGORY_LABELS` |
| Frontend Implementation | `JobOpeningsChart.tsx`, `WelcomeMessage.tsx`, `DataStoryMessage.tsx`, `JobFunctionStoryMessage.tsx` | update — display-label seams added/used at every consumer-facing render site |
| Everything else (IA structure, stored data, `ROLE_CATEGORIES`, every query/filter parameter) | — | no-change — deliberately, this is the whole point of choosing the cheap option |

## Execution Plan

- [x] Step 1: Confirmed the cheap/expensive distinction with the user before building anything; user chose cheap
- [x] Step 2: Found every literal-string consumer-facing occurrence (`Designer`/`Product Manager`/`Engineer` display text) via a real grep across the frontend — only 2 files, both checked
- [x] Step 3: `JobOpeningsChart.tsx` — updated the 3 `label` values in its existing `SERIES` array (already had a clean key/label seam)
- [x] Step 4: `WelcomeMessage.tsx` — added a `ROLE_CATEGORY_LABEL` map + `roleCategoryLabel()` helper (no seam existed before); applied at all 3 display sites (aria-label, tooltip title, visible span), leaving `row.role_category` untouched for keys/color lookups
- [x] Step 5: `YearOnYearBars` confirmed generic (reused for role_category/level/track) — relabeled only at the role-mix-shift call site in `DataStoryMessage.tsx`, added a `relabelRoleCategoryRows()` helper rather than touching the shared component
- [x] Step 6: Found and fixed a real, pre-existing inconsistency while here: `JobFunctionStoryMessage.tsx`'s and `market_stories.py`'s own Story 4 copy said "Design, Product, and Engineering" — dropping "Management" entirely, a different and wrong phrase, not just an old label. Also found the same issue in Story 1's own pre-existing "meaning" string (predates this session's work). All corrected to "Design, Product Management, and Engineering" consistently.
- [x] Step 7: `mcp_access/taxonomy.py` — the one-line label-dict edit its own docstring anticipated
- [x] Step 8: Deliberately left the Reasoning Panel trace and chat opening prompt on the real stored values — technical/provenance text should say what was actually queried, and an AI-facing tool docstring must use the literal filterable value, never a display label
- [x] Step 9: Verified end-to-end with real data: `get_taxonomy()` returns `{"value": "Designer", "label": "Design"}` etc. (value unchanged, label changed); Story 4's question text reads "What roles exist beyond Design, Product Management, and Engineering?"; `tsc --noEmit` and `npm run build` both clean

## Decision Log
- 2026-09-22: Chose the display-only relabel over a stored-value rename — the internal
  "occupation family" reasoning already existed in `job-classification.md`; this only needed
  promoting to what's shown, not a real data migration.
- 2026-09-22: Deliberately did not relabel technical/AI-facing surfaces (Reasoning Panel trace,
  chat opening prompt, MCP tool docstrings) that must state the literal queryable value — a
  display label there would be actively wrong, not just inconsistent.

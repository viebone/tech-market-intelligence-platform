source: stakeholder-request
date: 2026-09-04

The first opening task ("What we know about the market") should become a **welcome message**
rather than a computed market briefing. Its job is to orient a first-time visitor:

1. What this platform is — what it does and why it exists.
2. What data we have right now — a live inventory: how many job openings, how many companies,
   since when, which role areas, which signals (skills, pay, location). Plus one plain
   headline fact drawn from the data.
3. What questions can be answered — a few example questions the user can click to jump
   straight into the hiring-status conversation with that question asked. Plus a short note
   on what is out of scope.

## Decisions taken during refinement (2026-09-04)

- **Task name**: "About this platform" (replaces "What we know about the market" as the
  first, default-selected task).
- **Data depth**: inventory figures plus one headline fact (e.g. the largest role group so
  far). Not a full breakdown.
- **The market briefing stays**: the existing computed briefing keeps its own task, "What we
  know about the market", now second in the Task Panel. Nothing is removed — the welcome is
  added above it.
- **Outcome**: tracked against `understand-market-health-before-searching`. Orienting a
  professional quickly before they explore is already in that outcome's success criteria.
- **Example questions** (open at refinement, recommended): clicking one switches to the
  hiring-status task and sends the question, rather than only pre-filling the input.

## Draft copy (to be finalised in the experience spec)

**What this is** (fixed)
> Read the tech hiring market before you make a move. This platform gathers job openings from
> company career pages, sorts them by role, and tracks the skills, pay, and locations
> employers are asking for — so you can see where demand is heading instead of guessing.

**What we have right now** (live)
> We're currently following ~N job openings from ~M companies, gathered since {month year},
> across three role areas — Designer, Product Manager, and Engineer. {One headline fact.}
> For most of these we also have the skills employers mention, and pay figures where shared.
> This is a growing sample of the market, not every job out there.

**What you can ask** (clickable)
> Open "Tech market hiring status" for the demand trend, or ask something like:
> - Is hiring going up or down for designers right now?
> - Which skills come up most in product manager roles?
> - What pay range are senior engineering roles showing in London?
> We don't cover layoffs, company reviews, or application tracking.

Related: `changes/2026-09-04-market-data-story-task-and-content.md`,
`changes/2026-09-04-market-overview-default-task.md`,
`research/2026-09-04-market-data-stories.md`.

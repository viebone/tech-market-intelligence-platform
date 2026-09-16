---
id: codebase-stays-navigable-as-it-grows
source: business
priority: medium
status: active
created: 2026-09-16
---

# Outcome: Anyone working in this codebase can find and understand any component without already knowing where it lives

## Signal
See: `research/2026-09-16-frontend-organization.md`

> "I would like to keep things well organised, starting from the front-end, I would like to
> keep the stories well organised and separated from the main structure of the page or from the
> new mcp functionality and from the login functionality."

The concrete trigger: `frontend/src/features/market-health/` had grown to 30 files in one flat
folder, mixing three genuinely different concerns — page chrome present on every task, the
data-story catalogue, and one specific pinned chart feature — with no structure distinguishing
them. Separately, and unnoticed until traced by hand, 11 of those 30 files were dead code:
imported by nothing reachable from the real app, left behind across past changes with nothing in
the process that would have caught it.

## Context
This is the same underlying concern as `outcomes/bring-your-own-ai-agent-access.md`'s sibling
work from the same day — the user described "losing control of everything that is happening" as
the product grew. That first surfaced as *"I can no longer tell what this product does without
re-reading specs and code"* and was addressed with `OVERVIEW.md` plus a framework-wide rule
requiring it to stay current. This is the other half of the same feeling, aimed at the codebase
itself: as features accumulate, a folder that made sense when it held five files stops making
sense at thirty, and nothing about writing new code naturally prompts anyone to notice or fix
that — new files just keep landing in whatever folder already exists, and dead files just keep
not getting deleted, because no single change ever looks big enough on its own to justify a
pause and a cleanup.

Two new feature areas landed today specifically organized well from the start
(`frontend/src/features/mcp-access/`, `frontend/src/features/account/`) — proof this is
achievable, not a hypothetical ideal. The gap is entirely in what was never reorganized after it
grew.

If ignored: every new feature has a rising chance of landing in the wrong place (or a new flat
folder of its own), dead code keeps accumulating invisibly, and the confidence to change
anything drops as "where does this belong, and is it even still used" becomes a real question
before every edit — the exact opposite of staying in control of a growing product.

## Success looks like
- A new file's correct folder is obvious from what the file *does*, without asking or guessing —
  page structure, a feature's own UI, and story/content rendering are never mixed in one folder
- A component that's no longer reachable from the running app doesn't linger indefinitely — dead
  code is something the process catches and removes, not something a manual audit has to
  rediscover by tracing every import by hand
- Two unrelated capabilities (e.g. an existing feature and a newly added one) never share a
  folder just because they happened to ship around the same time
- Reorganizing a folder that's grown unclear is a normal, expected `technical-refactor` change —
  not a special, rare event that only happens when someone happens to notice and ask
- A frontend spec's own component-location table stays accurate — a reader can find a component
  at the path the spec says it's at, without it having quietly moved

## Out of scope
- A rigid, one-size-fits-all folder convention imposed on every future feature regardless of its
  actual shape — the right structure is decided per feature (as `mcp-access`/`account` already
  were), not templated mechanically
- Backend code organization — this outcome is scoped to what today's signal actually surfaced
  (the frontend); a backend equivalent is a separate future signal if one arises
- Automated dead-code detection tooling (a lint rule, a CI check) — this outcome is about the
  standard staying enforced through the change-request process and periodic attention, not about
  building new tooling; worth revisiting if manual tracing ever proves insufficient
- Retroactively auditing every other feature folder in one pass right now — addressed as each
  area is next touched or reorganized, matching this product's existing "fix it when you're
  there, not in one big sweep" pattern (e.g. dead-code findings during the 2026-08-11
  classification-taxonomy review)

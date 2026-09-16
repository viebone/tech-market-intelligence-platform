source: stakeholder-request
date: 2026-09-16

> "ok lets keep this somehow for the future in a way that if tomorrow we start making money we
> can switch off all the information that is coming from those sources which we don't have
> comercial license"

## Reading of the ask

A real, enforced mechanism — not a note in a doc — so that the day this product actually starts
charging for anything, every data source without a *confirmed* right to commercial use stops
being used automatically, without anyone having to remember to go source-by-source. One switch,
flipped once.

## What this doesn't (yet) need to solve

Nothing today reads `market_observations`/`skill_associations` back out anywhere (still
ingestion-only, per `backend/specs/scraped-data-sources/api.md`'s "What this doesn't decide") —
so there's no display/query surface to gate yet. The switch is built where it can actually bite
today (ingestion) and specified as a forward-binding requirement for whichever future change
builds a query/display surface over this data.

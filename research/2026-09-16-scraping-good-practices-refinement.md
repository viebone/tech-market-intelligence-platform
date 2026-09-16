source: stakeholder-request
date: 2026-09-16

Related: `research/2026-09-16-itjobswatch-scraping-permission.md`,
`research/2026-09-16-itjobswatch-data-model-analysis.md`, `changes/2026-09-16-polite-scraping-adapters.md`
(the change this refines — reopened rather than forked into a new file, since it's the same
feature, same day, still actively being shaped).

## What was asked, verbatim

> "it has to run once a week, it should not overwhelm the server, it should focus only on new
> things and not old things and we should alwasys apply the right cc licensing, in this case and
> always we should provide a way to name the sources aligned with the cc license of each source.
> for this we could apply the thinking process plus we should have a principle and a skill that
> ensure always good practices"

## Reading of the ask

Four concrete requirements on the already-implemented `scraped-data-sources` feature:
1. **Weekly cadence, enforced, not just documented** — the codebase's existing discipline
   (PoliteScraper's pacing is enforced in code, not a comment) should extend to run frequency
   too, not just per-request pacing.
2. **"Focus on new things, not old"** — avoid redundant work/storage for data that hasn't
   actually changed since the last run.
3. **Correct, source-specific CC licensing, always** — not a per-adapter placeholder string, but
   a real, explicit, source-keyed record of which licence variant applies and how to attribute
   it, since "Creative Commons" alone is not a citable licence.
4. **Generalized beyond this one feature** — a documented principle plus a framework-level skill
   that checks this for any current or future scraped source, mirroring the pattern already
   built this session for MCP-exposure decisions (`mcp-access-review`) and data legibility
   (`data-legibility`).

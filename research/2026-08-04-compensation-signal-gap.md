source: internal
date: 2026-08-04

`outcomes/understand-market-health-before-searching.md`'s "Success looks like" section has
stated, since 2026-06-10: "They can set a realistic salary target before applying to
anything." `design/information-architecture.md`'s Content Taxonomy has, since at least
2026-06-21, a defined term for exactly this: "**Compensation Signal** — A data point
representing salary range trend for a given role, seniority, or location," explicitly
marked "Future tasks" (alongside "Layoff Signal," while "Demand Signal" — the existing
trend chart — is marked as already shipped). Nothing in `design/market-health/experience.md`,
`backend/specs/market-health/api.md`, or the actual implementation currently surfaces
compensation data anywhere. This is a long-anticipated, already-named gap between promise
and delivery, not new scope being invented.

Investigated what's actually feasible by querying the real production database directly
(not assumed from API docs):

- **Ashby**: 62% of postings (975/1,581) already carry structured compensation data in
  `raw_response.compensation.compensationTiers[]` — real `minValue`/`maxValue`/
  `currencyCode`/`compensationType`, frequently pre-tiered by region (e.g. "US Tier 1 - SF
  & NYC Metros" vs "Canada"), plus a ready-made summary string
  (`compensationTierSummary`). Zero extraction needed — read the field.
- **Lever**: 76% of postings (230/302) mention salary, but only as free text inside an
  `additional`/`additionalPlain` field (e.g. "The estimated salary range for this position
  is estimated to be $93,000 - $160,000/year"). Fairly consistent phrasing — regex-first
  extraction, LLM fallback for anything regex can't parse.
- **Greenhouse**: 59% of postings (1,600/2,710) mention salary/compensation, but buried
  inside one large unstructured HTML `content` blob alongside the full job description —
  noisiest, least reliable source of the three for this specifically.
- None of this is stored anywhere queryable today. `raw_postings.raw_response` is JSONB
  with the raw data sitting in it unused; `classifications` has no salary field at all.

Explicitly out of scope for this change, agreed with the user during discussion:
- **Skills-in-demand / "must-haves" extraction** — also named in the same outcome, but
  needs per-posting (not per-title) LLM extraction, a fundamentally larger and
  differently-shaped cost problem than salary. Its own future change request.
- **Location/geography as a formal success criterion** — named only in the outcome's
  Context section today ("urgency, salary targets, target companies, geography"), never
  promoted to an explicit Success criterion. No scope decision made on formalizing it in
  this change; leave that wording as-is. (Notably, the IA's own "Compensation Signal"
  definition already ties salary to "role, seniority, or location" — so location will
  likely resurface naturally once compensation is spec'd, but is not being decided here.)
- **Company-specific breakdowns** — `outcomes/understand-market-health-before-searching.md`
  explicitly lists "Company-specific research" as Out of scope; this change must not
  contradict that.

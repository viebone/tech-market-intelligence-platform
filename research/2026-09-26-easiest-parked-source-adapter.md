source: stakeholder-request
date: 2026-09-26

User: "what about personio and other sources that we discussed?" → "start with the easiest one please"

Context: `research/2026-09-23-us-eu-employer-panel-expansion.md` and
`changes/2026-09-23-us-eu-employer-panel-expansion.md` parked these as out-of-scope follow-ups,
each needing its own change request and live terms verification (Rule 13): France Travail,
Arbeitnow, Jobicy, USAJOBS, Personio, Recruitee. Related: `EMPLOYER_PANEL.md` — "Next ATS
adapters under consideration".

## Probe results, 2026-09-26 (one request per endpoint, identified User-Agent, nothing stored)

| Candidate | Live result | Auth | Terms found | Verdict |
|---|---|---|---|---|
| **Personio** | `GET https://{slug}.jobs.personio.de/xml` → 200 `text/xml` for `personio`; per-company `<workzag-jobs><position>` with id, subcompany, office(s), department, recruitingCategory, name, employmentType, seniority, schedule, yearsOfExperience, occupation, createdAt, jobDescriptions | **None.** Personio's own help/dev docs: "No credentials are needed to access your XML feed"; feed is enabled per customer (Settings > Recruiting > Career page > Enable XML feed) for embedding jobs on their own site | Developer docs (`developer.personio.de/docs/retrieving-open-job-positions`) state no rate limit, no licence, no restriction on third-party reads. Support FAQ page returned 403 to the fetch tool — not read. No robots.txt on the jobs host (returns the SPA 404 page) | **Easiest.** Same per-company shape as Workable/Greenhouse; one adapter, no key. |
| Recruitee | `GET https://{slug}.recruitee.com/api/offers/` → 200 JSON for `bunq` (404 for `mollie`, `sendcloud` — wrong slugs, not evidence of anything) | None in practice — but Recruitee's own docs say the *Careers Site API* "requires authentication" (API token); the unauthenticated `/api/offers` on public sites is undocumented by them | No explicit third-party terms found | Works, but a grey area on permission — do second, after asking/confirming. |
| Arbeitnow | `GET https://www.arbeitnow.com/api/job-board-api` → 200 JSON, paginated aggregate feed (Doctolib et al.) | None | No published terms found on its API pages; contact@arbeitnow.com suggested. robots.txt allows all | Keyless, but it is an *aggregator* (many employers, one feed): needs cross-source dedupe (out of scope) and a licence answer we don't have. |
| Jobicy | `GET https://jobicy.com/api/v2/remote-jobs` → 200 JSON | None | Response `friendlyNotice`: credit Jobicy with a direct link and make every apply button redirect to the original job URL. Docs page is behind a Cloudflare challenge (403) — not read | Remote-only, attribution + apply-redirect obligations the product has no surface for yet. Not easiest. |
| France Travail | Not probed | OAuth2 client credentials (registration) | — | Needs credentials — not easiest. |
| USAJOBS | Not probed | API key + email header (registration) | — | Needs credentials — not easiest. |

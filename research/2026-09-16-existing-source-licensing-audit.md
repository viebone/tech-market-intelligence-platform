source: internal
date: 2026-09-16

Triggered by extending the "always name the source according to its licence" principle from the
new scraped-data-sources feature back across this product's other external data sources — see
`research/2026-09-16-scraping-good-practices-refinement.md`'s "if a data source doesn't have a
[confirmed legitimate] licence, we don't use it" rule, and the resolved clarification that this
means any confirmed legitimate reuse right (public domain, Open Government Licence, a source's
own bespoke reuse policy, CC, ...), not literally the Creative Commons brand only.

## What was checked, and what was found (fetched directly, 2026-09-16)

| Source | Access | Licence found | Confidence |
|---|---|---|---|
| SEC EDGAR (8-K Item 2.05) | Keyless full-text search API | **Public domain / no copyright restriction.** SEC's own privacy/reuse page, quoted directly: "Information presented on sec.gov is considered public information and may be copied or further distributed by users of the web site without the SEC's permission." | High — read directly off sec.gov |
| UK Companies House (Streaming API) | Streaming API key | **Open Government Licence v3.0.** Crown copyright; commercial reuse permitted with attribution. | High — confirmed via Companies House developer docs / gov.uk |
| Eurofound European Restructuring Monitor | Keyless CSV export | The EU's own bespoke reuse policy (not literally Creative Commons, though similar in spirit — attribution required, no distortion of meaning, reuse for commercial and non-commercial purposes authorised). | Medium — eurofound.europa.eu's legal/copyright pages rate-limited (HTTP 429) on direct fetch; this is from search-result excerpts of the EU's general reuse framework, not eurofound's own page verbatim. Worth a direct re-check later if this ever matters for something high-stakes. |
| US WARN notices (via WARN Firehose, warnfirehose.com) | Free-tier API key | **Two-layer situation, one clean, one not.** The *underlying* WARN Act data is public record, no copyright (WARN Firehose's own terms say so: "public record and is not subject to copyright by us"). But **WARN Firehose's own Terms of Service impose a separate contractual restriction**: "Resell, sublicense, or redistribute raw API access, bulk data downloads, or data exports to third parties without a separate commercial license agreement with us." | Medium-high on the quoted text; **not resolved** whether TMIP's specific use (storing structured facts derived from the free-tier API, not reselling raw exports) falls inside or outside that restriction — this is a judgement call about the operator's own agreed account terms, not something a public-page fetch can settle. |

## The one real open item

**WARN Firehose.** This is not a "get the licence" problem — it's a "does our actual use comply
with a contract you already agreed to" problem. Recommended next step: either re-read the
Terms of Service you accepted when signing up for the free tier (the exact wording may differ
from what a public terms page shows to a non-logged-in visitor), or email WARN Firehose directly
— the same move that got IT Jobs Watch's permission in the first place — describing exactly what
this product does with their data (ingests structured facts into its own database, doesn't
resell raw exports or bulk downloads) and asking whether that's within the free tier's terms.

## Not changed as a result of this audit

Per the operator's explicit decision: SEC EDGAR, UK Companies House, and Eurofound ERM all have
a confirmed, legitimate reuse basis (even though none is literally "Creative Commons") and
continue running as-is. Nothing in this audit found a reason to disable any of them.

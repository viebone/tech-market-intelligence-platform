---
id: job-classification
feature: market-health
directive: low
status: active
created: 2026-07-16
---

# Job Classification Taxonomy — Reference Spec

## What this spec is

Defines the canonical taxonomy used to classify every job posting ingested for Market Health:
role category, seniority, and track. This is the single source of truth for these values —
`backend/specs/market-health/api.md` and `frontend/specs/market-health/architecture.md` must
reference this file rather than each defining their own version of these enums.

`Role Category` is not a new concept — it is the same term already defined in
`design/information-architecture.md` Content Taxonomy (`Role Category`: "One of the three
tracked job categories: Designer, Product Manager, Engineer"). This spec extends that fixed,
product-wide definition with the sub-specialization, seniority, and track detail needed to
classify a real job posting against it. It does not redefine or rename it.

Reference: `design/market-health/experience.md` — the trend chart's three lines and the
Thinking Process accordion's role/seniority filter chips both draw their values from this
taxonomy.

---

## Role Category

Closed set — exactly the three categories fixed by the information architecture. No fourth
category may be added without first updating `design/information-architecture.md` (which would
also require a new accent colour, since `design/visual-design.md` currently caps the product at
three accent colours, one per Role Category).

| Role Category | Sub-specializations |
|---|---|
| Designer | UX Designer, UX Researcher, Product Designer, UI Designer |
| Product Manager | Product Manager, Product Owner, Technical Product Manager, Data Product Manager, Growth Product Manager |
| Engineer | Frontend Engineer, Backend Engineer, Full-stack Engineer, Mobile Engineer, ML/AI Engineer, Data Engineer, DevOps/SRE |

A sub-specialization is a detail level within a fixed Role Category — it narrows, it never
crosses a category boundary. This list starts narrow and widens only once real posting data
justifies it (see Raw Title below).

**Why one source filter covers all three categories:** when sourcing postings from the Adzuna
Jobs API, `category=it-jobs` was validated empirically as the correct filter for Designer,
Product Manager, and Engineer postings alike. An earlier assumption — that Designer postings
belong under Adzuna's `category=creative-design-jobs` — was tested and rejected: that category
captured only about 13% of matching Designer postings and skewed mean salary roughly 40% low,
because it mostly captures graphic/brand design work rather than the product/UX roles embedded
in tech teams that this product tracks.

---

## Seniority

Ordered ladder, a single value per posting:

```
entry → junior → mid → senior → lead → principal → manager → director → vp → exec
```

`mid` is also written "midweight" in UK job titles — the product's current data source
(Adzuna) is UK-only. Classify UK "midweight" postings as `mid`.

---

## Track

A dimension separate from seniority: `ic` (individual contributor) or `management`.

**Why this isn't folded into seniority:** "Lead" is genuinely ambiguous — at some companies it
names a senior individual contributor who still ships work, at others it names the first
management rung. Collapsing both meanings into one seniority value would corrupt any trend
answering "how many roles are management" — a Lead-heavy quarter could mean either more senior
ICs or more first-line managers, and those point to opposite conclusions for someone deciding
whether to pursue an IC or a management track.

---

## Raw Title (a trend input, not a filter)

Every posting's original job title is stored verbatim, independent of the closed Role Category,
Seniority, and Track fields above. It is not exposed as a user-facing filter in v1 — it exists
to catch emerging titles (e.g. "AI Product Manager," "Founding Engineer") that recur often
enough to be a real market signal, before they're common enough to justify a new Role Category
or sub-specialization. Reviewing raw title frequency is how this taxonomy gets revised over
time — not by guessing upfront what categories will eventually matter.

---

## Classification Method

Each posting is classified by an LLM call (technical implementation defined in
`backend/specs/market-health/api.md`), constrained to return only values from the Role
Category, Seniority, and Track sets defined above — it cannot invent a category outside this
taxonomy.

**The `other` escape hatch:** a posting that genuinely does not fit is classified `other`
rather than forced into the closest match. For example, a real posting encountered while
researching this taxonomy was titled "Product Manager - Health Policy" — nominally a Product
Manager title, but not a tech-market role in the sense this product tracks. `other`
classifications are logged for human review rather than silently folded into Product Manager
trend counts, which protects the trend data's accuracy.

**Taxonomy versioning:** every classification is tagged with a `taxonomy_version`. If this
taxonomy is later revised — a category added, a seniority level split — historical
classifications keep the version that produced them, so it is always possible to tell which
labels came from which version of this document rather than silently blending incompatible
labels together.

---

## What this rules out

- Free-text or classifier-invented Role Category, Seniority, or Track values — these three
  fields are always drawn from the closed sets above, never generated ad hoc
- A fourth Role Category, or renaming any of the three — both require updating
  `design/information-architecture.md` and `design/visual-design.md` first, not just this file
- Treating "Lead" as a seniority level without also capturing Track — the two are always
  captured together
- Using raw job title as a filter users can select against in v1 — it is a research input for
  revising this taxonomy, not a product surface
- Reclassifying historical postings silently when the taxonomy changes — old classifications
  keep their original `taxonomy_version`

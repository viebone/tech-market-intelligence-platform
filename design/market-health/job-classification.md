---
id: job-classification
feature: market-health
directive: low
status: active
created: 2026-07-16
updated: 2026-08-09
---

# Job Classification Taxonomy — Reference Spec

## What this spec is

Defines the canonical taxonomy used to classify every job posting ingested for Market Health:
role category, seniority, and track — plus, as of 2026-08-09, the **Requirements Taxonomy**
(skills, education level, language requirements) backing the IA's **Requirements Signal**
(`design/information-architecture.md` Content Taxonomy). This is the single source of truth
for all of these values — `backend/specs/market-health/api.md` and
`frontend/specs/market-health/architecture.md` must reference this file rather than each
defining their own version of these enums.

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

## Requirements Taxonomy (Requirements Signal)

Added 2026-08-09, backing the IA's **Requirements Signal**
(`design/information-architecture.md` Content Taxonomy). Defines the closed-ish sets used
to extract structured requirements from a posting's full *description* — a different input
than Role Category/Seniority/Track above, which classify from the *title* alone (see
Requirements Extraction Method, below, for why that distinction matters). Same discipline
as the rest of this document: closed sets to keep answers reliably aggregatable, with an
explicit freeform catch-all so a posting's genuinely unusual requirement is never silently
discarded just because it wasn't anticipated.

### Skills

Closed per Role Category, reviewed periodically — same "starts narrow, widens once real
data justifies it" discipline already established for sub-specializations, not exhaustive
on day one.

| Role Category | Tracked skills (v1) |
|---|---|
| Designer | Figma / design tooling, Design systems, UX research, Prototyping, Visual/UI design, Accessibility, Front-end coding (HTML/CSS/JS), Data & analytics literacy, AI-assisted design tools |
| Product Manager | Data analysis / SQL, Experimentation (A/B testing), Roadmapping & prioritization, Stakeholder management, Technical/API fluency, User research, AI/ML product experience, Business strategy (GTM, pricing) |
| Engineer | Frontend frameworks, Backend frameworks, Cloud/infrastructure, Databases, System design, ML/AI, Mobile, DevOps/SRE, Security |

Each tracked skill mention is captured with a requirement level: `must_have` or
`nice_to_have`. A skill mentioned in a posting that doesn't map to any tracked skill for
that posting's Role Category goes into **Other requirements** (below) rather than being
forced into the nearest match or silently dropped — the same principle as the `other` Role
Category escape hatch.

**Why per-category, not one shared list:** a shared list would either be too generic to be
useful (only skills that apply everywhere) or too long to be a meaningful closed set (every
discipline's skills at once). Scoping to the Role Category a posting is already classified
under keeps each list a genuinely reviewable size.

### Education level

A single closed value per posting, when mentioned at all:

```
not_mentioned → bootcamp_or_equivalent → bachelors → masters → phd
```

`not_mentioned` is the default and is **not itself informative** — most postings don't state
an education requirement at all, and that absence must never be read as "no degree needed."

### Language requirements

Spoken/written language proficiency — not programming languages (those are covered under
Skills, above). Relevant mainly for region-specific or client-facing roles. Captured as a
list of `{language, requirement_level}` pairs, `requirement_level` being `required` or
`preferred`. No closed list of languages is needed here — natural language names are already
a stable, unambiguous set (unlike skill phrasing, which varies) and don't need a curation
pass the way skills or role categories do.

### Responsibilities

Deliberately **not** a closed taxonomy — captured as a short, LLM-generated summary (2-4
sentences) of the core responsibilities, since day-to-day duties are too varied and specific
to force into a small fixed set the way skills or education can be. This is a summary of
what the posting says, not an extracted structured fact — held to the same "interpretation,
not a verified fact" honesty as everything else in this section (see Requirements
Extraction Method, below).

### Other requirements (the catch-all)

A freeform field capturing anything notable in a posting's description that doesn't fit
skills, education, or language requirements above — e.g. a specific certification, a
security clearance, a portfolio requirement. Never forced into one of the standard fields
just to avoid using this one. This is what keeps the standard structure honest: a posting
with a genuinely unusual requirement doesn't get that detail silently discarded just
because the schema didn't anticipate it.

## Requirements Extraction Method

Distinct from Classification Method (below), which classifies Role Category/Seniority/Track
from a posting's *title* alone. Requirements extraction reads a posting's full
*description* — there is no per-title shortcut here, since two postings sharing a title can
have entirely different actual requirements (see `backend/specs/market-health/api.md` —
Business Logic — Requirements extraction, for the technical/cost implications of that
difference).

**This is interpretation, not verified fact.** Every extracted field is the LLM's reading of
free text a company wrote in whatever style and phrasing it chose — never treat it as a
guarantee the posting's true requirements were captured perfectly. Answers built from this
data must speak in aggregate/proportional terms ("42% of postings mention X") rather than
absolute claims ("all postings require X"), and must always disclose how many postings an
answer is based on — the same discipline already established for Compensation Signal
(`design/market-health/experience.md`, User Flow 7a).

---

## Classification Method

Each posting is classified either by an LLM call, or — for titles that are unambiguously
not tech roles at all (e.g. "Account Executive," "Payroll Specialist," "Legal Counsel") — by
a cheap heuristic pre-filter that resolves straight to `other` without spending a model call
(technical implementation defined in `backend/specs/market-health/api.md`). Both paths are
constrained to the same closed sets: the pre-filter can only ever produce `other`, never
invent or guess a real category, and the LLM path returns only values from the Role
Category, Seniority, and Track sets defined above. Which path a given posting takes is a
cost optimization, not a taxonomy decision — it changes nothing about what `other` means or
what qualifies for it, only how cheaply the obvious cases are reached.

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
- Forcing a mentioned skill into the nearest tracked skill for its Role Category, or
  silently dropping it, when it doesn't genuinely match — it belongs in the freeform catch-all
- Treating `education_level: not_mentioned` as evidence that no degree is required — absence
  of a stated requirement is not itself a signal
- Presenting a Requirements Signal answer as an absolute claim ("all X roles require Y") —
  it is always a proportion of an interpreted sample, and must be stated as such
- Trying to fit day-to-day responsibilities into a closed taxonomy the way skills or
  education are — responsibilities are summarized, not classified into a fixed set

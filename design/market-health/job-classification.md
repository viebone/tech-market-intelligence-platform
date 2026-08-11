---
id: job-classification
feature: market-health
directive: low
status: active
created: 2026-07-16
updated: 2026-08-11
---

# Job Classification Taxonomy — Reference Spec

## What this spec is

Defines the canonical taxonomy used to classify every job posting ingested for Market Health:
role category, specialization, level, and track — plus the **Requirements Taxonomy**
(skills, education, years of experience, work arrangement, language requirements) backing
the IA's **Requirements Signal** (`design/information-architecture.md` Content Taxonomy).
This is the single source of truth for all of these values — `backend/specs/market-health/api.md`
and `frontend/specs/market-health/architecture.md` must reference this file rather than each
defining their own version of these enums.

`Role Category` is not a new concept — it is the same term already defined in
`design/information-architecture.md` Content Taxonomy (`Role Category`: "One of the three
tracked job categories: Designer, Product Manager, Engineer"). This spec extends that fixed,
product-wide definition with the specialization, level, track, and requirements detail needed
to classify a real job posting against it. It does not redefine or rename it, and does not
change what the product shows the user — everything in this revision (2026-08-11) restructures
what sits *underneath* Role Category, not the term itself or its three values.

Reference: `design/market-health/experience.md` — the trend chart's three lines and the
Thinking Process accordion's filter chips both draw their values from this taxonomy.

---

## Role Category

Closed set — exactly the three categories fixed by the information architecture. No fourth
category may be added without first updating `design/information-architecture.md` (which would
also require a new accent colour, since `design/visual-design.md` currently caps the product at
three accent colours, one per Role Category).

Internally, each Role Category is backed by an **occupation family** — Design, Product,
Engineering — rather than treating "Designer," "Product Manager," and "Engineer" as the
fundamental ontology of a job. This is a documentation/internal-naming distinction, not a
product change: the product still shows "Designer / Product Manager / Engineer" everywhere a
user sees it. The reason it matters internally: as real titles like "VP Product," "Head of
Design," or "Director of Product Design" appear (they already do — see Level and Track,
below), "Product Manager" becomes an awkward parent category for "VP Product," while "Product"
(the family) doesn't have that problem. Occupation family is what a Role Category *is*;
"Designer / Product Manager / Engineer" is how the product *names* it.

| Role Category | Occupation Family | Specializations |
|---|---|---|
| Designer | Design | UX Designer, UX Researcher, Product Designer, UI Designer, Content Designer / UX Writer, Design Systems, Other Design |
| Product Manager | Product | Product Manager, Product Owner, Technical Product Manager, Data Product Manager, Growth Product Manager |
| Engineer | Engineering | Frontend Engineer, Backend Engineer, Full-stack Engineer, Mobile Engineer, ML/AI Engineer, Data Engineer, DevOps/SRE |

A specialization is a detail level within a fixed Role Category — it narrows, it never
crosses a category boundary. This list starts narrow and widens only once real posting data
justifies it (see Raw Title below). The three Designer additions in this revision (Content
Designer / UX Writer, Design Systems, Other Design) come from the same UX-specific research
that originally shaped this taxonomy — title variety within Design is wider than the original
four specializations captured.

**A specialization is allowed to be `unknown`.** A title like "Senior Designer – Digital
Products" is clearly Design, but doesn't give enough evidence to say UX vs. Product vs. UI. In
that case, `role_category = Designer, specialization = unknown` is the correct classification —
not a guess at the closest-sounding specialization. This is the same principle the `other`
Role Category escape hatch already applies at the top level (see Classification Method,
below); this revision extends it one level down, to specialization.

**Why one source filter covers all three categories:** when sourcing postings from the Adzuna
Jobs API, `category=it-jobs` was validated empirically as the correct filter for Designer,
Product Manager, and Engineer postings alike. An earlier assumption — that Designer postings
belong under Adzuna's `category=creative-design-jobs` — was tested and rejected: that category
captured only about 13% of matching Designer postings and skewed mean salary roughly 40% low,
because it mostly captures graphic/brand design work rather than the product/UX roles embedded
in tech teams that this product tracks. (Adzuna itself was retired 2026-08-03 — this
historical note is kept for context on why the original filter choice was correct at the time.)

---

## Level

Ordered ladder, a single value per posting, describing seniority independent of whether the
posting is an individual-contributor or management position:

```
entry → junior → mid → senior → lead → principal → director → vp → executive → unknown
```

`mid` is also written "midweight" in UK job titles.

**This replaces the single `seniority` ladder used before this revision**, which combined
level and organizational function into one value — including `manager` as a ladder rung
alongside `senior`, `lead`, and `principal`. That collapsed real information: a real check
against classified production data (2026-08-11) found 160 postings with titles like
"Engineering Manager, Model Flywheel," "Systems Engineering Manager," and "Support Engineering
Manager (APAC)" — spanning what should be a real range of levels — all flattened into the
identical bucket `seniority = manager`, because "manager" absorbed the level distinction
entirely. "Senior Engineering Manager" and a first-line "Engineering Manager" became
indistinguishable. `level` + `track` (below) restores that distinction: "Senior Engineering
Manager" is `level = senior, track = management`; "Director of Product" is
`level = director, track = management`; "Principal Engineer" is `level = principal,
track = ic`.

`unknown` is a valid `level` value, same reasoning as specialization's `unknown` above — a
title that gives no real signal of seniority should say so, not default to a guessed middle
value.

---

## Track

A dimension separate from level: `ic` (individual contributor), `management`, or `unknown`.

**Why this isn't folded into level:** "Lead" is genuinely ambiguous — at some companies it
names a senior individual contributor who still ships work, at others it names the first
management rung. Collapsing both meanings into one value would corrupt any trend answering
"how many roles are management" — a Lead-heavy quarter could mean either more senior ICs or
more first-line managers, and those point to opposite conclusions for someone deciding whether
to pursue an IC or a management track. This reasoning already justified keeping `track`
separate from the old `seniority` ladder; this revision applies the same reasoning one step
further, by also removing "manager" as a level rung (see Level, above) rather than leaving a
partial overlap between the two fields.

`unknown` is added to `track` in this revision for the same reason as `level` and
specialization: a title can genuinely fail to disclose whether a role is IC or management
("Digital Lead" — see Unknown vs. Other, below), and guessing would corrupt track-based trend
answers the same way collapsing level would.

---

## Unknown vs. Other

Two closed-set escape hatches exist in this taxonomy, and they mean different things:

- **`other`** — the classifier has enough evidence to know what the posting is, and it
  confidently is not one of the tracked occupations. Example: "Corporate Lawyer." The
  posting was correctly sourced as ambiguous by the ingestion query, but it's genuinely not a
  Design/Product/Engineering role.
- **`unknown`** — the classifier does not have enough evidence from the title alone to
  classify the posting, even though it might plausibly be one of the tracked occupations.
  Example: "Digital Lead." This is not the same claim as "this definitely isn't a tracked
  role" — it's "the title alone can't tell."

**Why the distinction matters analytically:** these two failure modes point to completely
different problems, and conflating them (as this taxonomy did before this revision — `other`
was the only escape hatch) makes both invisible. A high `other` rate signals a sourcing/
targeting problem — the ingestion query is pulling in postings that were never going to be
relevant. A high `unknown` rate signals a classification quality problem — titles that likely
are relevant aren't giving the classifier enough to work with, which might mean the title-only
classification rule (see Classification Method, below) needs a fallback, or the specialization/
level lists need widening. Without the distinction, both look like the same undifferentiated
bucket of "stuff we couldn't classify," and the two very different fixes get proposed against
one merged number.

This distinction applies wherever a closed set exists in this taxonomy: Role Category (at the
top level, `unknown` sits alongside `other` the same way it always has for the closed
category set) and specialization (see Role Category, above). It does not apply to Level or
Track's `unknown` value in quite the same way — there is no equivalent "confidently not a
level" state, so `unknown` is the only escape hatch for those two fields.

---

## Raw Title (a trend input, not a filter)

Every posting's original job title is stored verbatim, independent of the closed Role Category,
Specialization, Level, and Track fields above. It is not exposed as a user-facing filter in v1
— it exists to catch emerging titles (e.g. "AI Product Manager," "Founding Engineer") that
recur often enough to be a real market signal, before they're common enough to justify a new
Role Category or specialization. Reviewing raw title frequency is how this taxonomy gets
revised over time — not by guessing upfront what categories will eventually matter. This
revision itself is an example: the Level/Track split and the Designer specialization
additions both came from reviewing real raw titles and real classified data, not from
redesigning the taxonomy in the abstract.

---

## Requirements Taxonomy (Requirements Signal)

Backs the IA's **Requirements Signal** (`design/information-architecture.md` Content
Taxonomy). Defines the closed-ish sets used to extract structured requirements from a
posting's full *description* — a different input than Role Category/Specialization/Level/
Track above, which classify from the *title* alone (see Requirements Extraction Method,
below, for why that distinction matters). Same discipline as the rest of this document:
closed sets to keep answers reliably aggregatable, with an explicit freeform catch-all so a
posting's genuinely unusual requirement is never silently discarded just because it wasn't
anticipated.

### Skills

Captured as `raw_skill` (the mention as it appears, normalized only for obvious casing/
punctuation) plus `skill_group` (a closed, curated category). Two fields, not one — a change
from the original design, which stored only a skill_group-equivalent string. Storing raw text
alongside the category is what makes a question like "which specific technologies are
becoming more frequently requested" answerable later ("React appears in 31% of frontend
roles") rather than only the coarser "42% of engineering roles request frontend-framework
experience." A **`normalized_skill`** field (canonicalizing spelling variants — "React.js" and
"React" collapsing to one value) is deliberately deferred, not built now: doing that well
needs a real skill-name dictionary, and building one upfront — before real spelling-variant
volume shows which variants actually matter — is the same premature-abstraction mistake this
taxonomy has avoided elsewhere (see Raw Title, above, and the sub-specialization/skill "starts
narrow" discipline throughout this document). `raw_skill` + `skill_group` ship now;
`normalized_skill` is a future pass once real data justifies the dictionary work.

`skill_group` is no longer selected purely from a fixed list of hands-on-technical categories
per Role Category. It's selected aware of **Role Category, Track, and Specialization**
together, because a large, real population of postings has no hands-on technical requirements
at all — and forcing them against a technical-only list was structurally guaranteed to
under-report. A real check against production data (2026-08-11) found Engineer postings
averaging 1.45 tracked skills per posting versus Product Manager's 3.09 and Designer's 2.75,
traced to two causes: (1) 216 Engineer + 26 Product Manager + 7 Designer postings are
`track = management`, and (2) roughly 265 Engineer postings carry a Solutions
Engineer/Solutions Architect/Customer Engineer/Support Engineer/Forward Deployed
specialization — pre-sales and customer-facing roles, not hands-on coding. Neither population
has anything in a hands-on technical list to match against, by construction, regardless of how
well-written the posting is.

| Skill group applies when… | Tracked skill groups (v1) |
|---|---|
| Any Role Category, `track = management` | **People leadership**: Team building & hiring, Coaching & career development, Budget & resource planning, Cross-functional / executive stakeholder management, Organizational design, Technical strategy & oversight, Performance management |
| Role Category = Engineer, specialization in {Solutions Engineer, Solutions Architect, Customer Engineer, Support Engineer, Forward Deployed Engineer, Forward Deployed Software Engineer} | **Pre-sales & solutions**: Technical pre-sales & discovery, RFP / technical proposal writing, Executive & technical stakeholder relationship-building, Co-solutioning & partner enablement, Technical demoing & solution design, Escalation & incident troubleshooting, Customer-facing communication |
| Role Category = Designer, `track = ic` | Figma / design tooling, Design systems, UX research, Prototyping, Visual/UI design, Accessibility, Front-end coding (HTML/CSS/JS), Data & analytics literacy, AI-assisted design tools |
| Role Category = Product Manager, `track = ic` | Data analysis / SQL, Experimentation (A/B testing), Roadmapping & prioritization, Stakeholder management, Technical/API fluency, User research, AI/ML product experience, Business strategy (GTM, pricing) |
| Role Category = Engineer, `track = ic`, hands-on specialization | Frontend frameworks, Backend frameworks, Cloud/infrastructure, Databases, System design, ML/AI, Mobile, DevOps/SRE, Security, **Data engineering / big data** (Kafka, Spark, Airflow, Trino, Iceberg-type tools), **Blockchain / Web3** (smart contracts, EVM, Solana, Stellar-type tech) |

The two new Engineer groups (Data engineering / big data, Blockchain / Web3) come from the
same production-data check: named technologies like Kafka, Spark, Airflow, and blockchain/
smart-contract stacks recurred often enough in real `other_requirements` freeform text to
justify promoting them to tracked groups, rather than leaving them permanently uncategorized.

More than one group's list can apply to a single posting where relevant (e.g. a Designer
posting with `track = management` should be checked against both People leadership and the
Designer IC list, since a Design Manager posting sometimes states craft expectations
alongside management ones) — this is a widening of scope, not a replacement of the
occupation-specific lists.

Each tracked skill mention is captured with a requirement level: `must_have` or
`nice_to_have`. A skill mentioned in a posting that doesn't map to any tracked skill_group
applicable to that posting goes into **Other requirements** (below) rather than being forced
into the nearest match or silently dropped — the same principle as the `other` Role Category
escape hatch, now applied at the skill level too.

**Why per-population, not one shared list:** a shared list would either be too generic to be
useful (only skills that apply everywhere) or too long to be a meaningful closed set (every
group's skills at once). Scoping to the population a posting actually belongs to (via Role
Category, Track, and Specialization together) keeps each list a genuinely reviewable size
while actually covering the posting in front of it.

### Education level

A single closed value per posting, when mentioned at all:

```
not_mentioned → bootcamp_or_equivalent → bachelors → masters → phd
```

`not_mentioned` is the default and is **not itself informative** — most postings don't state
an education requirement at all, and that absence must never be read as "no degree needed."

Two additional fields capture nuance the single ladder value loses on its own:

- **`education_required`** — whether the stated education level is a hard requirement or a
  preference (`required` / `preferred` / `not_mentioned`).
- **`equivalent_experience_accepted`** — boolean. Many real postings state something like
  "Bachelor's degree or equivalent professional experience." Collapsing that straight to
  `education_level = bachelors` loses the "or equivalent" clause entirely, and a downstream
  claim like "38% of Product roles require a bachelor's degree" would be misleading if a
  meaningful share of those postings explicitly accept equivalent experience instead. This
  field keeps that nuance intact rather than silently discarding it.

### Years of experience

**New in this revision.** `years_experience_min` — an integer, parsed from patterns like "3+
years," "5-8 years," "10+ years of experience." Promoted out of the freeform catch-all because
it's one of the most consistent, high-value signals across real postings — it appeared in
nearly every `other_requirements` entry captured before this revision existed as a dedicated
field, and it directly answers a real product question ("how many years of experience does a
Senior Security Engineer posting typically require?") that was previously unqueryable except
by reading prose one posting at a time.

### Work arrangement

**New in this revision.** A closed value per posting: `onsite`, `hybrid`, `remote`,
`not_mentioned`. Parsed from statements like "100% telecommuting permitted," "50% remote work
permitted," "based in the PST time zone" (onsite/hybrid signal). Also promoted out of the
freeform catch-all for the same reason as years of experience — a recurring, structured fact
that was previously only readable as prose.

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
skills, education, years of experience, work arrangement, or language requirements above —
e.g. a specific certification, a security clearance, a portfolio requirement. Never forced
into one of the standard fields just to avoid using this one. This is what keeps the standard
structure honest: a posting with a genuinely unusual requirement doesn't get that detail
silently discarded just because the schema didn't anticipate it.

**This field must never capture salary or compensation figures.** That data belongs to the
Compensation Signal pipeline (`backend/specs/market-health/api.md` — Business Logic —
Compensation extraction), which already handles it with its own structured/parsed confidence
distinction. A salary figure appearing in this pipeline's output — even in the freeform
catch-all — would create a second, uncoordinated source of truth for the same fact. Requirements
extraction must ignore compensation text entirely, not re-capture it.

## Requirements Extraction Method

Distinct from Classification Method (below), which classifies Role Category/Specialization/
Level/Track from a posting's *title* alone. Requirements extraction reads a posting's full
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
Category, Specialization, Level, and Track sets defined above. Which path a given posting
takes is a cost optimization, not a taxonomy decision — it changes nothing about what `other`
means or what qualifies for it, only how cheaply the obvious cases are reached.

**The `other` escape hatch:** a posting that genuinely does not fit is classified `other`
rather than forced into the closest match. For example, a real posting encountered while
researching this taxonomy was titled "Product Manager - Health Policy" — nominally a Product
Manager title, but not a tech-market role in the sense this product tracks. `other`
classifications are logged for human review rather than silently folded into Product Manager
trend counts, which protects the trend data's accuracy. See Unknown vs. Other, above, for how
`other` differs from `unknown` — both are real, distinct outcomes of this method.

**`classification_confidence`** — **new in this revision.** A closed value returned by the
LLM alongside every classification: `low`, `medium`, or `high`. This is the model's own
self-reported confidence, not a measured accuracy figure — same "interpretation, not verified
fact" honesty already applied to Requirements extraction. It exists so classifications can
eventually be filtered by confidence for particularly sensitive analyses, and so a human
reviewer has a place to start (low-confidence classifications are the ones worth spot-checking
first) rather than needing to review the full dataset uniformly.

**Taxonomy versioning:** every classification is tagged with a `taxonomy_version`. If this
taxonomy is later revised — a category added, a level split — historical classifications keep
the version that produced them, so it is always possible to tell which labels came from which
version of this document rather than silently blending incompatible labels together. This
revision (2026-08-11) is itself exactly the kind of change this rule anticipates: existing
classifications under the prior `seniority` ladder are not silently reinterpreted under
`level`/`track` — they are reprocessed and re-tagged with the new `taxonomy_version`, and the
old version's classifications remain inspectable as what they actually were at the time (see
`changes/2026-08-11-classification-taxonomy-redesign.md` for the reprocessing plan).

---

## What this rules out

- Free-text or classifier-invented Role Category, Specialization, Level, or Track values —
  these four fields are always drawn from the closed sets above, never generated ad hoc
- A fourth Role Category, or renaming any of the three — both require updating
  `design/information-architecture.md` and `design/visual-design.md` first, not just this file
- Treating "Lead" (or "Manager," "Director," etc.) as a level without also capturing Track —
  the two are always captured together
- Using `manager` (or any organizational-function word) as a Level value — organizational
  function is Track's job, not Level's; this was the core bug this revision fixes
- Treating `other` and `unknown` as interchangeable — `other` means confidently not tracked,
  `unknown` means not enough evidence to tell; conflating them hides two different data
  problems behind one number
- Using raw job title as a filter users can select against in v1 — it is a research input for
  revising this taxonomy, not a product surface
- Reclassifying historical postings silently when the taxonomy changes — old classifications
  keep their original `taxonomy_version`
- Forcing a mentioned skill into the nearest tracked skill_group for its population, or
  silently dropping it, when it doesn't genuinely match — it belongs in the freeform catch-all
- Scoring a posting's skills only against a hands-on-technical list when its Track or
  Specialization indicates it isn't a hands-on-technical role — skill_group selection must
  account for Role Category, Track, and Specialization together, not Role Category alone
- Treating `education_level: not_mentioned` as evidence that no degree is required — absence
  of a stated requirement is not itself a signal
- Collapsing "Bachelor's degree or equivalent experience" into a bare `education_level:
  bachelors` — `equivalent_experience_accepted` must capture that nuance separately
- Extracting salary or compensation figures anywhere in the Requirements Taxonomy, including
  the freeform catch-all — that is Compensation Signal's data, not Requirements Signal's
- Presenting a Requirements Signal answer as an absolute claim ("all X roles require Y") —
  it is always a proportion of an interpreted sample, and must be stated as such
- Trying to fit day-to-day responsibilities into a closed taxonomy the way skills or
  education are — responsibilities are summarized, not classified into a fixed set

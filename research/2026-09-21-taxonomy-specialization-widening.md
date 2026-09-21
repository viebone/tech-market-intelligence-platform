---
source: user-feedback
date: 2026-09-21
---

User (this session): "we need to break down these 3 categories into more categories, please make
a suggestion of the more popular roles that can break down those 3 categories that we already
have and lets go for it" — following directly from the prior day's "Job Function" idea (a
separate, additive field for the `other` bucket). This is a distinct, second ask: widen the
*specialization* closed sets documented in `job-classification.md` for the 3 tracked Role
Categories themselves, grounded in what real production data already shows.

## Real data pulled before proposing anything

Queried `classifications` for the top specialization values per `role_category`, in production,
right now (not guessed):

**Designer** (174 classified, non-unknown specializations):
Product Designer 107, UX Researcher 12, Brand Designer 11, Other Design 7, Motion Designer 5,
Web Designer 3, Creative Director 3, Product Design Manager 3, Art Director 2, UX Writer 2,
Visual Designer 2, Design Program Manager 2, (long tail of 1s).

**Product Manager** (353 classified):
Product Manager 219, Technical Program Manager 57, Platform Product Manager 15, Growth Product
Manager 11, AI Product Manager 5, Forward Deployed Product Manager 5, Technical Product Manager
5, Payments Product Manager 4, Enterprise Product Manager 3, Product Owner 3, (long tail).

**Engineer** (2,702 classified — by far the largest population):
Software Engineer 776, Machine Learning Engineer 213, Security Engineer 189, Solutions Engineer
145, Forward Deployed Engineer 141, Backend Engineer 138, Data Scientist 122, Engineering
Manager 118, Solutions Architect 111, Support Engineer 92, Customer Engineer 76, Data Engineer
76, Full Stack Engineer 74, Infrastructure Engineer 60, Research Engineer 57, Frontend Engineer
43, Forward Deployed Software Engineer 40, AI Engineer 38, Android Engineer 36, DevOps/SRE
Engineer 35, Platform Engineer 28, Site Reliability Engineer 25, Backend Software Engineer 23,
Network Engineer 23, iOS Engineer 23.

## What this shows

The LLM has already been organically inventing most of these values — `specialization` has no
closed-set enforcement in code today (`classification.py::_validate()` passes it through
unvalidated, unlike `level`/`track`). The gap is entirely in `job-classification.md`'s
documented list, which is now visibly out of date against real market data: `Software Engineer`
(the single largest specialization in the whole dataset, 776 postings) isn't documented at all,
and neither are `Security Engineer` (189), `Data Scientist` (122), or the whole pre-sales/
customer-facing engineering cluster (Solutions Engineer + Forward Deployed + Solutions Architect
+ Support + Customer Engineer = 565 postings combined) that the Requirements Taxonomy's own
skill_group table already recognizes structurally but `specialization` never named formally.

## Three real inconsistencies found, not just gaps

1. **Technical Program Manager** (57 postings under Product Manager) also appeared heavily in
   the LLM-decided `other` bucket under near-identical phrasing in earlier research this session
   (`Technical Program Manager` 6, `Staff Technical Program Manager` 5) — the same title stem
   landing in two different outcomes depending on call, not a stable rule.
2. **Data Scientist** — already found and documented as a real inconsistency (27 of 30 title
   variants land `Engineer`/`Data Scientist`; 3 with an infrastructure/safety/identity-adjacent
   qualifier land `other`).
3. **Engineering Manager** (118 postings) appears as a `specialization` value directly, which
   looks like the same specialization/track conflation the 2026-08-11 redesign fixed for `level`
   (`manager` used to wrongly appear as a level rung) — `track = management` already exists
   specifically to capture this, and letting it leak into `specialization` too undermines that
   fix's own reasoning.

## Outcome
See `outcomes/understand-market-health-before-searching.md` — "they can identify which roles and
skills are in demand vs. declining" depends directly on specialization granularity; this is a
refinement of an existing outcome, not a new one, and no success criteria need changing.

source: user-feedback
date: 2026-09-18

> "what other roles in the tech industry would be worth tracking?" → (after a proposal
> covering the Engineer-category gap) → "ok, lets include them, this would need to be
> standardised and documented properly"

## Context
`scraping/itjobswatch.py`'s `ROLE_SLUGS` only tracked 3 roles (`product-owner`,
`ux-designer`, `product-manager`) — 2 of the platform's 3 job-posting taxonomy categories
(`classification.py`'s `ROLE_CATEGORIES = {"Designer", "Product Manager", "Engineer"}`) had
real coverage, but **Engineer had zero** despite being a core tracked category for job
postings. Proposed and confirmed 5 additions: `software-developer`, `devops-engineer`,
`data-engineer`, `full-stack-developer` (Engineer), `product-designer` (Designer) — each
verified to resolve on the real live site via WebFetch before being trusted (rank + vacancy
count quoted verbatim for each, not guessed):

| Slug | Rank | Vacancy count |
|---|---|---|
| software-developer | 147 | 1,486 |
| devops-engineer | 169 | 1,339 |
| data-engineer | 102 | 2,064 |
| full-stack-developer | 213 | 1,027 |
| product-designer | 718 | 86 |

User explicitly asked that adding tracked roles be "standardised and documented properly" —
i.e. not just a silent code edit, but a real, documented, repeatable procedure, the same way
`DATA_SOURCES.md` §5 already documents "add/retire a tracked company."

source: stakeholder-request
date: 2026-09-06

"I need the 'what we know' story to be more visual and make sure it has no repetition with
the others"

Current state: "What we know about the market" (`market-data-briefing`, rendered by
`DataStoryMessage.tsx`) is three prose paragraphs — "Market snapshot" (N jobs, M companies),
"What stands out" (largest role group, top skill group), "How to read this" (collected since
X). Almost every fact in it is **already shown on the "About this platform" welcome**: total
job openings, companies, collection start, the role-category breakdown, the largest role.

Meanwhile the backend already computes rich material the story ignores: top job titles, top
specializations, the full skills breakdown (must-have vs nice-to-have), compensation
disclosure rates (only ~6% of postings state a salary), and geography (top countries/cities).

Wanted: rebuild the story so it (1) shows the market substance the welcome doesn't — the
actual roles, skills, pay transparency, and locations — as **charts/bars, not prose**, and
(2) drops the inventory recap that duplicates the welcome.

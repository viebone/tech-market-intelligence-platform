source: user-feedback
date: 2026-09-11

See also: the new framework-level principle and skill this triggered —
`.claude/skills/data-legibility/SKILL.md` and `CLAUDE.md` (workspace root) — Rules for AI #10,
built the same session in direct response to this feedback.

Raw trigger:

> "one improvement. each data point needs to be explained in detail, for example: Companies
> with the most reported impact: what are those units, what is referring to? as a principle,
> data must be correctly explained, charts must have a title and subtitle when needed, units
> clearly explained, same whenever there are colours or shapes, it must be clear. we need a
> principle and a skill at framework level, all products must follow this basic principle."

Concrete example given: "Companies with the most reported impact" (Story 2 — Employment risk
across the market) states neither the unit ("impact" measured how?) nor what's being summed.

Real audit of this product's two data stories against the new principle (`StoryBlock.tsx`,
`RankedBarList.tsx`, `YearOnYearBars.tsx`, `DataStoryMessage.tsx`,
`EmploymentRiskStoryMessage.tsx` all read in full) found the same gap repeats across every
`RankedBarList`-based block in both stories:

- Story 2: "Companies with the most reported impact", "By country", "By sector" — all rank by
  `jobs_affected` (summed), never stated.
- Story 1: "The roles being hired", "Where the roles are" rank by posting count, never stated;
  "What employers ask for" ranks by mention count, never stated (though its must-have/opacity
  distinction does already carry a small caption — that one's compliant).
- `StoryBlock` (the shared block component every story uses) has no subtitle slot at all —
  only a `heading` and a bottom `qualifier` footnote, which currently carries a data-honesty
  caveat, not a stated unit.
- `YearOnYearBars`'s two-colour bar (`bg-gray-700` ghost = the prior year, `bg-indigo-500` =
  the current year) is documented in `design/visual-design.md`'s design spec but has **no
  legend rendered to the end user anywhere** — a real, independent colour-legibility gap,
  found during this audit, not mentioned in the original feedback.

"""
Shared plain-language definition wording — ONE place, so a data point's definition reads
identically wherever it's shown: a Data Story's own qualifier, and an MCP tool's `meta` for the
same figure (`design/visual-design.md` — Chart accessibility standard: "a data point's definition
wording should come from one place shared with the MCP tool meta").

Agreed 2026-09-26 between `changes/2026-09-26-story-5-tech-lens.md` (this file's first keys) and
`changes/2026-09-26-data-story-chart-variety.md` (adds its own key later) so neither change invents
a second mechanism. Rules:
- Pure constants. No imports, no database, no formatting logic — a value is the exact sentence(s)
  to show, nothing to fill in.
- Dotted, stable keys (`"<area>.<subject>.<aspect>"`), owned by whichever change first needed the
  wording; a later change only ADDS its own keys, never edits another change's key without its own
  change request.
- A key that is defined here but never referenced by any story or tool is dead text — the test
  suite (`tests/test_data_definitions.py`) fails the build on that, and on a story/tool that
  references a key not defined here.
"""

from __future__ import annotations

DEFINITIONS: dict[str, str] = {
    # backend/specs/market-health/api.md — Story 5, block "uk-tech-and-communications"
    # (changes/2026-09-26-story-5-tech-lens.md). Shown in the story's qualifier and in
    # get_trusted_statistics' meta.definitions whenever the "J" (information and communication)
    # series is part of the result.
    "ons.industry.J.breadth": (
        "Information and communication is the closest official group to tech, but it is broader "
        "— it also covers telecoms, publishing, film, TV and radio, alongside software and IT "
        "services. Engineering and research roles are counted in a different group (professional, "
        "scientific and technical activities)."
    ),
    # Same block. Shown whenever any ONS Vacancy Survey series is part of the result.
    "ons.vacancies.rounding": (
        "Estimates are published in whole thousands, so small moves in a group this size are "
        "within rounding. The survey leaves out employment agencies."
    ),
    # backend/specs/market-health/api.md — Story 3, "Pay block gains the full percentile spread"
    # (changes/2026-09-26-data-story-chart-variety.md). Shown in the "Typical pay by role" story
    # block's how-to-read line and in get_market_benchmark's meta.definitions, whenever any role
    # in the result carries salary data — the same sentence a person reads and an external AI is
    # told, so neither describes the chart's whisker/band/dot differently.
    "benchmark.salary.percentiles": (
        "Each bar spans the middle 80% of advertised salaries for that role; the shaded band is "
        "the middle 50%; the dot is the median."
    ),
}

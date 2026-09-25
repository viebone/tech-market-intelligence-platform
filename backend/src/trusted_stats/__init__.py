"""
Trusted external statistics — published statistics from trusted institutions, standardised into one store.

NOT named `statistics/`: that is a Python standard-library module and a local package of that name would
shadow it. Spec: backend/specs/trusted-statistics/api.md; map and recipe: backend/TRUSTED_STATISTICS.md.

**Add a new source — a recipe (full version in backend/TRUSTED_STATISTICS.md):**
  1. Pass the trust bar; write the evidence file with the licence quotes read off the publisher's own page.
  2. Register SOURCE_LICENCES[<source>] and TRUSTED_PUBLISHERS[<source>] — in the same commit as the adapter
     (tests/test_source_licences.py and tests/test_trusted_stats.py fail on one without the other).
  3. Implement the adapter (discover / pure parse / validate) and add it to ALL_STATISTICS_ADAPTERS below.
  4. Test parse() against a small trimmed REAL file, with expected values from the publisher's own figures.
"""

from trusted_stats.base import (
    FetchedStatistic,
    LayoutError,
    ParsedRelease,
    PoliteFetcher,
    ReleaseRef,
    SeriesDefinition,
    StatisticsAdapter,
    StatisticsConfigError,
    StatisticsFetchError,
    ingest_adapter,
    is_due_from_last_run,
)
from trusted_stats.ons_vacancy import OnsVacancySurveyAdapter
from trusted_stats.registry import TRUSTED_PUBLISHERS, TrustedPublisher

ALL_STATISTICS_ADAPTERS: list[StatisticsAdapter] = [
    OnsVacancySurveyAdapter(),
]

__all__ = [
    "ALL_STATISTICS_ADAPTERS", "FetchedStatistic", "LayoutError", "OnsVacancySurveyAdapter", "ParsedRelease",
    "PoliteFetcher", "ReleaseRef", "SeriesDefinition", "StatisticsAdapter", "StatisticsConfigError",
    "StatisticsFetchError", "TRUSTED_PUBLISHERS", "TrustedPublisher", "ingest_adapter", "is_due_from_last_run",
]

"""
Registry of every live scraped market-benchmark adapter, mirroring
sources/__init__.py's ALL_SOURCE_ADAPTERS pattern — with one deliberate
difference: entries here are adapter *classes*, not pre-built instances.
Every ScrapedSourceAdapter needs a RobotsCacheStore + PageCacheStore at
construction time (they're Postgres-backed — scraping_storage.py — and
PoliteScraper deliberately never imports db.py itself, see scraping/base.py's
module docstring), so ingest_scraped_sources.py constructs each adapter with
the real stores at run time instead of this module doing it eagerly at
import time. Job-posting adapters (sources/__init__.py) and employment-event
adapters (employment_events/__init__.py) have no such dependency, hence the
difference.

**Add a new scraped source — a recipe, no other file needs to change:**
  1. Create `scraping/{name}.py` implementing the `ScrapedSourceAdapter`
     protocol (base.py) — a `name: str`, a constructor accepting
     `(robots_store, page_store)`, and a `fetch(self) -> ScrapeResult` method.
     Get the target's own scraping-permission terms in writing first — this
     mechanism exists because IT Jobs Watch explicitly granted it, not as a
     default right to scrape anything with no API.
  2. Import the class and add it to `ALL_SCRAPED_SOURCE_ADAPTERS` below.
  3. Update `DATA_SOURCES.md` §3b/§7 (the standing source-documentation
     requirement, same as every other source category in this codebase).
"""

from scraping.base import (
    FetchedMarketObservation,
    FetchedSkillAssociation,
    PoliteScraper,
    RobotsDisallowedError,
    ScrapedSourceAdapter,
    ScraperConfigError,
    ScrapeFetchError,
    ScrapeResult,
)
from scraping.itjobswatch import ItJobsWatchAdapter
from source_licences import (
    LicenceNotRegisteredError,
    SourceLicence,
    get_licence,
    is_commercial_mode,
    is_source_usable,
)

ALL_SCRAPED_SOURCE_ADAPTERS: list[type[ScrapedSourceAdapter]] = [
    ItJobsWatchAdapter,
]

# How often (minimum) a source's adapter may actually run — Business Logic
# rule 8, enforced via IngestionRun in scraping_storage.py. A per-adapter
# override belongs here, keyed by adapter name, not hardcoded into
# ingest_scraped_sources.py — this source's own granted permission implies
# weekly; a future source's own terms could reasonably differ.
MIN_RUN_INTERVAL_DAYS: dict[str, int] = {
    "itjobswatch": 7,
}
DEFAULT_MIN_RUN_INTERVAL_DAYS = 7

__all__ = [
    "ALL_SCRAPED_SOURCE_ADAPTERS",
    "DEFAULT_MIN_RUN_INTERVAL_DAYS",
    "FetchedMarketObservation",
    "FetchedSkillAssociation",
    "LicenceNotRegisteredError",
    "MIN_RUN_INTERVAL_DAYS",
    "PoliteScraper",
    "RobotsDisallowedError",
    "ScrapedSourceAdapter",
    "ScraperConfigError",
    "ScrapeFetchError",
    "ScrapeResult",
    "SourceLicence",
    "get_licence",
    "is_commercial_mode",
    "is_source_usable",
]

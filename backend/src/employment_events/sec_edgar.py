"""
SEC EDGAR full-text search — 8-K Item 2.05 filings ("Costs Associated with
Exit or Disposal Activities"), the SEC's own structured classification for a
material restructuring/exit-activity disclosure by a US-listed company.

Added 2026-09-11 (research/2026-09-11-employment-event-data-sources.md —
"Expanded source catalog"). Confirmed live via real, unauthenticated calls
during this adapter's own construction — not a guess:
  Base URL:  https://efts.sec.gov/LATEST/search-index
  Auth:      none — but a descriptive User-Agent header is REQUIRED by SEC's
             own fair-access policy (a generic/missing one risks throttling)
  Params:    q (full-text query), forms, startdt/enddt (YYYY-MM-DD), from
             (pagination offset, page size 10, Elasticsearch-style)
  Response:  {"hits": {"total": {...}, "hits": [{"_source": {...}}, ...]}}
  Real example _source: {"ciks": ["0001618732"], "display_names":
    ["Nutanix, Inc.  (NTNX)  (CIK 0001618732)"], "file_date": "2026-08-04",
    "form": "8-K", "adsh": "0001193125-26-331661", "biz_states": ["CA"],
    "sics": ["7372"], "items": ["2.05"]}

This is the only source so far with a genuinely real company name straight
from the record (`display_names[0]`, cleaned of its trailing ticker/CIK
suffix) — unlike UK Companies House's Streaming API, which gives only a bare
company number (employment_events/companies_house.py).

**Full-text search is a recall net, `items` is the real filter.** EDGAR's
full-text search has no direct "filter by SEC item number" query param, so
this adapter searches a handful of restructuring-language phrases to cast a
wide net, then keeps only hits whose structured `items` field actually
contains `"2.05"` — the SEC's own classification, not a text-match guess.
A hit matching the search terms but not carrying item 2.05 is discarded
(e.g. TrueBlue's Q2 earnings press release above, which happened to mention
"workforce" in an unrelated context and doesn't carry 2.05).

**No jobs_affected, no sector.** The search index's metadata doesn't size
headcount impact (would need parsing the filing's actual text — out of
scope here) or name an industry directly — `sics` is a SIC code, not a
sector name, and mapping the ~1,000-code SIC table honestly is its own
future task, not attempted here with a partial/guessed mapping.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, timedelta

import httpx

from employment_events.base import EVENT_TYPES, FetchedEmploymentEvent

logger = logging.getLogger(__name__)

BASE_URL = "https://efts.sec.gov/LATEST/search-index"
PAGE_SIZE = 10
MAX_PAGES_PER_RUN = 5  # generous for a 30-day window's typical volume

# Recall net — cast wide, then filtered down to real Item 2.05 filings only
# (see module docstring). Deliberately several phrasings, not one, since
# full-text search can't be trusted alone to find every real filing.
_SEARCH_TERMS = (
    '"workforce reduction" OR "reduction in force" OR "restructuring plan" '
    'OR "headcount reduction" OR "cost reduction plan" OR "workforce '
    'restructuring"'
)

# SEC's own structured classification for a material restructuring/exit
# disclosure — see https://www.sec.gov/files/form8-k.pdf, Item 2.05.
_RESTRUCTURING_ITEM = "2.05"

_DISPLAY_NAME_SUFFIX_RE = re.compile(r"\s*\([A-Z.]{1,6}\)\s*\(CIK\s*\d+\)\s*$")


def _clean_company_name(display_name: str) -> str:
    """'Nutanix, Inc.  (NTNX)  (CIK 0001618732)' -> 'Nutanix, Inc.'"""
    return _DISPLAY_NAME_SUFFIX_RE.sub("", display_name).strip()


def _map_hit(source: dict) -> FetchedEmploymentEvent | None:
    ciks = source.get("ciks") or []
    adsh = source.get("adsh")
    display_names = source.get("display_names") or []
    file_date = source.get("file_date")

    if not (ciks and adsh and display_names and file_date):
        logger.warning(
            "sec_edgar: hit missing ciks/adsh/display_names/file_date — "
            "skipped, not guessed. Raw _source: %r", source,
        )
        return None

    cik = ciks[0]
    biz_states = source.get("biz_states") or []
    region = biz_states[0] if biz_states else None

    return FetchedEmploymentEvent(
        source_ref=adsh,
        company_raw=_clean_company_name(display_names[0]),
        event_date=file_date,
        event_type="restructuring",
        jobs_affected=None,  # not sized by this index — see module docstring
        country="US",
        region=region,
        sector=None,  # SIC code present but not honestly mappable here yet
        source_url=(
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{adsh.replace('-', '')}/"
        ),
        confidence="confirmed",  # a mandatory regulatory disclosure
        raw_response=source,
    )


class SecEdgarAdapter:
    name = "sec_edgar_8k"

    def fetch(self) -> list[FetchedEmploymentEvent]:
        date_to = date.today()
        date_from = date_to - timedelta(days=30)
        # Required by SEC's fair-access policy — identifies the caller (a
        # real contact, not a credential); a generic/placeholder value risks
        # throttling and doesn't meet the policy's actual intent. Set
        # SEC_EDGAR_CONTACT to "Your Org Name your-real-email@example.com"
        # before running this in production — the fallback below is only
        # for local dev/testing and should not be relied on long-term.
        contact = os.environ.get(
            "SEC_EDGAR_CONTACT", "TechMarketIntelligencePlatform (set SEC_EDGAR_CONTACT)"
        )
        headers = {"User-Agent": contact}

        seen_adsh: set[str] = set()
        results: list[FetchedEmploymentEvent] = []

        with httpx.Client(timeout=30.0, headers=headers) as client:
            for page in range(MAX_PAGES_PER_RUN):
                response = client.get(
                    BASE_URL,
                    params={
                        "q": _SEARCH_TERMS,
                        "forms": "8-K",
                        "startdt": date_from.isoformat(),
                        "enddt": date_to.isoformat(),
                        "from": page * PAGE_SIZE,
                    },
                )
                response.raise_for_status()
                hits = response.json().get("hits", {}).get("hits", [])
                if not hits:
                    break

                for hit in hits:
                    source = hit.get("_source") or {}
                    items = source.get("items") or []
                    if _RESTRUCTURING_ITEM not in items:
                        continue  # matched the search terms, but not a real 2.05 filing

                    adsh = source.get("adsh")
                    if not adsh or adsh in seen_adsh:
                        continue  # dedupe: one event per filing, not per exhibit file
                    seen_adsh.add(adsh)

                    event = _map_hit(source)
                    if event is not None:
                        results.append(event)

                if len(hits) < PAGE_SIZE:
                    break  # last page

        assert all(e.event_type in EVENT_TYPES for e in results)
        return results

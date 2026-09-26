"""
Personio XML job-feed adapter.

Public, unauthenticated GET endpoint per company (Personio account subdomain):
    https://{company}.jobs.personio.de/xml

Personio's own docs say no credentials are needed ("Do I need credentials to
access the XML feed? No" — support.personio.de FAQ on XML job integration,
read 2026-09-26) and that the customer switches the feed on themselves
(Settings > Recruiting > Career Page > Enable XML feed) to publish jobs on
their own website. Personio recommends syncing at most hourly; this platform
fetches once per daily run. `.jobs.personio.de` and `.jobs.personio.com` serve
the identical feed (verified 2026-09-26 on three boards) — `.de` is used.

**The response is XML, not JSON.** Each `<position>` is converted to a dict by
`_position_to_dict` so `raw_response` (a JSON column) stays the source's own
shape, verbatim — every child element kept under its own name, nothing renamed
or dropped. Repeated `<office>` elements under `<additionalOffices>` become a
list; the nested `<jobDescriptions>/<jobDescription>` blocks become a list of
`{"name", "value"}` (the value is the HTML body, kept as published).

**An unknown or disabled slug is a redirect, not a 404.** A board that doesn't
exist (or whose feed the customer has switched off) answers `307` to
`https://personio.com`. `PacedFetcher` doesn't follow redirects and treats a
non-retryable 3xx as failure, so this surfaces as `SourceFetchError` for that
one company — never silently parsed as an empty board, and never followed to
Personio's marketing site. A board that exists but has no open roles returns a
valid `<workzag-jobs/>` with zero positions — an ordinary empty result.

Real data-shape facts found and handled, not assumed (2026-09-26, three boards):
- There is **no country field and no salary field** — only free-text `<office>`
  city strings ("Munich", "Berlin - Mitte", "Remote, UK"). `city` is the first
  office as published; `country` is left None rather than inferred from a city.
- The feed's own job-detail values are always English but the job *text*
  (title, description) is in whatever language the job was published in — real
  boards mix English (Stark) and German ("m/w/*" titles, Capmo). Downstream
  classification must cope with both; see the change request's Step 8.
- Boards can carry stale postings: `choco`'s feed still lists roles created in
  2017. `createdAt` is kept in `raw_response`; nothing here filters on it.
- A position's own `<name>` is a direct child of `<position>`; `<name>` also
  appears inside each `<jobDescription>`, which is why parsing reads direct
  children only.

Security: the feed is third-party XML, so a document declaring a DTD or entity
is rejected outright (no billion-laughs / external-entity surface) and the body
is size-capped.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from sources.base import FetchedPosting, PacedFetcher, SourceFetchError

logger = logging.getLogger(__name__)

BASE_URL = "https://{company}.jobs.personio.de/xml"

# Largest real feed seen so far is ~1.8 MB (Stark, 131 positions with full
# descriptions). 15 MB leaves ample headroom while bounding memory.
MAX_FEED_BYTES = 15 * 1024 * 1024

USER_AGENT = "tmip-job-ingest/1.0 (public job-market research; polite, 1 request per second)"

# Curated, not exhaustive — every slug below was validated 2026-09-26 by
# fetching its real feed and content-inspecting the postings to confirm they
# belong to the intended company (same discipline as every other adapter's
# COMPANIES list, EMPLOYER_PANEL.md). Not added: `choco` (feed lists only
# roles created in 2017 — stale), `bounti` (3 sales roles, employer not
# verifiable from its own postings), `moss` (real board, 0 open roles).
COMPANIES: list[str] = [
    "personio",   # Personio itself (Munich HQ)
    "stark",      # STARK defence technology (Munich/Berlin, ~130 roles)
    "capmo",      # Capmo, construction-site software (Munich/Berlin)
]


def _position_to_dict(position: ET.Element) -> dict:
    """One <position> → a plain dict, every direct child kept under its own name."""
    result: dict = {}
    for child in position:
        if child.tag == "additionalOffices":
            result["additionalOffices"] = [(o.text or "").strip() for o in child.findall("office")]
        elif child.tag == "jobDescriptions":
            result["jobDescriptions"] = [
                {
                    "name": (jd.findtext("name") or "").strip(),
                    "value": (jd.findtext("value") or "").strip(),
                }
                for jd in child.findall("jobDescription")
            ]
        else:
            result[child.tag] = (child.text or "").strip()
    return result


def parse_feed(company: str, xml_bytes: bytes) -> list[FetchedPosting]:
    """
    Parse one Personio XML feed into FetchedPostings, one per distinct position
    id. Raises SourceFetchError on a malformed or unsafe document — that
    company fails alone, never the run.
    """
    if len(xml_bytes) > MAX_FEED_BYTES:
        raise SourceFetchError(f"personio feed for {company!r} exceeds {MAX_FEED_BYTES} bytes")
    head = xml_bytes.lower()
    if b"<!doctype" in head or b"<!entity" in head:
        raise SourceFetchError(f"personio feed for {company!r} declares a DTD/entity — refusing to parse")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise SourceFetchError(f"personio feed for {company!r} is not valid XML: {exc}") from exc
    if root.tag != "workzag-jobs":
        raise SourceFetchError(f"personio feed for {company!r} has unexpected root <{root.tag}>")

    seen_ids: set[str] = set()
    results: list[FetchedPosting] = []
    for position in root.findall("position"):
        job = _position_to_dict(position)
        job_id = job.get("id")
        if not job_id or job_id in seen_ids:
            continue
        seen_ids.add(job_id)
        results.append(FetchedPosting(
            source_ref=f"{company}/{job_id}",
            company=company,
            title=job.get("name", ""),
            raw_response=job,
            # No country or salary in this feed (see module docstring) — city
            # is the first office exactly as published, country stays None.
            country=None,
            city=job.get("office") or None,
        ))
    return results


class PersonioAdapter:
    name = "personio"
    companies = COMPANIES

    def __init__(self) -> None:
        self._fetcher = PacedFetcher(source_name="personio")

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        with httpx.Client(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            response = self._fetcher.get(client, BASE_URL.format(company=company))
        return parse_feed(company, response.content)

"""
Source licence registry — covers every external data source this product
draws on, not only scraped ones. Moved here 2026-09-16 (was
scraping/licences.py) once the admin licensing view surfaced that the
employment-event API sources (SEC EDGAR, UK Companies House, Eurofound ERM,
US WARN via WARN Firehose) have exactly the same "what are we actually
allowed to do with this" question as a scraped source — a registry named
`scraping.licences` was the wrong home for that. See
`research/2026-09-16-all-sources-licensing-status.md`.

Every adapter (scraped or API-based) looks up its own licence/attribution
from here; there is no code path that invents a licence string locally. An
unregistered source is a hard error, not a silent gap — same "refuse rather
than proceed with a guess" discipline `scraping/base.py`'s `SCRAPER_CONTACT`
check already applies to identification.

`scraping/base.py`'s run-cadence/`robots.txt`/pacing constraints (Rule 13,
`polite-scraping-review`) stay scraping-specific — an API-based source like
SEC EDGAR doesn't need `robots.txt` compliance or a page cache. Only the
licence-registry concept generalizes; this module owns that piece alone.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class LicenceNotRegisteredError(Exception):
    """Raised when a source has no entry here at all. Adding a new source —
    scraped or API-based — means registering its licence here first, never
    inventing a placeholder inline at the call site."""


@dataclass(frozen=True)
class SourceLicence:
    source: str
    licence: str                  # the confirmed variant, or an explicitly-labelled "unconfirmed" placeholder
    attribution_text: str         # the exact citation string to use wherever this data is shown/republished
    licence_url: str
    confirmed: bool                # True only once a human has read the source's own licence statement
    permits_commercial_use: bool   # see "Commercial-use kill switch," below


# itjobswatch: CONFIRMED 2026-09-16 — read directly off itjobswatch.co.uk's own
# copyright page (https://www.itjobswatch.co.uk/copyright.aspx), cross-checked
# against a second independent search result. Real quoted wording: "Real-time
# IT job market trends and actionable insights by IT Jobs Watch is licensed
# under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0
# International License." Attribution requirement (quoted): "All extracts
# must include attribution by including and clearly stating Source IT Jobs
# Watch." One explicit exclusion, worth recording even though it doesn't
# apply to what this adapter scrapes: "The licence excludes job vacancy
# listings and other third-party material" — this adapter only ever touches
# aggregate market-trend stats (rank, salary percentiles, skill associations),
# never a vacancy listing, so the exclusion isn't in play here, but it's
# recorded so nobody assumes the licence covers *everything* on the site.
#
# sec_edgar_8k / companies_house_insolvency / eurofound_erm / us_warn: added
# 2026-09-16, per research/2026-09-16-existing-source-licensing-audit.md —
# read the full audit there for how each was checked and its confidence
# level. Two are confirmed to high confidence (SEC EDGAR, Companies House);
# Eurofound ERM and US WARN (via WARN Firehose) are deliberately left
# `confirmed=False` — not because there's a known problem, but because
# neither was checked to the same standard as the other two (Eurofound's own
# copyright page rate-limited on direct fetch; WARN Firehose's own Terms of
# Service, as applied to this specific account's actual use, hasn't been
# reviewed by the operator yet). `confirmed=False` here is the honest state,
# not a downgrade — see `overall_status()`, below, for how this renders.
SOURCE_LICENCES: dict[str, SourceLicence] = {
    "itjobswatch": SourceLicence(
        source="itjobswatch",
        licence="CC BY-NC-SA 4.0",
        attribution_text="Source: IT Jobs Watch (itjobswatch.co.uk)",
        licence_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        confirmed=True,
        permits_commercial_use=False,  # the "NC" clause — see below
    ),
    "sec_edgar_8k": SourceLicence(
        source="sec_edgar_8k",
        licence="Public domain (U.S. government work)",
        attribution_text="Source: SEC EDGAR (sec.gov)",
        licence_url="https://www.sec.gov/privacy",
        confirmed=True,
        permits_commercial_use=True,
    ),
    "companies_house_insolvency": SourceLicence(
        source="companies_house_insolvency",
        licence="Open Government Licence v3.0",
        attribution_text="Contains public sector information licensed under the Open Government Licence v3.0 — Companies House",
        licence_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        confirmed=True,
        permits_commercial_use=True,
    ),
    "eurofound_erm": SourceLicence(
        source="eurofound_erm",
        licence="EU reuse policy (attribution required, no distortion) — not independently re-confirmed against eurofound.europa.eu's own page",
        attribution_text="Source: Eurofound European Restructuring Monitor (eurofound.europa.eu)",
        licence_url="https://www.eurofound.europa.eu/en/about-eurofound/legal-and-data-protection-notices",
        confirmed=False,  # medium confidence only — see module docstring
        permits_commercial_use=True,
    ),
    "us_warn": SourceLicence(
        source="us_warn",
        licence="Underlying WARN Act data: public record, no copyright. WARN Firehose's own Terms of Service separately restrict redistribution/resale of raw API access or bulk exports — this platform's actual use against those terms is not yet reviewed",
        attribution_text="Source: WARN Firehose (warnfirehose.com), derived from public WARN Act filings",
        licence_url="https://www.warnfirehose.com/terms",
        confirmed=False,  # our specific use hasn't been checked against WARN Firehose's actual ToS
        permits_commercial_use=True,
    ),
}

# *** The "NC" (NonCommercial) clause above, and why it now has a real switch. ***
# TMIP has a Premium paid plan tier (mcp-access). CC BY-NC-SA 4.0 permits use
# only for non-commercial purposes. Nothing today violates this — this data
# isn't surfaced anywhere yet — but the day this product actually starts
# charging for anything, a source like this one needs to stop being used
# automatically, not "whenever someone remembers." That's what
# TMIP_COMMERCIAL_MODE / is_source_usable(), below, are for.


def get_licence(source: str) -> SourceLicence:
    """
    The one lookup every adapter (scraped or API-based) uses. Raises
    LicenceNotRegisteredError for an unregistered source — never falls back
    to a bare "Creative Commons"/"public domain" or any other invented
    string.
    """
    try:
        return SOURCE_LICENCES[source]
    except KeyError:
        raise LicenceNotRegisteredError(
            f"No licence registered for source {source!r} — register it in "
            f"source_licences.py's SOURCE_LICENCES before this adapter can produce data."
        ) from None


# ---------------------------------------------------------------------------
# Commercial-use kill switch — added 2026-09-16
# (research/2026-09-16-commercial-mode-kill-switch.md). One env var, flipped
# once, the day this product actually starts making money — everything
# downstream of it (ingestion today; any future query/display function)
# automatically stops using a source whose licence doesn't confirm the
# right to use it commercially. Nobody has to remember to go source-by-
# source and turn things off by hand.
#
# Deliberately conservative on "don't know": an *unconfirmed* licence is
# treated the same as "doesn't permit commercial use" once commercial mode
# is on — "we haven't checked" is not the same as "we're allowed to."
# ---------------------------------------------------------------------------

_TRUE_STRINGS = {"1", "true", "yes", "on"}


def is_commercial_mode() -> bool:
    """
    True once this product is actually monetized — flip TMIP_COMMERCIAL_MODE
    to a real value in the deployment's env (backend/.env.example documents
    it) when that day comes. Defaults to False (not commercial) so nothing
    changes until someone deliberately turns this on.
    """
    return os.environ.get("TMIP_COMMERCIAL_MODE", "false").strip().lower() in _TRUE_STRINGS


def is_source_usable(source: str) -> bool:
    """
    The one check every ingestion path (today) and every future query/
    display function (per backend/specs/scraped-data-sources/api.md's
    forward-binding requirement) must call before using data from `source`.

    Not in commercial mode: always True — nothing changes from how this
    product operates today.

    In commercial mode: True only if the source's licence is BOTH confirmed
    AND explicitly marked as permitting commercial use. A source this
    product has never registered a licence for at all still raises
    LicenceNotRegisteredError (via get_licence) rather than silently
    passing — the same "refuse rather than guess" discipline as everywhere
    else in this module.
    """
    if not is_commercial_mode():
        return True
    licence = get_licence(source)
    return licence.confirmed and licence.permits_commercial_use


# ---------------------------------------------------------------------------
# Overall status — added 2026-09-16, per explicit request: "list all the
# sources, and put pending if not confirmed or not licensed if cannot be
# used." A single three-value status, for display (the admin licensing view)
# rather than a pair of separate booleans a reader has to combine themselves.
# ---------------------------------------------------------------------------

def overall_status(source: str) -> str:
    """
    'pending'      — licence not yet confirmed. We genuinely don't know yet
                     — never shown as if it were resolved either way.
    'not_licensed' — confirmed, but this source cannot currently be used
                     (is_source_usable() is False — i.e. commercial mode is
                     on and this licence doesn't clear it). A real, active
                     conflict, not a "maybe."
    'licensed'     — confirmed, and currently fine to use.

    As of 2026-09-16, with TMIP_COMMERCIAL_MODE off, no source can be
    'not_licensed' — that state only becomes reachable once the switch is
    on and a confirmed-but-non-commercial licence (e.g. itjobswatch's) is
    actually in conflict with it.
    """
    licence = get_licence(source)
    if not licence.confirmed:
        return "pending"
    if not is_source_usable(source):
        return "not_licensed"
    return "licensed"

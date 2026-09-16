"""
Source licence registry — Tech Decisions: "Licence registry — a hard
dependency, not an adapter-local constant". Every scraped-source adapter
looks up its own licence/attribution from here; there is no code path to
construct a FetchedMarketObservation/FetchedSkillAssociation with a licence
string an adapter invented locally. An unregistered source is a hard error,
not a silent gap — same "refuse rather than proceed with a guess" discipline
scraping/base.py's SCRAPER_CONTACT check already applies to identification.

Added 2026-09-16 (research/2026-09-16-scraping-good-practices-refinement.md),
replacing a per-adapter hardcoded placeholder string.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class LicenceNotRegisteredError(Exception):
    """Raised when an adapter's source has no entry here at all. Adding a
    new scraped source means registering its licence here first — never an
    adapter inventing its own placeholder inline."""


@dataclass(frozen=True)
class SourceLicence:
    source: str
    licence: str                  # the confirmed variant, or an explicitly-labelled "unconfirmed" placeholder
    attribution_text: str         # the exact citation string to use wherever this data is shown/republished
    licence_url: str
    confirmed: bool                # True only once a human has read the source's own licence statement
    permits_commercial_use: bool   # added 2026-09-16 — see "Commercial-use kill switch," below


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
SOURCE_LICENCES: dict[str, SourceLicence] = {
    "itjobswatch": SourceLicence(
        source="itjobswatch",
        licence="CC BY-NC-SA 4.0",
        attribution_text="Source: IT Jobs Watch (itjobswatch.co.uk)",
        licence_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        confirmed=True,
        permits_commercial_use=False,  # the "NC" clause — see below
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
    The one lookup every scraped-source adapter uses. Raises
    LicenceNotRegisteredError for an unregistered source — never falls back
    to a bare "Creative Commons" or any other invented string.
    """
    try:
        return SOURCE_LICENCES[source]
    except KeyError:
        raise LicenceNotRegisteredError(
            f"No licence registered for source {source!r} — register it in "
            f"scraping/licences.py's SOURCE_LICENCES before this adapter can produce data."
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

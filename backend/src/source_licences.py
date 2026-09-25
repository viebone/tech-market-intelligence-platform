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
    permits_commercial_use: bool   # informational — does the licence itself say commercial use is OK?
                                    # Feeds a human's decision on `rejected`, below; does not by itself
                                    # block anything (see "Per-source switch," below, for why).
    rejected: bool = False          # added 2026-09-16 — the ONE thing that actually blocks use. An
                                     # explicit, git-tracked, human decision — "we reviewed this
                                     # source and decided its data can't be used" — never inferred
                                     # automatically from confirmed/permits_commercial_use/commercial
                                     # mode. Defaults to False: every source is usable until someone
                                     # deliberately says otherwise. See "Per-source switch," below.
    data_summary: str = ""         # added 2026-09-16 — plain-language "what do we actually take from
                                    # this source" (field-level detail lives in DATA_SOURCES.md; this is
                                    # the one-line version, kept next to the licence itself so nobody has
                                    # to cross-reference two files to answer "is this specific data covered")


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
        data_summary="Aggregate UK IT market stats only — demand rank, vacancy share, salary percentiles, weighted role/skill associations. No individual postings, no PII.",
    ),
    "sec_edgar_8k": SourceLicence(
        source="sec_edgar_8k",
        licence="Public domain (U.S. government work)",
        attribution_text="Source: SEC EDGAR (sec.gov)",
        licence_url="https://www.sec.gov/privacy",
        confirmed=True,
        permits_commercial_use=True,
        data_summary="Per-filing: company name, filing date, CIK, accession number, US state, SEC's own Item 2.05 classification. Filing metadata only, not the filing's full text.",
    ),
    "companies_house_insolvency": SourceLicence(
        source="companies_house_insolvency",
        licence="Open Government Licence v3.0",
        attribution_text="Contains public sector information licensed under the Open Government Licence v3.0 — Companies House",
        licence_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        confirmed=True,
        permits_commercial_use=True,
        data_summary="Per-case: company number (no company name — the stream doesn't provide one), case dates, insolvency type. No PII beyond the public company register.",
    ),
    "eurofound_erm": SourceLicence(
        source="eurofound_erm",
        licence="EU reuse policy (attribution required, no distortion) — not independently re-confirmed against eurofound.europa.eu's own page",
        attribution_text="Source: Eurofound European Restructuring Monitor (eurofound.europa.eu)",
        licence_url="https://www.eurofound.europa.eu/en/about-eurofound/legal-and-data-protection-notices",
        confirmed=False,  # medium confidence only — see module docstring
        permits_commercial_use=True,
        data_summary="Per-event: company name, event date, restructuring type, sector, country, jobs affected. Full CSV row kept verbatim in raw_response.",
    ),
    "us_warn": SourceLicence(
        source="us_warn",
        licence="Underlying WARN Act data: public record, no copyright. WARN Firehose's own Terms of Service separately restrict redistribution/resale of raw API access or bulk exports — this platform's actual use against those terms is not yet reviewed",
        attribution_text="Source: WARN Firehose (warnfirehose.com), derived from public WARN Act filings",
        licence_url="https://www.warnfirehose.com/terms",
        confirmed=False,  # our specific use hasn't been checked against WARN Firehose's actual ToS
        permits_commercial_use=True,
        data_summary="Per-notice: company name, industry (mapped to sector), jobs affected, event date, US state, WARN Firehose's own source URL for the underlying filing.",
    ),
    # greenhouse / lever / ashby: added 2026-09-16, per direct research against each
    # platform's own official API docs (docs.greenhouse.io, github.com/lever/postings-api,
    # developers.ashbyhq.com) — none publish a formal data-reuse licence. All three
    # describe the API's *intended* use as "let the hiring company build its own careers
    # page" — but all three endpoints are public and unauthenticated (no API key), and
    # Lever's own docs go further, explicitly acknowledging third-party access: "Note
    # that all job postings in the published state are publicly viewable. These jobs may
    # be scraped by third parties." Greenhouse's and Ashby's docs neither state nor
    # prohibit third-party read access — recorded honestly as "no restriction found,"
    # not manufactured into a formal licence that doesn't exist. `confirmed=True` here
    # reflects that the *source's own current documentation* was actually read (not
    # guessed) — not that a formal reuse licence was found, because none exists.
    "greenhouse": SourceLicence(
        source="greenhouse",
        licence="No formal data-reuse licence published. Public, unauthenticated API — Greenhouse's own docs describe the intended use as letting the hiring company build its own careers page; third-party read access is neither addressed nor prohibited.",
        attribution_text="Job posting data originally published by the hiring company via its Greenhouse-hosted job board",
        licence_url="https://docs.greenhouse.io/job-board.html",
        confirmed=True,
        permits_commercial_use=True,
        data_summary="Per-posting: title, company, full raw job-object response (description HTML, location, department) kept verbatim; parsed country/city/salary where structured data is present.",
    ),
    "lever": SourceLicence(
        source="lever",
        licence="No formal data-reuse licence published. Public, unauthenticated API — Lever's own docs explicitly state: \"all job postings in the published state are publicly viewable. These jobs may be scraped by third parties.\"",
        attribution_text="Job posting data originally published by the hiring company via its Lever-hosted job board",
        licence_url="https://github.com/lever/postings-api",
        confirmed=True,
        permits_commercial_use=True,
        data_summary="Per-posting: title, company, full raw job-object response kept verbatim; parsed country/city/salary where structured data is present.",
    ),
    "ashby": SourceLicence(
        source="ashby",
        licence="No formal data-reuse licence published. Public, unauthenticated API — Ashby's own docs describe the intended use as letting the hiring company build its own careers page; third-party read access is neither addressed nor prohibited.",
        attribution_text="Job posting data originally published by the hiring company via its Ashby-hosted job board",
        licence_url="https://developers.ashbyhq.com/docs/public-job-posting-api",
        confirmed=True,
        permits_commercial_use=True,
        data_summary="Per-posting: title, company, full raw job-object response kept verbatim (includeCompensation=true, so structured pay data is often present); parsed country/city/salary where present.",
    ),
    # ons_vacancy_survey: CONFIRMED 2026-09-24 — read directly off ons.gov.uk's own dataset page for VACS03
    # ("All content is available under the Open Government Licence v3.0, except where otherwise stated"),
    # ONS's terms and conditions page, and the licence text at nationalarchives.gov.uk. The OGL permits
    # commercial and non-commercial use with acknowledgement of the source; ONS states no attribution wording
    # beyond the licence notice, so the OGL's own default wording plus the named source is used. The OGL does
    # NOT cover departmental logos — never use the ONS logo. First source of the "trusted external
    # statistics" category (trusted_stats/, backend/specs/trusted-statistics/api.md). Evidence with exact
    # quotes: research/2026-09-24-ons-licence-and-access-confirmation.md.
    "ons_vacancy_survey": SourceLicence(
        source="ons_vacancy_survey",
        licence="Open Government Licence v3.0",
        attribution_text=(
            "Source: Office for National Statistics — Vacancy Survey. "
            "Contains public sector information licensed under the Open Government Licence v3.0."
        ),
        licence_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        confirmed=True,
        permits_commercial_use=True,
        data_summary=(
            "Aggregate UK vacancy estimates by industry (SIC 2007) and size of business — levels in thousands, "
            "3-month rolling averages. No individual postings, no personal data."
        ),
    ),
    # workable: added 2026-09-19, per direct research against Workable's own
    # help docs (help.workable.com's "Using the Workable API to create a
    # careers page" article) — same "no formal licence, no restriction
    # found, not manufactured" honesty as greenhouse/ashby above. The public
    # widget endpoint requires no API key or login and is described as
    # existing specifically so any consumer (not just the hiring company)
    # can build a careers page from it.
    "workable": SourceLicence(
        source="workable",
        licence="No formal data-reuse licence published. Public, unauthenticated widget API — Workable's own docs describe the intended use as letting a company (or a third party building on its behalf) build a careers page from it; third-party read access is neither addressed nor prohibited.",
        attribution_text="Job posting data originally published by the hiring company via its Workable-hosted job board",
        licence_url="https://help.workable.com/hc/en-us/articles/115012771647-Using-the-Workable-API-to-create-a-careers-page",
        confirmed=True,
        permits_commercial_use=True,
        data_summary="Per-posting: title, company, full raw job-object response kept verbatim; parsed country/city where present. No structured salary field on this endpoint.",
    ),
}

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
# Per-source switch — revised 2026-09-16, per explicit direction:
# "we can switch on/off by sources. Just make sure that ingestions always
# work and that insights and other functionality always work unless we say
# license rejected. but in any case the ingestions can work until we say
# the opposite."
#
# Two independent lifecycles, never conflated:
#   1. INGESTION (collecting data) — always runs, for every registered
#      adapter, regardless of anything in this file. This module is never
#      consulted to decide whether to fetch — see ingest_scraped_sources.py.
#      Collecting has value on its own (internal analysis, a future
#      re-negotiated licence) independent of whether the data can currently
#      be *used*.
#   2. USE (a future chart, chat answer, MCP tool — anything that shows or
#      acts on this data) — gated by exactly one thing: `SourceLicence.rejected`.
#      Defaults to False, so every source is usable by default. The ONLY way
#      a source stops being usable is a human explicitly setting
#      `rejected=True` here, in this file — a deliberate, git-tracked,
#      reviewable decision, never an automatic inference from `confirmed`,
#      `permits_commercial_use`, or whether this product happens to be
#      monetized. Those two fields stay in the registry as context a human
#      reads *before* deciding whether to set `rejected` — they no longer
#      compute anything themselves.
#
# `TMIP_COMMERCIAL_MODE` is kept as a plain informational signal (surfaced
# in the admin view) — a reminder that "we're monetized now, go review
# sources" — not an automatic gate. Nothing flips `rejected` on its own.
# ---------------------------------------------------------------------------

_TRUE_STRINGS = {"1", "true", "yes", "on"}


def is_commercial_mode() -> bool:
    """
    Informational only — True once TMIP_COMMERCIAL_MODE is set in the
    deployment's env. Does not, by itself, block anything; see the module
    note above for why gating is `rejected`-only now. Surfaced in the admin
    view as a reminder to go review sources once this is true, not as a
    live filter.
    """
    return os.environ.get("TMIP_COMMERCIAL_MODE", "false").strip().lower() in _TRUE_STRINGS


def is_source_usable(source: str) -> bool:
    """
    The one check every future query/display function must call before
    using data from `source` (per backend/specs/scraped-data-sources/api.md's
    forward-binding requirement). Never called by ingestion — ingestion is
    not gated by this at all (see the module note above).

    True unless a human has explicitly set `rejected=True` for this source.
    A source this product has never registered a licence for at all still
    raises LicenceNotRegisteredError (via get_licence) rather than silently
    passing — the same "refuse rather than guess" discipline as everywhere
    else in this module.
    """
    return not get_licence(source).rejected


# ---------------------------------------------------------------------------
# Overall status — for display (the admin licensing view). A single
# three-value status rather than separate booleans a reader has to combine.
# ---------------------------------------------------------------------------

def overall_status(source: str) -> str:
    """
    'rejected' — a human has explicitly set `rejected=True` for this
                 source. Always wins, regardless of confirmation status —
                 an explicit decision is an explicit decision.
    'pending'  — not rejected, but licence not yet confirmed. We genuinely
                 don't know yet — never shown as if it were resolved.
    'licensed' — not rejected, and confirmed. Currently fine to use.

    As of 2026-09-16, no registered source has `rejected=True` — "we don't
    have any rejected just yet" is a true statement about the data, checked
    against the real registry, not assumed.
    """
    licence = get_licence(source)
    if licence.rejected:
        return "rejected"
    if not licence.confirmed:
        return "pending"
    return "licensed"

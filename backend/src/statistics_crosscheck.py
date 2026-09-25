"""
Cross-checks: the platform's own composition placed beside an official statistic.

Story 5's third movement ("how this compares with the roles we track"). The rules, from the spec
(backend/specs/trusted-statistics/api.md — rule 8 and §6):

- A cross-check is CONTEXT, NOT PROOF. Each function returns two independent, separately-labelled series of
  SHARES, each with its own denominator and its own named source. There is no difference, ratio, score or
  verdict anywhere in these payloads — deliberately; nothing downstream can display one.
- The platform side is restricted to postings with a RECORDED UK location, because ONS covers the UK only
  while the panel also holds US and EU employers. Most stored postings have NO country recorded (about
  72% at 2026-09-25), so the comparison states how many roles it covers and how many it cannot place.
- A role whose employer has no industry-group mapping (crosswalks.py) or no size band
  (employer_headcount.py) is counted in an explicit "not placed" figure — never dropped, never forced
  into a group.

Pure functions (`*_from_counts`, `ons_shares`) hold the arithmetic so it is testable without a database.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Both spellings exist in stored data ('GB' 587 rows, 'UK' 70 rows on 2026-09-25) — a known inconsistency in
# normalisation; this module treats both as the UK rather than silently dropping 70 rows.
UK_COUNTRY_CODES = ("GB", "UK")
TOTAL_SERIES = "AP2Y"


def platform_mix_from_counts(company_counts: dict[str, int], group_of) -> dict:
    """
    company_counts: postings per company (UK-located only). group_of(company) -> a group key, or None when the
    employer cannot be placed. Returns shares (%) of ALL UK-located postings, with the unplaced share stated.
    """
    total = sum(company_counts.values())
    groups: dict[str, int] = {}
    unplaced = 0
    for company, n in company_counts.items():
        g = group_of(company)
        if g is None:
            unplaced += n
        else:
            groups[g] = groups.get(g, 0) + n
    pct = (lambda n: round(100.0 * n / total, 2)) if total else (lambda n: None)
    return {
        "postings": total,
        "unplaced_count": unplaced,
        "unplaced_share_pct": pct(unplaced),
        "shares_pct": {g: pct(n) for g, n in sorted(groups.items())},
        "counts": dict(sorted(groups.items())),
    }


def ons_shares(observations_by_key: dict[str, float], total: float | None) -> dict[str, float]:
    """key -> share (%) of the all-vacancies total, from stored levels. Empty if the total is missing/zero."""
    if not total:
        return {}
    return {k: round(100.0 * v / total, 2) for k, v in observations_by_key.items()}


def _uk_company_counts() -> tuple[dict[str, int], int, int]:
    """(postings per company for UK-located roles, all-postings total, postings with no country recorded)."""
    from db import get_connection

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT company, count(*) FROM raw_postings WHERE country = ANY(%s) AND company IS NOT NULL GROUP BY company",
            (list(UK_COUNTRY_CODES),),
        ).fetchall()
        total, unknown = conn.execute("SELECT count(*), count(*) FILTER (WHERE country IS NULL) FROM raw_postings").fetchone()
    return {r[0]: int(r[1]) for r in rows}, int(total), int(unknown)


def _ons_side(dimension: str, key_of) -> dict:
    """Latest-period ONS shares by a dimension key, from the shared query function (usable-gated, named)."""
    from market_query import query_trusted_statistics_data

    total = query_trusted_statistics_data(dimension="total", publisher="ons_vacancy_survey")
    parts = query_trusted_statistics_data(dimension=dimension, publisher="ons_vacancy_survey")
    if not total["usable"]:
        return {"usable": False}
    if not total["statistics"]:
        return {"usable": True, "collected": False}
    t = total["statistics"][0]
    t_obs = t["observations"][0]
    levels: dict[str, float] = {}
    labels: dict[str, str] = {}
    for st in parts["statistics"]:
        obs = [o for o in st["observations"] if o["period_start"] == t_obs["period_start"]]
        k = key_of(st["series"])
        if k is not None and obs:
            levels[k] = obs[0]["value"]
            labels[k] = st["series"]["dimension"][dimension if dimension != "industry" else "industry"]["label"]
    return {
        "usable": True, "collected": True,
        "period_label": t_obs["period_label"], "period_start": t_obs["period_start"], "value_status": t_obs["value_status"],
        "total": t_obs["value"], "unit": t["series"]["unit"], "source": t["series"]["source"],
        "coverage_note": t["series"]["coverage_note"], "seasonal_adjustment": t["series"]["seasonal_adjustment"],
        "levels": levels, "labels": labels, "shares_pct": ons_shares(levels, t_obs["value"]),
    }


def industry_mix() -> dict:
    """Platform vs ONS by SIC 2007 SECTION. Industry only — see size_mix() for the size dimension."""
    from industries import industry_for
    from trusted_stats.crosswalks import CROSSWALK_VERSION, sic_section_for

    counts, total_postings, unknown_country = _uk_company_counts()
    platform = platform_mix_from_counts(counts, lambda c: sic_section_for(industry_for(c)))
    ons = _ons_side("industry", lambda s: (s["dimension"]["industry"]["code"]
                                           if s["dimension"]["industry"]["system"] == "SIC2007_section" else None))
    return {
        "platform": {**platform, "as_of": datetime.now(timezone.utc).isoformat(), "total_postings": total_postings,
                     "country_unknown_count": unknown_country, "crosswalk_version": CROSSWALK_VERSION,
                     "basis": "postings with a recorded UK location; industry via the versioned crosswalk"},
        "ons": ons,
    }


def size_mix() -> dict:
    """
    Platform vs ONS by employment size band. The platform band is DERIVED from a cited headcount range
    (employer_headcount.py) — most figures are WORLDWIDE headcounts, whereas ONS sizes the UK business, and ONS may
    size a subsidiary as its parent group (unverified). Both caveats belong beside any display of this.
    """
    from employer_headcount import AMBIGUOUS, size_band_for

    counts, total_postings, unknown_country = _uk_company_counts()
    platform = platform_mix_from_counts(counts, lambda c: (lambda b: None if b in (None, AMBIGUOUS) else b)(size_band_for(c)))
    ons = _ons_side("size_band", lambda s: s["dimension"]["size_band"]["code"])
    return {
        "platform": {**platform, "as_of": datetime.now(timezone.utc).isoformat(), "total_postings": total_postings,
                     "country_unknown_count": unknown_country,
                     "basis": "postings with a recorded UK location; size band derived from a cited (mostly worldwide) headcount"},
        "ons": ons,
    }

"""
The one place that words "how we read the market" and every estimate qualifier —
design/market-health/experience.md — How we read the market, Requirements estimates;
backend/specs/market-health/api.md — Business Logic — Sampling — Method text.

Every surface (welcome, stories, curated answers, chat prompt, reasoning trace, MCP, admin) calls
these functions. No other module may hold method wording, so the welcome, a story, chat and an
external AI can never tell different versions. {M} and {cap} are live values: the distinct-
company count (same as the welcome's Companies tile) and the per-role limits in
sampling_settings.py. A test asserts every surface renders identical text for the same inputs.

Plain words only (end-user-content): never "stratified", "weighted", "confidence interval".
"""

from __future__ import annotations

import sampling_settings as settings
from db import get_connection


def company_count() -> int | None:
    """Same definition as GET /api/market-health/welcome's inventory.companies. None if the
    database can't be read: reference surfaces (MCP get_taxonomy, server instructions) must keep
    working without it, so the text then says "the companies we follow" with no number."""
    try:
        with get_connection() as conn:
            return conn.execute(
                "SELECT count(DISTINCT company) FROM raw_postings WHERE company IS NOT NULL"
            ).fetchone()[0]
    except Exception:  # noqa: BLE001 — wording must never take a reference tool down
        return None


def _companies(m: int | None) -> str:
    return f"the {m:,} companies" if m is not None else "the companies"


def _cap_phrase() -> str:
    eng = settings.limit_for("Engineer")
    pm = settings.limit_for("Product Manager")
    if eng == pm:
        return f"up to {eng} job descriptions" if eng is not None else "every job description"
    def part(limit, label):
        return f"every {label} description" if limit is None else f"up to {limit} for {label} roles"
    return f"{part(eng, 'engineering')} and {part(pm, 'product')}"


def limit_per_group() -> int | None:
    return settings.limit_for("Engineer")


def one_line(m: int | None) -> str:
    return (f"We count every job posted by {_companies(m)} we follow, and read a fair sample of "
            "those job descriptions in full to see what employers ask for.")


def full(m: int | None) -> list[dict]:
    who = f"{m:,} companies" if m is not None else "the companies we follow"
    return [
        {"heading": "Who we follow",
         "text": f"The career pages of {who}, plus official sources for layoffs and national "
                 "vacancy figures. That's a large slice of tech hiring, not every employer."},
        {"heading": "Every job counted",
         "text": "Every job those companies post is counted and sorted by role, specialization and level. "
                 "Job numbers, trends and pay come from all of them."},
        {"heading": "A fair sample read in full",
         "text": "To see which skills and experience employers ask for, we read "
                 f"{_cap_phrase()} for each role and specialization every month, picked so that every job "
                 "has the same chance. For design roles we read every one."},
        {"heading": "How close the estimates are",
         "text": "Each skills figure says how many descriptions we read and how close the estimate is likely "
                 "to be, for example \"±12 pts\". That's enough to see which skills lead and how they compare. "
                 "When two skills are closer than that, we say they're level, and when a sample is too small "
                 "to tell, we say so."},
    ]


def method(m: int | None = None) -> dict:
    """The `method` object returned by the welcome and MCP get_taxonomy."""
    m = company_count() if m is None else m
    return {"one_line": one_line(m), "full": full(m), "company_count": m, "limit_per_group": limit_per_group()}


def full_as_markdown(m: int | None) -> str:
    """The full version as one answer (curated "How do you get these numbers?", chat prompt)."""
    return "\n\n".join(f"**{item['heading']}.** {item['text']}" for item in full(m))


def coverage_line(m: int | None) -> str:
    """meta.coverage on every MCP job-postings tool: counts are full counts, not estimates."""
    return (f"Full count of every job posted by {_companies(m)} this platform follows — not an "
            "estimate, and not the whole market.")


def requirements_method_note() -> str:
    """meta.method on requirements responses (MCP) — the sampling rule in words."""
    return (f"Skills and other requirements are read from a fair sample: {_cap_phrase()} per role and "
            "specialization per month, every design role read in full. Shares are estimates for all "
            "postings in the slice; quote the qualifier with any number.")


def rule_line() -> str:
    """The admin Sampling panel's rule line."""
    default = settings.default_limit()
    parts = [f"Up to {default} per role and specialization per month"]
    for role in ("Designer", "Engineer", "Product Manager", "other"):
        limit = settings.limit_for(role)
        if limit != default:  # only roles that differ from the default are named
            parts.append(f"{role}: all" if limit is None else f"{role}: up to {limit}")
    parts.append("unknown: kept until resolved")
    return " · ".join(parts)


def qualifier(confidence: str, sample_n: int, population_n: int, margin_pts: int | None) -> str:
    """The n-of-N line for a requirements figure (experience — Requirements estimates —
    Thresholds). Rendered here once so no surface writes its own wording."""
    if sample_n == 0:
        return "No postings in this slice have been read yet."
    if confidence in ("full", "full_small"):
        return f"Based on all {population_n:,} postings."
    if confidence == "too_few":
        return f"Not enough postings read yet to estimate this ({sample_n:,} of {population_n:,} so far)."
    line = f"Estimated from {sample_n:,} of {population_n:,} postings we read in full · ±{margin_pts} pts"
    if confidence == "small_sample":
        line += " · small sample, treat as a rough guide"
    return line

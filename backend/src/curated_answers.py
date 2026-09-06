"""
Curated instant answers — common market-health questions answered deterministically
from live platform data, with NO model call.

See changes/2026-09-03-chat-resilience-and-instant-answers.md and
backend/specs/market-health/api.md — "Curated instant-answer engine".

Adding a question is a one-file change: add a CuratedEntry (canonical question +
phrasings + a builder) and a focused test. Nothing else changes — not the model
stages, the tool interface, or the stream contract.

Every builder must honour the same honesty rules a model answer must
(design/market-health/experience.md — User Flow 7c):
  - state the data's time window (from the query's data_range)
  - proportions carry their denominator; never an absolute claim
  - structured vs. parsed compensation are never blended
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from llm.base import ToolCall
from market_query import (
    query_compensation_data,
    query_market_data,
    query_requirements_data,
)

# A builder returns (answer_markdown, tool_calls) — the tool calls feed the
# reasoning trace exactly as a model answer's do.
Builder = Callable[[], "tuple[str, list[ToolCall]]"]

_PLOTTED = ("Designer", "Product Manager", "Engineer")


@dataclass(frozen=True)
class CuratedEntry:
    id: str
    question: str                       # canonical — shown as a suggestion chip
    match_phrasings: tuple[str, ...]     # extra accepted wordings
    builder: Builder


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip(" ?.!,’'\"")


def _window(data_range: dict) -> str:
    e, l = data_range.get("earliest"), data_range.get("latest")
    return f"tracked between {e} and {l}" if e and l else "tracked so far"


def _tc(name: str, args: dict, result) -> ToolCall:
    return ToolCall(name=name, args=args, result=result)


# --------------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------------

def _roles_in_demand() -> tuple[str, list[ToolCall]]:
    args = {"group_by": ["role_category"]}
    r = query_market_data(**args)
    rows = sorted(
        (row for row in r["rows"] if row.get("role_category") in _PLOTTED),
        key=lambda x: x["count"],
        reverse=True,
    )
    total = sum(row["count"] for row in rows)
    tc = [_tc("query_market_data", args, r)]
    if total == 0:
        return "No classified postings are available yet for the role areas we track.", tc
    lines = [
        f"- **{row['role_category']}** — {row['count']:,} postings "
        f"({round(row['count'] / total * 100)}% of the {total:,} we track)"
        for row in rows
    ]
    body = (
        f"Across the postings {_window(r['data_range'])}, demand by role area breaks down as:\n\n"
        + "\n".join(lines)
        + f"\n\n{rows[0]['role_category']} leads by a wide margin. These are shares of the "
        "roles and companies we currently track — a growing sample, not the whole market."
    )
    return body, tc


def _pay_for(role: str):
    def build() -> tuple[str, list[ToolCall]]:
        args = {"role_category": [role]}
        r = query_compensation_data(**args)
        tc = [_tc("query_compensation_data", args, r)]
        structured, parsed = r["structured_count"], r["parsed_count"]
        lo, hi, cur = r["salary_min"], r["salary_max"], r["currency"]
        total = r["total_matching"]
        window = _window(r["data_range"])
        if structured == 0 and parsed == 0:
            return (
                f"None of the {total:,} {role} postings {window} disclose a salary range, "
                "so there's no reliable pay figure to give for this slice yet.",
                tc,
            )
        if structured > 0 and lo and hi:
            # Guard against inconsistent disclosed data (mixed hourly/annual, bad
            # parsing) — a min of a few hundred next to a max in the hundreds of
            # thousands is not a range worth stating as one.
            plausible = lo >= 10_000 and hi / lo <= 20
            if plausible:
                body = (
                    f"Based on **{structured:,} {role} postings with a disclosed salary range** "
                    f"({window}), pay runs roughly **{cur} {lo:,.0f}–{hi:,.0f}**."
                )
            else:
                body = (
                    f"**{structured:,} {role} postings disclose a salary range** ({window}), but "
                    f"the disclosed figures are too inconsistent to state as one band "
                    f"(they span {cur} {lo:,.0f} to {hi:,.0f} — likely a mix of hourly and "
                    "annual, or parsing noise). Treat any single number with caution."
                )
            if parsed > 0:
                body += (
                    f" A further {parsed:,} postings mention pay only in the job text — those "
                    "are noisier estimates and are not included above."
                )
            return body, tc
        # structured == 0 but parsed > 0
        return (
            f"No {role} postings {window} carry a structured salary range. "
            f"{parsed:,} mention pay within the job description text — those are estimates "
            "only, not disclosed figures, so treat any number from them with caution. "
            "Ask for the estimate explicitly if you want it.",
            tc,
        )

    return build


def _skills_for(role: str):
    def build() -> tuple[str, list[ToolCall]]:
        args = {"role_category": [role]}
        r = query_requirements_data(**args)
        tc = [_tc("query_requirements_data", args, r)]
        total = r["total_matching"]
        window = _window(r["data_range"])
        if total == 0:
            return (
                f"No {role} postings {window} have had their requirements extracted yet, "
                "so there's nothing to summarise for this slice.",
                tc,
            )
        ranked = sorted(
            r["skills"],
            key=lambda s: s["must_have_count"] + s["nice_to_have_count"],
            reverse=True,
        )[:6]
        lines = [
            f"- **{s['skill_group']}** — mentioned in "
            f"{s['must_have_count'] + s['nice_to_have_count']:,} of {total:,} postings "
            f"({round((s['must_have_count'] + s['nice_to_have_count']) / total * 100)}%; "
            f"{s['must_have_count']:,} as must-have)"
            for s in ranked
        ]
        body = (
            f"Based on **{total:,} {role} postings with extracted requirements** ({window}), "
            "the most-mentioned skill groups are:\n\n"
            + "\n".join(lines)
            + "\n\nThese are proportions of the postings we've processed, interpreted from "
            "job-description text — not verified facts."
        )
        return body, tc

    return build


# --------------------------------------------------------------------------
# Catalogue
# --------------------------------------------------------------------------

CURATED_CATALOGUE: tuple[CuratedEntry, ...] = (
    CuratedEntry(
        id="roles-in-demand",
        question="Which roles are most in demand right now?",
        match_phrasings=(
            "which roles are growing",
            "which roles are in demand",
            "what roles are in demand",
            "which role has the most demand",
            "which role has the most openings",
            "what role has the most jobs",
            "role breakdown",
        ),
        builder=_roles_in_demand,
    ),
    CuratedEntry(
        id="engineer-pay",
        question="What do engineers earn?",
        match_phrasings=(
            "what do engineers earn",
            "engineer salary",
            "engineer pay",
            "how much do engineers make",
            "what is the salary for engineers",
        ),
        builder=_pay_for("Engineer"),
    ),
    CuratedEntry(
        id="designer-pay",
        question="What do designers earn?",
        match_phrasings=(
            "what do designers earn",
            "designer salary",
            "designer pay",
            "how much do designers make",
        ),
        builder=_pay_for("Designer"),
    ),
    CuratedEntry(
        id="pm-pay",
        question="What do product managers earn?",
        match_phrasings=(
            "what do product managers earn",
            "product manager salary",
            "pm salary",
            "how much do product managers make",
        ),
        builder=_pay_for("Product Manager"),
    ),
    CuratedEntry(
        id="pm-skills",
        question="What skills do product manager roles ask for?",
        match_phrasings=(
            "what skills do product manager postings ask for",
            "what skills do pms need",
            "product manager skills",
            "skills for product managers",
        ),
        builder=_skills_for("Product Manager"),
    ),
    CuratedEntry(
        id="engineer-skills",
        question="What skills do engineering roles ask for?",
        match_phrasings=(
            "what skills do engineering postings ask for",
            "what skills do engineers need",
            "engineer skills",
            "skills for engineers",
        ),
        builder=_skills_for("Engineer"),
    ),
)


def suggestions() -> dict:
    """Presentation metadata for the frontend chips — no answers."""
    return {"suggestions": [{"id": e.id, "question": e.question} for e in CURATED_CATALOGUE]}


def match(user_text: str) -> CuratedEntry | None:
    """
    Conservative match: the normalised message must equal, or clearly contain,
    a canonical question or one of its phrasings. Anything ambiguous returns
    None and falls through to the model — a wrong instant answer is worse than
    a slow correct one.
    """
    if not user_text:
        return None
    norm = _norm(user_text)
    for entry in CURATED_CATALOGUE:
        candidates = (entry.question, *entry.match_phrasings)
        for c in candidates:
            cn = _norm(c)
            if norm == cn or (len(cn) >= 12 and cn in norm):
                return entry
    return None

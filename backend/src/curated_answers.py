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


# Filler that carries no intent — dropped before comparing a message to a
# catalogued phrasing (see match()). Keep this tight: a word that distinguishes
# one curated question from another must NOT be here.
_STOPWORDS = frozenset(
    """
    a an the is are was were be been being am
    do does did done doing
    what which who whom whose how why where when
    much many more most some any all
    for of in on at to from with by as into about around over
    i me my mine you your yours we us our ours they them their
    it its this that these those there here
    right now today currently these days lately recently nowadays
    and or vs versus than then so just also too very really quite
    tell show give list explain
    need needs want wants would will can could should shall may might must
    get gets got getting have has had having
    like looking look s re ll
    please thanks
    """.split()
)


def _content_tokens(text: str) -> set[str]:
    """Lowercase alnum tokens, minus stopwords, crudely singularised so
    'managers' == 'manager' and 'skills' == 'skill'. Used for tolerant matching
    of a naturally-worded question against a catalogued phrasing."""
    out: set[str] = set()
    for tok in re.sub(r"[^a-z0-9\s]", " ", text.lower()).split():
        if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        if tok and tok not in _STOPWORDS:
            out.add(tok)
    return out


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
            "what roles are most in demand",
            "which role has the most demand",
            "which role has the most openings",
            "what role has the most jobs",
            "which roles are hiring the most",
            "what is being hired the most",
            "hiring demand by role",
            "demand by role category",
            "role breakdown",
        ),
        builder=_roles_in_demand,
    ),
    CuratedEntry(
        id="engineer-pay",
        question="What do engineers earn?",
        match_phrasings=(
            "what do engineers earn",
            "what do software engineers earn",
            "engineer salary",
            "engineering salary",
            "engineer pay",
            "engineer compensation",
            "pay for engineers",
            "how much do engineers make",
            "how much do engineers earn",
            "what is the salary for engineers",
            "what salary do engineers get",
        ),
        builder=_pay_for("Engineer"),
    ),
    CuratedEntry(
        id="designer-pay",
        question="What do designers earn?",
        match_phrasings=(
            "what do designers earn",
            "designer salary",
            "design salary",
            "designer pay",
            "designer compensation",
            "pay for designers",
            "how much do designers make",
            "how much do designers earn",
            "what is the salary for designers",
        ),
        builder=_pay_for("Designer"),
    ),
    CuratedEntry(
        id="pm-pay",
        question="What do product managers earn?",
        match_phrasings=(
            "what do product managers earn",
            "what do pms earn",
            "product manager salary",
            "product management salary",
            "pm salary",
            "pm pay",
            "product manager compensation",
            "pay for product managers",
            "how much do product managers make",
            "how much do product managers earn",
            "how much do pms make",
        ),
        builder=_pay_for("Product Manager"),
    ),
    CuratedEntry(
        id="pm-skills",
        question="What skills do product manager roles ask for?",
        match_phrasings=(
            "what skills do product manager postings ask for",
            "what skills do product managers need",
            "what skills do pms need",
            "what skills are in demand for product managers",
            "what skills are most in demand for product managers",
            "which skills are in demand for pms",
            "in demand skills for product managers",
            "top skills for product managers",
            "product manager skills",
            "product management skills",
            "pm skills",
            "skills for product managers",
            "what should a product manager know",
        ),
        builder=_skills_for("Product Manager"),
    ),
    CuratedEntry(
        id="engineer-skills",
        question="What skills do engineering roles ask for?",
        match_phrasings=(
            "what skills do engineering postings ask for",
            "what skills do engineers need",
            "what skills do software engineers need",
            "what skills are in demand for engineers",
            "what skills are most in demand for engineers",
            "in demand skills for engineers",
            "top skills for engineers",
            "engineer skills",
            "engineering skills",
            "skills for engineers",
            "skills for software engineers",
            "what should an engineer know",
        ),
        builder=_skills_for("Engineer"),
    ),
)


def suggestions() -> dict:
    """Presentation metadata for the frontend chips — no answers."""
    return {"suggestions": [{"id": e.id, "question": e.question} for e in CURATED_CATALOGUE]}


# A phrasing must contribute at least this share of its own content words to the
# message (_MIN_OVERLAP_RATIO), account for at least this many words
# (_MIN_OVERLAP_WORDS), AND cover at least this share of the *message's* content
# words (_MIN_MSG_COVERAGE — so a 2-word phrasing like "engineer skill" doesn't
# match a long comparison question that merely happens to contain both words).
# It must also beat every other entry. Tuned so ordinary rephrasings land while
# comparison / compound questions fall through to the model.
_MIN_OVERLAP_RATIO = 0.75
_MIN_OVERLAP_WORDS = 2
_MIN_MSG_COVERAGE = 0.5


def _best_overlap(msg_tokens: set[str], entry: CuratedEntry) -> tuple[float, int]:
    """(best ratio, matched-word count) for this entry's closest phrasing."""
    best = (0.0, 0)
    for phrasing in (entry.question, *entry.match_phrasings):
        pt = _content_tokens(phrasing)
        if not pt:
            continue
        matched = len(msg_tokens & pt)
        ratio = matched / len(pt)
        if (ratio, matched) > best:
            best = (ratio, matched)
    return best


def match(user_text: str) -> CuratedEntry | None:
    """
    Match a user message to a curated entry — tolerant of natural rephrasings,
    but still conservative: an ambiguous message, or one that fits two entries
    equally well, falls through to the model. A wrong instant answer is worse
    than a slow correct one.

    Two passes:
      1. exact, or a phrasing that is a substring AND most of the message (so a
         short phrasing like "engineer pay" inside a comparison question does not
         trigger a false match);
      2. content-word overlap — the message must carry ≥75% of some phrasing's
         distinguishing words (≥2 words), and beat every other entry.
    """
    if not user_text:
        return None

    norm = _norm(user_text)
    for entry in CURATED_CATALOGUE:
        for c in (entry.question, *entry.match_phrasings):
            cn = _norm(c)
            if norm == cn or (
                len(cn) >= 12 and cn in norm and len(cn) >= 0.6 * len(norm)
            ):
                return entry

    msg_tokens = _content_tokens(user_text)
    if not msg_tokens:
        return None
    scored = sorted(
        ((*_best_overlap(msg_tokens, e), e) for e in CURATED_CATALOGUE),
        key=lambda s: (s[0], s[1]),
        reverse=True,
    )
    top_ratio, top_matched, top_entry = scored[0]
    if top_ratio < _MIN_OVERLAP_RATIO or top_matched < _MIN_OVERLAP_WORDS:
        return None
    if top_matched / len(msg_tokens) < _MIN_MSG_COVERAGE:
        return None  # the message is about more than this phrasing covers
    runner_ratio, runner_matched, _ = scored[1]
    if runner_ratio >= top_ratio and runner_matched >= top_matched:
        return None  # ambiguous — two entries fit equally
    return top_entry

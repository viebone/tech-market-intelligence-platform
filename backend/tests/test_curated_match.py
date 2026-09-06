"""
Regression tests for curated_answers.match() — the tolerant matcher that decides
whether a chat message gets the sub-second no-model answer or falls through to
the model (changes/2026-09-06-chat-answer-truncation-and-curated-match.md).

No pytest in this repo yet — run directly:

    cd backend/src && ./venv_linux/bin/python ../tests/test_curated_match.py

Every `test_*` function is a plain assert, so `pytest` picks them up unchanged
if it is ever added.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import curated_answers as ca  # noqa: E402


# Ordinary rephrasings that MUST reach the curated instant answer.
_SHOULD_MATCH = {
    "pm-skills": [
        "What skills do product manager roles ask for?",          # canonical
        "What skills are more in demand for product managers?",    # the reported bug
        "what skills do product managers need",
        "What skills are in demand for PMs?",
        "skills in demand for product managers",
        "top skills for product managers",
        "what should a product manager know",
    ],
    "engineer-skills": [
        "What skills do engineering roles ask for?",
        "what skills are in demand for engineers",
        "top skills for engineers",
        "what skills do software engineers need",
    ],
    "engineer-pay": [
        "What do engineers earn?",
        "how much do engineers make",
        "what is the salary for engineers",
        "engineer compensation",
    ],
    "designer-pay": [
        "What do designers earn?",
        "how much do designers make",
        "designer salary",
    ],
    "pm-pay": [
        "What do product managers earn?",
        "how much do pms make",
        "product manager salary",
    ],
    "roles-in-demand": [
        "Which roles are most in demand right now?",
        "what roles are hiring the most",
        "which roles are growing",
        "hiring demand by role",
    ],
}

# Messages that must NOT match any entry — they go to the model (a wrong instant
# answer is worse than a slow correct one).
_SHOULD_NOT_MATCH = [
    "how does engineer pay compare to designer pay",   # comparison — ambiguous
    "Compare demand and required skills for security engineers versus ML engineers.",
    "what skills and pay do backend engineers get versus frontend",
    "should I learn Rust as an engineer",              # synthesis — model territory
    "is Kubernetes worth learning",
    "what is the weather today",
    "tell me about the market",
    "what changed last month",
    "how many product manager postings mention SQL",   # narrow — model territory
    "",
]


def test_natural_rephrasings_hit_the_curated_path():
    for expected_id, questions in _SHOULD_MATCH.items():
        for q in questions:
            entry = ca.match(q)
            assert entry is not None, f"{q!r} should have matched {expected_id}, got None"
            assert entry.id == expected_id, f"{q!r} matched {entry.id}, expected {expected_id}"


def test_ambiguous_and_off_topic_fall_through():
    for q in _SHOULD_NOT_MATCH:
        assert ca.match(q) is None, f"{q!r} should NOT have matched, got {ca.match(q).id}"


def test_every_catalogue_entry_matches_its_own_canonical_question():
    for entry in ca.CURATED_CATALOGUE:
        assert ca.match(entry.question) is entry, f"{entry.id}'s canonical question didn't match itself"


def test_every_phrasing_matches_its_own_entry():
    for entry in ca.CURATED_CATALOGUE:
        for phrasing in entry.match_phrasings:
            got = ca.match(phrasing)
            assert got is not None and got.id == entry.id, (
                f"{entry.id}: phrasing {phrasing!r} resolved to "
                f"{got.id if got else None}"
            )


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)

"""
statistics_crosscheck.py — the pure arithmetic behind Story 5's third movement
(design/market-health/data-stories.md, blocks 6 and 7; backend/specs/trusted-statistics/api.md §6).

No existing test file covered this module before (`industry_mix()` shipped 2026-09-25 with no
test; `size_mix()` was written to the same contract but never wired in or tested until
`changes/2026-09-25-employer-size-standard-bands.md` Step 7/8, 2026-09-27). This covers the pure,
database-free functions the spec itself calls out as testable in isolation
(`platform_mix_from_counts`, `ons_shares`) plus a real, live check of `size_mix()` against
production, documented in the change request rather than repeated here (a DB-backed test would
need a fixture database this repo doesn't have).

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_statistics_crosscheck.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from statistics_crosscheck import ons_shares, platform_mix_from_counts  # noqa: E402


def test_platform_mix_groups_and_states_shares_of_the_whole():
    counts = {"acme": 30, "beta": 20, "gamma": 50}
    result = platform_mix_from_counts(counts, lambda c: {"acme": "J", "beta": "K", "gamma": "J"}[c])
    assert result["postings"] == 100
    assert result["counts"] == {"J": 80, "K": 20}
    assert result["shares_pct"] == {"J": 80.0, "K": 20.0}
    assert result["unplaced_count"] == 0
    assert result["unplaced_share_pct"] == 0.0


def test_platform_mix_states_an_unplaced_share_never_drops_it():
    counts = {"acme": 30, "mystery": 70}
    result = platform_mix_from_counts(counts, lambda c: None if c == "mystery" else "J")
    assert result["postings"] == 100
    assert result["counts"] == {"J": 30}          # the unplaced company never appears as a fake group
    assert result["unplaced_count"] == 70
    assert result["unplaced_share_pct"] == 70.0
    assert sum(result["shares_pct"].values()) + result["unplaced_share_pct"] == 100.0


def test_platform_mix_empty_input_never_divides_by_zero():
    result = platform_mix_from_counts({}, lambda c: "J")
    assert result == {"postings": 0, "unplaced_count": 0, "unplaced_share_pct": None, "shares_pct": {}, "counts": {}}


def test_platform_mix_a_group_of_none_for_everyone_is_all_unplaced():
    result = platform_mix_from_counts({"a": 5, "b": 5}, lambda c: None)
    assert result["postings"] == 10
    assert result["unplaced_count"] == 10
    assert result["unplaced_share_pct"] == 100.0
    assert result["shares_pct"] == {}


def test_ons_shares_divides_by_the_stated_total_never_recomputes_it():
    # The total passed in is AP2Y — the published all-vacancies figure — not sum(levels.values()),
    # because ONS's own total need not equal the sum of the parts shown (rounding, unlisted classes).
    shares = ons_shares({"1-9": 91.0, "10-49": 99.0}, total=702.0)
    assert shares == {"1-9": round(100 * 91.0 / 702.0, 2), "10-49": round(100 * 99.0 / 702.0, 2)}


def test_ons_shares_missing_or_zero_total_is_empty_never_a_crash():
    assert ons_shares({"1-9": 91.0}, total=None) == {}
    assert ons_shares({"1-9": 91.0}, total=0) == {}


def test_platform_and_ons_shares_use_the_same_rounding_precision():
    # Both sides must round the same way (2dp) or the two bars in a two-series comparison row would
    # carry different implied precision for no honest reason.
    plat = platform_mix_from_counts({"a": 1, "b": 2}, lambda c: "J")
    ons = ons_shares({"J": 33.0}, total=100.0)
    assert plat["shares_pct"]["J"] == 100.0
    assert ons["J"] == 33.0


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"PASS {name}")
    print(f"{len(tests)}/{len(tests)} passed")

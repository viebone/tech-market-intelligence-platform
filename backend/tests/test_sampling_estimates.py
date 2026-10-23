"""
Requirements estimates and the one shared wording — backend/specs/market-health/api.md —
Business Logic — Sampling — Estimates / Method text; design/market-health/experience.md —
How we read the market, Requirements estimates.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_sampling_estimates.py
"""

import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import method_text  # noqa: E402
from sampling_estimates import Estimator, about_level  # noqa: E402

G1 = ("Engineer", "Backend Engineer", date(2026, 11, 1))
G2 = ("Engineer", "Frontend Engineer", date(2026, 11, 1))
G3 = ("Designer", "Product Designer", date(2026, 11, 1))


def test_post_stratified_share_against_hand_values():
    # G1: 700 postings, 50 read, 20 mention X.  G2: 100 postings, 50 read, 40 mention X.
    est = Estimator({G1: (700, 50), G2: (100, 50)}, {G1: 50, G2: 50})
    share = est.share_pct({G1: 20, G2: 40})
    hand = 100 * (700 * 20 / 50 + 100 * 40 / 50) / 800        # = 45.0
    assert share == round(hand, 1) == 45.0
    # The naive pooled share (60/100 = 60%) would overweight the small group — the point of weighting.
    assert share != 60.0


def test_margin_against_hand_value():
    est = Estimator({G1: (700, 50), G2: (100, 50)}, {G1: 50, G2: 50})
    var = (700 / 800) ** 2 * 0.25 / 50 * (650 / 699) + (100 / 800) ** 2 * 0.25 / 50 * (50 / 99)
    assert est.margin_pts() == math.ceil(100 * 1.96 * math.sqrt(var))


def test_every_posting_read_is_not_an_estimate():
    est = Estimator({G3: (38, 38)}, {G3: 38})
    e = est.estimate()
    assert not e["is_estimate"] and e["margin_pts"] is None and e["confidence"] == "full"
    assert e["qualifier"] == "Based on all 38 postings."


def test_thresholds():
    assert Estimator({G1: (700, 50)}, {G1: 50}).confidence() == "estimate"
    assert Estimator({G1: (700, 20)}, {G1: 20}).confidence() == "small_sample"
    assert Estimator({G1: (700, 6)}, {G1: 6}).confidence() == "too_few"
    assert Estimator({G3: (8, 8)}, {G3: 8}).confidence() == "full_small"
    assert not Estimator({G1: (700, 6)}, {G1: 6}).shows_shares


def test_unread_groups_are_reported_not_mixed_in():
    est = Estimator({G1: (700, 50), G2: (300, 0)}, {G1: 50})
    e = est.estimate()
    assert e["unread_n"] == 300 and e["population_n"] == 700


def test_requirement_filters_narrow_the_base():
    # Remote-only: 10 of G1's 50 read postings are remote. Base = 700/50 * 10 = 140.
    est = Estimator({G1: (700, 50)}, {G1: 10})
    assert est.estimate()["population_n"] == 140
    assert est.share_pct({G1: 5}) == 50.0


def test_about_level():
    assert about_level(42.0, 38.0, 14)
    assert not about_level(42.0, 20.0, 14)
    assert not about_level(42.0, 41.0, None)                 # no margin (full count): data order stands


def test_qualifier_wording_matches_the_experience_spec():
    assert method_text.qualifier("estimate", 50, 712, 14) == \
        "Estimated from 50 of 712 postings we read in full · ±14 pts"
    assert method_text.qualifier("small_sample", 20, 300, 22).endswith("· small sample, treat as a rough guide")
    assert method_text.qualifier("too_few", 6, 700, None) == \
        "Not enough postings read yet to estimate this (6 of 700 so far)."
    assert method_text.qualifier("estimate", 0, 0, None) == "No postings in this slice have been read yet."


def test_method_text_is_one_source_with_live_values():
    m = 210
    one = method_text.one_line(m)
    assert one == ("We count every job posted by the 210 companies we follow, and read a fair sample of "
                   "those job descriptions in full to see what employers ask for.")
    obj = method_text.method(m)
    assert obj["one_line"] == one and obj["company_count"] == 210 and obj["limit_per_group"] == 50
    assert [i["heading"] for i in obj["full"]] == [
        "Who we follow", "Every job counted", "A fair sample read in full", "How close the estimates are"]
    assert "up to 50 job descriptions" in obj["full"][2]["text"]
    # The curated answer is the same text, joined.
    assert all(i["text"] in method_text.full_as_markdown(m) for i in obj["full"])


def test_method_text_without_a_company_count_still_reads_well():
    # Reference surfaces (MCP get_taxonomy, server instructions) must work with no database.
    assert method_text.one_line(None).startswith("We count every job posted by the companies we follow,")
    assert method_text.full(None)[0]["text"].startswith("The career pages of the companies we follow,")
    assert "None" not in method_text.full_as_markdown(None) + method_text.coverage_line(None)


def test_method_text_follows_the_settings():
    import os
    os.environ["SAMPLING_LIMIT_PRODUCT_MANAGER"] = "40"
    try:
        text = method_text.full(210)[2]["text"]
        assert "up to 50 for engineering roles and up to 40 for product roles" in text
        assert "Product Manager: up to 40" in method_text.rule_line()
    finally:
        del os.environ["SAMPLING_LIMIT_PRODUCT_MANAGER"]
    assert method_text.rule_line() == \
        "Up to 50 per role and specialization per month · Designer: all · unknown: kept until resolved"


def test_no_forbidden_words_in_visible_method_text():
    text = (method_text.one_line(210) + method_text.full_as_markdown(210) + method_text.coverage_line(210)
            + method_text.requirements_method_note()).lower()
    for word in ("every job in the market", "we don't count every job", "stratified", "weighted",
                 "confidence interval", "statistically significant"):
        assert word not in text, word


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print(f"ok  {name}")
    print(f"{len(tests)} passed")

"""
Employer headcount -> ONS size band (changes/2026-09-25-employer-size-standard-bands.md;
backend/specs/market-health/api.md — Business Logic — Employer size, revised).

What this enforces:
- the band derivation is right at every boundary (each side of 9/10, 49/50, 249/250, 2,499/2,500);
- a range that straddles a boundary is 'ambiguous' unless a human recorded a band_choice with a reason,
  and a band_choice is only accepted where it is actually a choice (straddle, band the range touches,
  reason given, confidence 'low');
- malformed curated entries are rejected (low > high, no source, no as_of, bad basis/confidence);
- COVERAGE: every tracked company (industries.COMPANY_INDUSTRY) is either in COMPANY_HEADCOUNT or in
  UNKNOWN_HEADCOUNT with a reason — adding a company without deciding fails the build (same pattern as
  test_source_licences.py) — and no stale entry outlives a removed company;
- no tracked company is left 'ambiguous' (PM decision 2026-09-25: choose the more probable band);
- nothing outside the five ONS band codes (or None) ever comes out — the retired Startup / Small-Growth /
  Medium / Large labels cannot reappear.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_employer_headcount.py
    (or, in WSL, ./venv_linux/bin/python ../tests/test_employer_headcount.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import employer_headcount as eh  # noqa: E402
import industries  # noqa: E402
from employer_headcount import (  # noqa: E402
    AMBIGUOUS, COMPANY_HEADCOUNT, ONS_SIZE_BANDS, UNKNOWN_HEADCOUNT, EmployerHeadcount, ons_size_band, size_band_for,
)

_CODES = {code for code, *_ in ONS_SIZE_BANDS}


def _hc(low, high=None, **kw):
    kw.setdefault("as_of", "2026")
    kw.setdefault("basis", "worldwide")
    kw.setdefault("source", "test")
    kw.setdefault("confidence", "medium")
    return EmployerHeadcount(low, low if high is None else high, **kw)


def _raises(fn) -> bool:
    try:
        fn()
    except ValueError:
        return True
    return False


# ── derivation ────────────────────────────────────────────────────────────────

def test_every_boundary_lands_in_the_right_band():
    cases = [
        (1, "1-9"), (9, "1-9"), (10, "10-49"), (49, "10-49"), (50, "50-249"), (249, "50-249"),
        (250, "250-2499"), (2499, "250-2499"), (2500, "2500+"), (100000, "2500+"),
    ]
    for n, expected in cases:
        assert ons_size_band(_hc(n)) == expected, f"{n} -> {ons_size_band(_hc(n))}, expected {expected}"


def test_a_range_inside_one_band_gets_that_band():
    assert ons_size_band(_hc(900, 1001)) == "250-2499"
    assert ons_size_band(_hc(250, 2499)) == "250-2499"
    assert ons_size_band(_hc(2500, 9000)) == "2500+"


def test_a_straddling_range_is_ambiguous_unless_a_choice_was_recorded():
    assert ons_size_band(_hc(240, 386, confidence="low")) == AMBIGUOUS
    assert ons_size_band(_hc(2400, 2600, confidence="low")) == AMBIGUOUS
    chosen = _hc(240, 386, confidence="low", band_choice="250-2499", band_choice_reason="most sources >= 250")
    assert ons_size_band(chosen) == "250-2499"


def test_no_entry_means_no_band_never_a_guess():
    assert ons_size_band(None) is None
    assert size_band_for(None) is None
    assert size_band_for("") is None
    assert size_band_for("a-company-nobody-researched") is None


# ── entry validation ──────────────────────────────────────────────────────────

def test_malformed_entries_are_rejected():
    assert _raises(lambda: _hc(500, 100))                                   # low > high
    assert _raises(lambda: _hc(0))                                          # below the smallest band
    assert _raises(lambda: _hc(100, source=" "))                            # no source
    assert _raises(lambda: _hc(100, as_of=""))                              # no as_of
    assert _raises(lambda: _hc(100, basis="global"))                        # unknown basis
    assert _raises(lambda: _hc(100, confidence="certain"))                  # unknown confidence


def test_band_choice_is_only_accepted_where_it_is_really_a_choice():
    ok = dict(confidence="low", band_choice="250-2499", band_choice_reason="why")
    assert not _raises(lambda: _hc(240, 386, **ok))
    assert _raises(lambda: _hc(900, 1001, **ok))                                             # range not straddling
    assert _raises(lambda: _hc(240, 386, confidence="low", band_choice="2500+", band_choice_reason="x"))  # band not touched
    assert _raises(lambda: _hc(240, 386, confidence="low", band_choice="250-2499"))          # no reason
    assert _raises(lambda: _hc(240, 386, confidence="medium", band_choice="250-2499", band_choice_reason="x"))  # not low
    assert _raises(lambda: _hc(240, 386, band_choice_reason="reason without a choice"))


# ── the curated data ──────────────────────────────────────────────────────────

def test_every_tracked_company_has_a_headcount_or_an_explicit_reason():
    tracked = set(industries.COMPANY_INDUSTRY)
    have = set(COMPANY_HEADCOUNT)
    unknown = set(UNKNOWN_HEADCOUNT)
    missing = tracked - have - unknown
    assert not missing, f"tracked companies with no headcount and no UNKNOWN_HEADCOUNT reason: {sorted(missing)}"
    both = have & unknown
    assert not both, f"in both COMPANY_HEADCOUNT and UNKNOWN_HEADCOUNT: {sorted(both)}"
    stale = (have | unknown) - tracked
    assert not stale, f"headcount entries for companies that are no longer tracked: {sorted(stale)}"
    for company, reason in UNKNOWN_HEADCOUNT.items():
        assert reason.strip(), f"{company} is in UNKNOWN_HEADCOUNT with no reason"


def test_no_tracked_company_is_left_ambiguous():
    # PM decision 2026-09-25: choose the more probable band rather than leave a company unplaced.
    left = [c for c in COMPANY_HEADCOUNT if size_band_for(c) == AMBIGUOUS]
    assert not left, f"straddling range with no band_choice (record a choice and its reason): {left}"


def test_every_recorded_choice_states_its_reason_and_stays_low_confidence():
    choices = {c: e for c, e in COMPANY_HEADCOUNT.items() if e.band_choice}
    assert choices, "expected the PM-decided choices for the previously ambiguous companies"
    for company, entry in choices.items():
        assert entry.band_choice_reason.strip(), company
        assert entry.confidence == "low", company
    assert set(choices) == {"gymshark", "faculty", "substack", "notion", "supabase"}, sorted(choices)


def test_only_ons_band_codes_or_none_ever_come_out():
    seen = {size_band_for(c) for c in set(COMPANY_HEADCOUNT) | set(UNKNOWN_HEADCOUNT)}
    assert seen <= (_CODES | {None}), f"unexpected values: {seen - _CODES - {None}}"
    for retired in ("Startup", "Small/Growth", "Medium", "Large", "Medium/Small"):
        assert retired not in seen


def test_research_spot_checks():
    expected = {
        "monzo": "2500+",        # 5,275-5,429 (old bucket: Medium)
        "wise": "2500+",         # 7,585
        "ocadogroup": "2500+",   # 11,941
        "spotify": "2500+",      # 7,287-7,323 (20-F)
        "autotrader": "250-2499",  # 1,249-1,267
        "doximity": "250-2499",  # 880 FTE (10-K)
        "peloton": "250-2499",   # 2,262 (10-K) — below the 2,500 boundary
        "cuvva": "50-249",       # 96-100
        "attio": "50-249",       # 115-177
        "gymshark": "250-2499",  # chosen: straddles 250-2,499 / 2,500+
        "lever": None,           # no company-level figure found
    }
    for company, band in expected.items():
        assert size_band_for(company) == band, f"{company}: {size_band_for(company)} != {band}"


def test_no_company_is_under_50_employees_in_this_panel():
    # A real, useful fact from the 2026-09-25 research (the size cross-check will surface it) — pinned so a
    # future change that adds a micro/small firm is a conscious edit of this test, not a silent shift.
    assert not [c for c in COMPANY_HEADCOUNT if size_band_for(c) in ("1-9", "10-49")]


def test_industries_reexports_the_same_function_raw_postings_already_imports():
    assert industries.size_band_for is eh.size_band_for
    assert not hasattr(industries, "COMPANY_SIZE_BAND"), "the retired hand-assigned labels must not come back"


def test_backfill_plan_rewrites_old_labels_and_never_invents_values():
    from backfill_employer_size_band import plan  # pure function — no database needed

    rows = [
        ("monzo", "Medium", 40),          # retired label -> ONS band
        ("cuvva", "Small/Growth", 12),    # retired label -> ONS band
        ("wise", "2500+", 7),             # already correct -> untouched by the plan (idempotent)
        ("lever", None, 9),               # unknown headcount, stored NULL -> no change
        ("some-removed-company", "Large", 3),   # not in the lookup -> reported, left alone
        (None, "Medium", 2),              # no company -> reported, left alone
    ]
    changes, untouched = plan(rows)
    assert {(c["company"], c["old"], c["new"], c["rows"]) for c in changes} == {
        ("monzo", "Medium", "2500+", 40),
        ("cuvva", "Small/Growth", "50-249", 12),
    }, changes
    assert {u["company"] for u in untouched} == {"some-removed-company", None}, untouched
    # idempotent: planning again from the already-migrated state changes nothing
    migrated = [(c["company"], c["new"], c["rows"]) for c in changes] + [("wise", "2500+", 7), ("lever", None, 9)]
    again, _ = plan(migrated)
    assert again == [], again


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

"""
The sampling decision — backend/specs/market-health/api.md — Business Logic — Sampling;
changes/2026-10-10-requirements-extraction-sampling.md; CLAUDE.md Rule 15.

What these pin down: the choice is fair and repeatable; a month keeps about the limit, never
explodes; Designer and unknown are always kept; a steady-state day writes nothing and nothing in
this path ever deletes or overwrites; a not-kept posting can never be selected for paid reading.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_sampling.py
"""

import inspect
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import raw_postings  # noqa: E402
import sampling  # noqa: E402
import sampling_settings as settings  # noqa: E402


class _Swap:
    def __init__(self, module, **attrs):
        self._module, self._attrs, self._saved = module, attrs, {}

    def __enter__(self):
        for name, value in self._attrs.items():
            self._saved[name] = getattr(self._module, name)
            setattr(self._module, name, value)
        return self

    def __exit__(self, *a):
        for name, value in self._saved.items():
            setattr(self._module, name, value)


class _SpyConnection:
    """Stands in for db.get_connection(): records SQL, returns canned rows for SELECTs."""
    def __init__(self, select_rows=()):
        self.statements: list[str] = []
        self._rows = list(select_rows)

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self):
        return self

    def execute(self, sql, params=None):
        self.statements.append(" ".join(sql.split()))
        return self

    def executemany(self, sql, rows):
        self.statements.append(" ".join(sql.split()))

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return None


# --- fair and repeatable --------------------------------------------------------

def test_hash_is_fixed_and_uniform():
    assert sampling.hash_u("greenhouse:acme/1") == sampling.hash_u("greenhouse:acme/1")
    values = [sampling.hash_u(f"lever:co/{i}") for i in range(20000)]
    assert all(0.0 <= v < 1.0 for v in values)
    assert abs(sum(values) / len(values) - 0.5) < 0.01          # mean of U(0,1)
    assert abs(sum(v < 0.1 for v in values) / len(values) - 0.1) < 0.01


# --- the rate -------------------------------------------------------------------

def test_rate_is_one_for_small_or_unlimited_groups():
    assert sampling.rate_for(None, 5000, 4000, 20, 31) == 1.0
    assert sampling.rate_for(50, 40, 10, 3, 31) == 1.0
    assert sampling.rate_for(50, 0, 0, 1, 31) == 1.0             # new group, no history


def test_rate_from_previous_month():
    assert abs(sampling.rate_for(50, 700, 100, 3, 31) - 50 / 700) < 1e-9


def test_rate_only_falls_after_recalibration_day():
    # A new source doubles volume: last month 100, this month 400 seen by day 10 of 30.
    r = sampling.rate_for(50, 100, 400, 10, 30)
    assert abs(r - 50 / 1200) < 1e-9                             # projected 1,200 for the month
    # A quiet month never raises the rate above last month's.
    assert sampling.rate_for(50, 700, 10, 20, 30) == 50 / 700
    # Before day 7, no recalibration.
    assert sampling.rate_for(50, 100, 400, 6, 30) == 0.5


# --- the decision ---------------------------------------------------------------

def test_designer_and_unknown_always_kept():
    assert sampling.decide("Designer", 0.99, 0.01, None, 10_000) == ("kept", "all_kept_role")
    assert sampling.decide("unknown", 0.99, 0.01, 50, 10_000) == ("kept", "unknown_role")


def test_selection_and_ceiling():
    assert sampling.decide("Engineer", 0.01, 0.07, 50, 0) == ("kept", "selected")
    assert sampling.decide("Engineer", 0.50, 0.07, 50, 0) == ("not_kept", "not_selected")
    assert sampling.decide("Engineer", 0.50, 1.0, 50, 0) == ("kept", "under_limit")
    assert sampling.decide("Engineer", 0.01, 0.07, 50, 100) == ("not_kept", "ceiling")


def test_default_limits():
    assert settings.limit_for("Designer") is None
    assert settings.limit_for("unknown") is None
    assert settings.limit_for("Engineer") == 50 == settings.limit_for("Product Manager") == settings.limit_for("other")


def test_a_simulated_month_keeps_about_the_limit():
    """K=50, a stable 700-posting group. One month is a Poisson draw (sd ≈ 6.8), so the useful
    checks are: on average the sample sits on the limit, and no month strays far from it."""
    rng = random.Random(7)  # fixed seed: deterministic, not flaky
    months = []
    for trial in range(200):
        kept = 0
        for i in range(700):
            day = 1 + i * 30 // 700
            rate = sampling.rate_for(50, 700, i + 1, day, 30)
            decision, _ = sampling.decide("Engineer", sampling.hash_u(f"sim{trial}:{rng.random()}"), rate, 50, kept)
            kept += decision == "kept"
        months.append(kept)
    mean = sum(months) / len(months)
    assert 47 <= mean <= 53, mean
    assert all(25 <= k <= 75 for k in months), (min(months), max(months))      # ≈ ±3.7 sd


def test_a_surge_is_bounded_by_the_ceiling():
    kept = 0
    for i in range(5000):  # no history, so the rate starts at 1 — the ceiling must hold it
        rate = sampling.rate_for(50, 0, i + 1, 2, 30)
        decision, _ = sampling.decide("Engineer", sampling.hash_u(f"surge:{i}"), rate, 50, kept)
        kept += decision == "kept"
    assert kept == settings.CEILING_MULTIPLIER * 50


# --- Rule 15: the steady state, and nothing destructive anywhere -------------------

def test_steady_state_decision_phase_writes_nothing():
    spy = _SpyConnection(select_rows=[])
    with _Swap(sampling, get_connection=spy):
        stats = sampling.run_decision_phase({}, now=datetime(2026, 11, 3, 6, tzinfo=timezone.utc))
    assert stats == {"postings_kept": 0, "postings_not_kept": 0, "postings_pending": 0}
    assert not any(s.startswith(("INSERT", "UPDATE", "DELETE")) for s in spy.statements)


def test_before_go_live_nothing_runs():
    spy = _SpyConnection()
    with _Swap(sampling, get_connection=spy):
        sampling.run_decision_phase({}, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert spy.statements == []


def test_sampling_path_never_deletes_or_overwrites():
    for fn in (sampling.run_decision_phase, sampling.reuse_duplicate_extractions, raw_postings.insert_new_postings):
        src = inspect.getsource(fn).upper()
        assert "DELETE FROM" not in src, fn.__name__
        assert "UPDATE RAW_POSTINGS" not in src and "UPDATE POSTING_DETAILS" not in src, fn.__name__
        assert "UPDATE POSTING_SAMPLES" not in src, fn.__name__


def test_decided_postings_with_payload_are_inserted_once():
    now = datetime(2026, 11, 20, 6, tzinfo=timezone.utc)
    created = datetime(2026, 11, 19, 6, tzinfo=timezone.utc)
    pending = [
        ("greenhouse:a/1", created, "acme", "Product Designer", "greenhouse", "Designer", "Product Designer"),
        ("greenhouse:a/2", created, "acme", "Engineer", "greenhouse", None, None),          # unclassified
        ("greenhouse:a/3", created, "acme", "Lawyer", "greenhouse", "other", None),
    ]

    class _Conn(_SpyConnection):
        def execute(self, sql, params=None):
            super().execute(sql, params)
            self._rows = pending if "LEFT JOIN posting_samples ps" in sql and "ORDER BY rp.created_at" in sql else []
            return self

    spy = _Conn()
    payloads = {pid: {"content": "<p>desc</p>"} for pid, *_ in pending}
    with _Swap(sampling, get_connection=spy):
        stats = sampling.run_decision_phase(payloads, now=now)
    assert stats["postings_pending"] == 1                      # the unclassified one waits
    assert stats["postings_kept"] >= 1                          # the designer, always
    inserts = [s for s in spy.statements if s.startswith("INSERT INTO posting_samples")]
    assert len(inserts) == 1 and "ON CONFLICT (posting_id) DO NOTHING" in inserts[0]


def test_not_kept_postings_are_never_selected_for_paid_reading():
    where = raw_postings._NEEDING_REQUIREMENTS_WHERE
    assert "ps.decision IN ('kept', 'kept_before_sampling')" in where
    assert settings.SAMPLING_GO_LIVE.isoformat() in where      # legacy backlog still drains
    assert "posting_samples ps" in raw_postings._NEEDING_REQUIREMENTS_JOINS


def test_counts_never_read_sampling_tables():
    """Job counts, trends, pay and coverage read raw_postings + classifications only, so sampling
    cannot change them (spec: Sampling across the other response surfaces — Unchanged and checked)."""
    import market_openings
    import market_query
    for fn in (market_query.query_market_data, market_query.query_compensation_data):
        src = inspect.getsource(fn)
        assert "posting_samples" not in src and "posting_details" not in src and "raw_response" not in src, fn.__name__
    src = inspect.getsource(market_openings)
    assert "posting_samples" not in src and "posting_details" not in src


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print(f"ok  {name}")
    print(f"{len(tests)} passed")

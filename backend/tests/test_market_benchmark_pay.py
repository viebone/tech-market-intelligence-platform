"""
Row-shaping checks for Story 3's "Typical pay by role" block after it gained the full salary
percentile spread — added 2026-09-27 (`changes/2026-09-26-data-story-chart-variety.md`), for
`design/market-health/data-stories.md`'s Range chart and `backend/specs/market-health/api.md`'s
"Pay block gains the full percentile spread".

**Deviates from this test suite's usual "skip cleanly if no DATABASE_URL" convention**
(`test_story_yoy.py`) — deliberately, and named here rather than silently: no DATABASE_URL is
configured in this environment, and the whole point of this change is the *shaping* of a role's
row (percentile casts, the 30-sample flag, which definitions travel with it) — logic that never
touches SQL semantics, only what Python does with the tuples psycopg would hand back. A fake
connection whose `.execute()` returns fixed rows exercises the real functions
(`build_market_benchmark_story`, `query_market_benchmark_data`, `get_market_benchmark`) exactly as
written, rather than skipping them entirely until a live database happens to be available.

Run:
    cd backend/src && ./venv_linux/bin/python ../tests/test_market_benchmark_pay.py
"""

import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Columns match the real SELECTs in market_stories.build_market_benchmark_story() and
# market_query.query_market_benchmark_data() — see backend/specs/market-health/api.md.
_OBSERVATION_COLUMNS = (
    "entity_name", "vacancy_count", "salary_median", "salary_sample_size",
    "salary_p10", "salary_p25", "salary_p75", "salary_p90", "salary_unit", "employment_type",
)
_SKILL_COLUMNS = ("skill_name", "job_count")

# Three roles exercising every honesty state at once:
#  - "Product Owner": full percentile spread, a real (non-small) sample.
#  - "UX Designer": salary_sample_size below 30 -> small_sample.
#  - "Product Manager": salary_median present but every percentile NULL -> "range not reported".
#  - "DevOps Engineer": salary_median itself NULL -> excluded from pay_rows entirely (unchanged
#    pre-existing behaviour, checked here so this change is confirmed not to have broken it).
_OBSERVATION_ROWS = [
    ("Product Owner", 42, 65000, 45, 48000, 58000, 72000, 85000, "GBP/year", "permanent"),
    ("UX Designer", 18, 55000, 12, 42000, 50000, 61000, 70000, "GBP/year", "permanent"),
    ("Product Manager", 30, 70000, 8, None, None, None, None, "GBP/year", "permanent"),
    ("DevOps Engineer", 25, None, None, None, None, None, None, None, "permanent"),
]
_SKILL_ROWS = [("SQL", 120), ("Python", 90)]


class _FakeCursor:
    def __init__(self, columns, rows):
        self.description = [(c,) for c in columns]
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeConn:
    """Returns each queued (columns, rows) pair in order, one per `.execute()` call —
    matches both functions' real call order (observation query, then skill-associations query),
    regardless of the SQL text (this test isn't exercising SQL correctness)."""

    def __init__(self, queued):
        self._queued = list(queued)

    def execute(self, _sql, _params=None):
        columns, rows = self._queued.pop(0)
        return _FakeCursor(columns, rows)


@contextmanager
def _fake_get_connection(observation_rows=_OBSERVATION_ROWS, skill_rows=_SKILL_ROWS):
    yield _FakeConn([
        (_OBSERVATION_COLUMNS, observation_rows),
        (_SKILL_COLUMNS, skill_rows),
    ])


def _patch_connections(monkeypatch_targets, observation_rows=_OBSERVATION_ROWS, skill_rows=_SKILL_ROWS):
    """monkeypatch_targets: modules whose bound `get_connection` name needs replacing (each did
    `from db import get_connection`, so the name lives in that module's own namespace, not db's)."""
    originals = {}
    for module in monkeypatch_targets:
        originals[module] = module.get_connection
        module.get_connection = lambda om=observation_rows, sm=skill_rows: _fake_get_connection(om, sm)
    return originals


def _restore(originals):
    for module, original in originals.items():
        module.get_connection = original


def _pay_rows_by_name(roles):
    return {r["entity_name"]: r for r in roles}


def test_build_market_benchmark_story_pay_row_shape():
    import market_stories
    originals = _patch_connections([market_stories])
    try:
        story = market_stories.build_market_benchmark_story()
    finally:
        _restore(originals)

    pay_section = next(s for s in story["sections"] if s["id"] == "market-benchmark-pay")
    assert pay_section["status"] == "ready"
    by_name = _pay_rows_by_name(pay_section["content"]["roles"])

    # DevOps Engineer has no salary_median at all -- excluded entirely, same as before this change.
    assert "DevOps Engineer" not in by_name

    po = by_name["Product Owner"]
    assert po["salary_median"] == 65000.0 and isinstance(po["salary_median"], float)
    assert po["salary_p10"] == 48000.0 and po["salary_p90"] == 85000.0
    assert po["salary_unit"] == "GBP/year" and po["employment_type"] == "permanent"
    assert po["small_sample"] is False

    ux = by_name["UX Designer"]
    assert ux["salary_sample_size"] == 12
    assert ux["small_sample"] is True, "sample_size 12 is below the 30-sample threshold"

    pm = by_name["Product Manager"]
    assert pm["salary_median"] == 70000.0
    assert pm["salary_p10"] is None and pm["salary_p90"] is None, (
        "a role with salary_median but no percentiles must carry None, never an invented range"
    )
    # A role with a real sample size but no percentiles is still judged by its sample size for
    # small_sample -- 8 < 30, so it's flagged small even though "range not reported" is the more
    # visible state for this particular row (both are true and neither hides the other).
    assert pm["small_sample"] is True

    # The shared how-to-read wording travels with the section content whenever any role has pay data.
    from data_definitions import DEFINITIONS
    assert pay_section["content"]["definitions"] == {
        "benchmark.salary.percentiles": DEFINITIONS["benchmark.salary.percentiles"]
    }
    assert "30" in pay_section["qualifier"] or "small sample" in pay_section["qualifier"]


def test_build_market_benchmark_story_no_pay_data_has_no_definitions():
    import market_stories
    no_pay_rows = [("DevOps Engineer", 25, None, None, None, None, None, None, None, "permanent")]
    originals = _patch_connections([market_stories], observation_rows=no_pay_rows, skill_rows=[])
    try:
        story = market_stories.build_market_benchmark_story()
    finally:
        _restore(originals)

    pay_section = next(s for s in story["sections"] if s["id"] == "market-benchmark-pay")
    assert pay_section["status"] == "insufficient_data"
    assert pay_section["content"].get("definitions", {}) == {}, (
        "no role has salary data -- the how-to-read definition has nothing to explain and must "
        "not be shown as if a chart were rendering"
    )


def test_query_market_benchmark_data_pay_field_shape():
    import market_query
    originals = _patch_connections([market_query])
    try:
        result = market_query.query_market_benchmark_data()
    finally:
        _restore(originals)

    assert result["usable"] is True
    by_name = _pay_rows_by_name(result["roles"])

    po = by_name["Product Owner"]
    assert po["salary_p25"] == 58000.0 and po["salary_p75"] == 72000.0
    assert po["small_sample"] is False
    ux = by_name["UX Designer"]
    assert ux["small_sample"] is True

    from data_definitions import DEFINITIONS
    assert result["definitions"] == {
        "benchmark.salary.percentiles": DEFINITIONS["benchmark.salary.percentiles"]
    }


def test_get_market_benchmark_meta_definitions():
    import market_query
    import mcp_access.tools as tools

    originals = _patch_connections([market_query])
    try:
        envelope = tools.get_market_benchmark()
    finally:
        _restore(originals)

    from data_definitions import DEFINITIONS
    assert envelope["meta"]["definitions"] == {
        "benchmark.salary.percentiles": DEFINITIONS["benchmark.salary.percentiles"]
    }
    # The same fields the story shows are reachable through the MCP tool, unit-for-unit.
    role = next(r for r in envelope["data"]["roles"] if r["entity_name"] == "Product Owner")
    assert role["salary_p10"] == 48000.0 and role["salary_unit"] == "GBP/year"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

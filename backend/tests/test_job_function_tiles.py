"""
Shape checks for Story 4's function-breakdown block after it gained a treemap — added
2026-09-27 (`changes/2026-09-26-data-story-chart-variety.md`), for
`design/market-health/data-stories.md`'s Story 4 tail-handling decision and
`design/visual-design.md`'s Treemap. Pure logic, no database — `_job_function_tiles` takes
already-queried `{job_function, posting_count}` rows and shapes them into treemap tiles.

Run:
    cd backend/src && ./venv_linux/bin/python ../tests/test_job_function_tiles.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_query import _job_function_tiles  # noqa: E402


def _by_name(tiles):
    return {t["job_function"]: t for t in tiles}


def test_small_functions_merge_below_threshold():
    rows = [
        {"job_function": "Sales", "posting_count": 100},
        {"job_function": "Marketing", "posting_count": 80},
        {"job_function": "Legal", "posting_count": 3},
        {"job_function": "HR", "posting_count": 2},
        {"job_function": "unknown", "posting_count": 15},
    ]
    tiles = _job_function_tiles(rows)
    by_name = _by_name(tiles)

    assert by_name["Sales"]["kind"] == "named" and by_name["Sales"]["share"] == 50.0
    assert by_name["Marketing"]["kind"] == "named"
    assert "Legal" not in by_name and "HR" not in by_name, "small functions merge into the aggregate tile"

    aggregate = next(t for t in tiles if t["kind"] == "aggregate")
    assert aggregate["posting_count"] == 5
    assert set(aggregate["merged"]) == {"Legal", "HR"}
    assert aggregate["job_function"] == "2 smaller functions"


def test_unknown_never_merges_even_below_threshold():
    rows = [
        {"job_function": "Sales", "posting_count": 970},
        {"job_function": "unknown", "posting_count": 10},  # 1.0% -- well below the 3% floor
        {"job_function": "Legal", "posting_count": 20},  # 2.0% -- also below the floor
    ]
    tiles = _job_function_tiles(rows)
    by_name = _by_name(tiles)

    assert by_name["unknown"]["kind"] == "unknown"
    assert by_name["unknown"]["posting_count"] == 10, "unknown is never folded into the aggregate tile"
    aggregate = next(t for t in tiles if t["kind"] == "aggregate")
    assert aggregate["merged"] == ["Legal"]


def test_single_smaller_function_is_grammatically_singular():
    rows = [{"job_function": "Sales", "posting_count": 990}, {"job_function": "Legal", "posting_count": 10}]
    tiles = _job_function_tiles(rows)
    aggregate = next(t for t in tiles if t["kind"] == "aggregate")
    assert aggregate["job_function"] == "1 smaller function"


def test_no_small_functions_means_no_aggregate_tile():
    rows = [{"job_function": "Sales", "posting_count": 60}, {"job_function": "Marketing", "posting_count": 40}]
    tiles = _job_function_tiles(rows)
    assert not any(t["kind"] == "aggregate" for t in tiles)
    assert len(tiles) == 2


def test_shares_sum_to_roughly_100():
    rows = [{"job_function": "Sales", "posting_count": 33}, {"job_function": "Marketing", "posting_count": 33},
            {"job_function": "Legal", "posting_count": 34}]
    tiles = _job_function_tiles(rows)
    assert abs(sum(t["share"] for t in tiles) - 100.0) < 0.5


def test_empty_input_returns_empty_list():
    assert _job_function_tiles([]) == []


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

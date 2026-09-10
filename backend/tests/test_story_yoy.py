"""
Shape + honesty checks for the market-data-briefing year-on-year sections
(changes/2026-09-10-story-yoy-breakdowns.md).

Needs a DATABASE_URL (reads live aggregates). Run:
    cd backend/src && ./venv_linux/bin/python ../tests/test_story_yoy.py

Skips cleanly if no database is configured.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_SRC = Path(__file__).resolve().parent.parent / "src"
for _env in (_SRC.parent / ".env", _SRC / ".env"):
    if _env.exists():
        for line in _env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_HAS_DB = bool(os.environ.get("DATABASE_URL"))

_YOY_IDS = {"role-mix-shift", "seniority-shift", "track-shift"}


def _story():
    import market_stories
    return market_stories.build_market_data_briefing()


def test_yoy_sections_present_and_well_shaped():
    if not _HAS_DB:
        print("  (skipped — no DATABASE_URL)")
        return
    story = _story()
    by_id = {s["id"]: s for s in story["sections"]}
    for sid in _YOY_IDS:
        assert sid in by_id, f"{sid} section missing"
        sec = by_id[sid]
        c = sec["content"]
        assert c["dimension"] in {"role_category", "level", "track"}
        assert set(c["current_window"]) == {"start_date", "end_date"}
        assert isinstance(c["comparison_available"], bool)
        # current window is always ~365 days
        from datetime import date
        s, e = (date.fromisoformat(c["current_window"][k]) for k in ("start_date", "end_date"))
        assert timedelta(days=360) <= (e - s) <= timedelta(days=370)
        for row in c["rows"]:
            assert 0.0 <= row["current_share"] <= 1.0
            assert row["current_count"] >= 0
            if c["comparison_available"]:
                assert row["prior_share"] is not None and row["delta_pp"] is not None
            else:
                # never estimated / zero-filled when unavailable
                assert row["prior_count"] is None
                assert row["prior_share"] is None
                assert row["delta_pp"] is None


def test_insufficient_history_still_renders_current_window():
    if not _HAS_DB:
        print("  (skipped — no DATABASE_URL)")
        return
    story = _story()
    for sec in story["sections"]:
        if sec["id"] not in _YOY_IDS:
            continue
        c = sec["content"]
        if not c["comparison_available"]:
            # status must stay "ready" so the current window shows
            assert sec["status"] == "ready", f"{sec['id']} blanked instead of showing current window"
            assert c["prior_window"] is None
            assert "comparison starts" in sec["qualifier"].lower()
            assert c["rows"], f"{sec['id']} has no current-window rows"


def test_role_mix_shares_cover_only_tracked_categories():
    if not _HAS_DB:
        print("  (skipped — no DATABASE_URL)")
        return
    story = _story()
    rm = next(s for s in story["sections"] if s["id"] == "role-mix-shift")
    values = {row["value"] for row in rm["content"]["rows"]}
    assert values <= {"Designer", "Product Manager", "Engineer"}, values
    if rm["content"]["rows"]:
        assert abs(sum(r["current_share"] for r in rm["content"]["rows"]) - 1.0) < 0.01


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

"""
Unit tests for feedback_storage.py's pure, no-database logic — comment
normalization and story_id validation against the live catalogue. The
insert_*/get_feedback_summary/list_feedback_responses functions all need a
live Postgres connection and aren't covered here — same "test the parts that
don't need a live database" scope as test_scraping.py.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv_linux/bin/python ../tests/test_feedback.py
    (or, on Windows, ./venv/Scripts/python ../tests/test_feedback.py)

Every `test_*` function is a plain assert, same convention as
test_scraping.py / test_mcp_access.py / test_curated_match.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from feedback_storage import _normalize_comment, valid_story_ids  # noqa: E402
from market_stories import STORY_CATALOGUE  # noqa: E402


def test_normalize_comment_none_stays_none():
    assert _normalize_comment(None) is None


def test_normalize_comment_empty_string_becomes_none():
    assert _normalize_comment("") is None


def test_normalize_comment_whitespace_only_becomes_none():
    assert _normalize_comment("   \n\t  ") is None


def test_normalize_comment_strips_surrounding_whitespace_but_keeps_text():
    assert _normalize_comment("  Great tool!  ") == "Great tool!"


def test_normalize_comment_preserves_internal_whitespace():
    text = "Line one\nLine two"
    assert _normalize_comment(text) == text


def test_valid_story_ids_matches_the_live_catalogue():
    # Reuses market_stories.list_stories() rather than a duplicated list — a
    # story added to/removed from the catalogue must be reflected here with
    # no change to this test or to feedback_storage.py itself (backend/specs/
    # user-feedback/api.md — Business Logic — story_id validation).
    expected = {story["id"] for story in STORY_CATALOGUE}
    assert valid_story_ids() == expected
    assert len(expected) > 0, "the catalogue must not be empty for this test to be meaningful"


def test_valid_story_ids_rejects_an_unknown_id():
    assert "not-a-real-story-id" not in valid_story_ids()


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

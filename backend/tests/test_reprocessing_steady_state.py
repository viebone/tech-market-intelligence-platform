"""
The daily taxonomy-reprocessing step must do nothing — no paid work, no deletes — on a
steady-state day, and must only clear requirements for postings whose classification actually
changed.

From 2026-09-21 to 2026-10-10 it did the opposite: it treated every posting as stale, then
deleted every extracted requirements row, so the batch lane paid to re-read the same oldest 500
postings every day (9,500 batch slots, 1,056 distinct postings). Fixed by
changes/2026-10-10-requirements-re-extraction-loop.md.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_reprocessing_steady_state.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import classification  # noqa: E402
import ingest  # noqa: E402


class _Swap:
    """Swap attributes on a module for the duration of a `with` block, restore after."""
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


def _fail(name):
    def _raise(*a, **k):
        raise AssertionError(f"{name} must not be called")
    return _raise


def _row(pid, role="Engineer", track="ic", spec="Backend Engineer"):
    return {"id": pid, "role_category": role, "track": track, "specialization": spec}


# --- the steady-state guarantee -------------------------------------------------

def test_steady_state_day_does_no_work_and_deletes_nothing():
    deletes: list = []
    with _Swap(ingest, get_stale_for_reclassification=lambda version: [],
               reclassify_all=_fail("reclassify_all")), \
         _Swap(ingest.reqs, delete_requirements_for_reprocess=lambda ids: deletes.append(ids)):
        stats = asyncio.run(ingest.run_taxonomy_reprocessing_phase(already_used_today=0))
    assert deletes == []
    assert stats["total_classified"] == 0
    assert stats["llm_requests_used"] == 0


def test_stale_query_is_scoped_to_the_current_version():
    seen: list = []
    with _Swap(ingest, get_stale_for_reclassification=lambda version: seen.append(version) or []):
        asyncio.run(ingest.run_taxonomy_reprocessing_phase(already_used_today=0))
    assert seen == [classification.TAXONOMY_VERSION]


# --- only changed classifications clear requirements -----------------------------

def test_only_changed_postings_have_requirements_cleared():
    stale = [{"id": f"p{i}", "title": "Backend Engineer"} for i in range(100)]

    async def _fake_reclassify(postings, already_used_today=0):
        return {
            "cache_hits": 100, "heuristic_filtered": 0, "llm_classified": 0,
            "other_count": 0, "total_classified": 100, "stopped_early": False,
            "budget_reached": False, "llm_requests_used": 0,
            "changed_posting_ids": ["p3", "p50", "p99"],
        }

    deletes: list = []
    with _Swap(ingest, get_stale_for_reclassification=lambda version: stale,
               reclassify_all=_fake_reclassify), \
         _Swap(ingest.reqs, delete_requirements_for_reprocess=lambda ids: deletes.append(list(ids))):
        stats = asyncio.run(ingest.run_taxonomy_reprocessing_phase(already_used_today=0))
    assert deletes == [["p3", "p50", "p99"]]
    assert "changed_posting_ids" not in stats  # never leaks into ingestion_runs fields


def test_reprocessed_but_unchanged_postings_keep_requirements():
    async def _fake_reclassify(postings, already_used_today=0):
        return {
            "cache_hits": 54, "heuristic_filtered": 0, "llm_classified": 0,
            "other_count": 0, "total_classified": 54, "stopped_early": False,
            "budget_reached": False, "llm_requests_used": 0, "changed_posting_ids": [],
        }

    with _Swap(ingest, get_stale_for_reclassification=lambda v: [{"id": "x", "title": "t"}],
               reclassify_all=_fake_reclassify), \
         _Swap(ingest.reqs, delete_requirements_for_reprocess=_fail("delete_requirements_for_reprocess")):
        asyncio.run(ingest.run_taxonomy_reprocessing_phase(already_used_today=0))


def test_changed_posting_ids_compares_requirements_relevant_fields_only():
    prior = {
        "same": ("Engineer", "ic", "Backend Engineer"),
        "new_spec": ("Engineer", "ic", "Backend Engineer"),
        "new_track": ("Engineer", "ic", "Backend Engineer"),
        "new_role": ("Engineer", "ic", "Backend Engineer"),
    }
    rows = [
        {**_row("same"), "level": "senior", "classification_confidence": "low"},  # level/confidence don't count
        _row("new_spec", spec="Platform Engineer"),
        _row("new_track", track="management"),
        _row("new_role", role="Designer"),
        _row("no_prior_row"),
    ]
    assert classification.changed_posting_ids(prior, rows) == [
        "new_spec", "new_track", "new_role", "no_prior_row",
    ]


# --- reclassify_all writes cache hits and reports changes -----------------------

def test_reclassify_all_writes_cache_hits_and_makes_no_llm_call():
    """Stale postings whose title is already classified on the current version used to be
    counted but never written, so they stayed stale forever and re-triggered the step."""
    postings = [{"id": "a", "title": "Backend Engineer"}, {"id": "b", "title": "Product Designer"}]
    cache = {
        "Backend Engineer": {"role_category": "Engineer", "specialization": "Backend Engineer",
                             "level": "mid", "track": "ic", "classification_confidence": "high",
                             "job_function": None, "model": "gemini-2.5-flash"},
        "Product Designer": {"role_category": "Designer", "specialization": "Product Designer",
                             "level": "mid", "track": "ic", "classification_confidence": "high",
                             "job_function": None, "model": "gemini-2.5-flash"},
    }
    prior = {"a": ("Engineer", "ic", "Backend Engineer"), "b": ("Designer", "ic", "UX Designer")}
    written: list = []
    with _Swap(classification,
               _get_requirements_relevant_fields=lambda ids: prior,
               _get_title_cache_for_version=lambda titles, version: cache,
               update_classifications=lambda rows: written.extend(rows),
               classify_batch=_fail("classify_batch")):
        stats = asyncio.run(classification.reclassify_all(postings))
    assert sorted(r["id"] for r in written) == ["a", "b"]
    assert all(r["job_function"] is None and r["model"] == "gemini-2.5-flash" for r in written)
    assert stats["changed_posting_ids"] == ["b"]
    assert stats["llm_requests_used"] == 0
    assert stats["cache_hits"] == 2


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")

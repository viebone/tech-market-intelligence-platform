"""
Repeat-work guardrails for paid requirements extraction — backend/specs/market-health/api.md —
Business Logic — Repeat-work guardrails; changes/2026-10-10-requirements-re-extraction-loop.md
(Step 4); CLAUDE.md Rule 15.

What these pin down: a lane about to pay for postings it already paid for refuses to spend; a
daily run can't bulk-delete results; paid work always splits into new + repeats; a steady-state
day pays for nothing and deletes nothing.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_requirements_guard.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import batch_jobs  # noqa: E402
import ingest  # noqa: E402
import requirements as reqs  # noqa: E402
import requirements_guard as guard  # noqa: E402
from llm import providers  # noqa: E402


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


def _posting(pid, role="Engineer"):
    return {"id": pid, "source": "greenhouse", "raw_response": {"content": f"Build things. {pid}"},
            "role_category": role, "track": "ic", "specialization": "Backend Engineer"}


def _lookup(explained: set[str] = frozenset(), unexplained: set[str] = frozenset()):
    """A fake prior_extractions(): which ids were extracted before, and whether explained."""
    def _inner(ids):
        out = {}
        for pid in ids:
            if pid in explained:
                out[pid] = True
            elif pid in unexplained:
                out[pid] = False
        return out
    return _inner


class _SpyConnection:
    """Stands in for db.get_connection(): records every SQL statement, runs none."""
    def __init__(self, fetch=()):
        self.statements: list[str] = []
        self._fetch = list(fetch)
        self.rowcount = 0

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
        self.rows = list(rows)

    def fetchall(self):
        return self._fetch


# --- the rule itself ------------------------------------------------------------

def test_breaker_thresholds():
    assert not guard.is_blocked(selected=500, unexplained=0)
    assert not guard.is_blocked(selected=500, unexplained=50)      # exactly at both limits
    assert guard.is_blocked(selected=500, unexplained=51)          # over the count
    assert guard.is_blocked(selected=100, unexplained=11)          # over the share
    assert not guard.is_blocked(selected=100, unexplained=10)
    assert not guard.is_blocked(selected=0, unexplained=0)


def test_already_paid_selection_is_blocked():
    ids = [f"p{i}" for i in range(100)]
    check = guard.check_repeat_work(ids, lookup=_lookup(unexplained=set(ids)))
    assert check["blocked"] and check["unexplained"] == 100 and check["repeats"] == 100


def test_deliberate_reprocess_requests_explain_the_repeat():
    ids = [f"p{i}" for i in range(100)]
    check = guard.check_repeat_work(ids, lookup=_lookup(explained=set(ids)))
    assert not check["blocked"] and check["explained"] == 100 and check["unexplained"] == 0


def test_a_small_leak_passes_but_is_counted():
    ids = [f"p{i}" for i in range(100)]
    check = guard.check_repeat_work(ids, lookup=_lookup(unexplained={"p1", "p2", "p3", "p4", "p5"}))
    assert not check["blocked"] and check["repeats"] == 5
    assert check["repeat_ids"] == {"p1", "p2", "p3", "p4", "p5"}


def test_severest_guard_wins():
    assert guard.severest([]) == "ok"
    assert guard.severest(["batch_submit_incomplete", "repeat_work_blocked_batch"]) == "repeat_work_blocked_batch"
    assert guard.severest(["delete_cap_blocked", "batch_submit_incomplete"]) == "delete_cap_blocked"


# --- the delete cap ---------------------------------------------------------------

def test_daily_delete_over_cap_is_refused_before_any_sql():
    spy = _SpyConnection()
    ids = [f"p{i}" for i in range(guard.DAILY_REPROCESS_DELETE_CAP + 1)]
    with _Swap(reqs, get_connection=spy):
        try:
            reqs.delete_requirements_for_reprocess(ids, reason="classification_changed")
        except guard.RequirementsDeleteCapExceeded as exc:
            assert exc.attempted == len(ids)
        else:
            raise AssertionError("expected RequirementsDeleteCapExceeded")
    assert spy.statements == []


def test_daily_delete_at_cap_runs_and_records_reprocess_requests():
    spy = _SpyConnection()
    ids = [f"p{i}" for i in range(guard.DAILY_REPROCESS_DELETE_CAP)]
    with _Swap(reqs, get_connection=spy):
        reqs.delete_requirements_for_reprocess(ids, reason="classification_changed")
    assert any(s.startswith("DELETE FROM posting_requirements") for s in spy.statements)
    assert any(s.startswith("INSERT INTO requirements_reprocess_requests") for s in spy.statements)
    assert len(spy.rows) == len(ids)


def test_manual_bulk_delete_without_change_ref_is_refused():
    spy = _SpyConnection()
    with _Swap(reqs, get_connection=spy):
        try:
            reqs.delete_requirements_for_reprocess(["a"] * 3, reason="taxonomy_migration", allow_bulk=True)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for a bulk delete with no change_ref")
    assert spy.statements == []


# --- the ledger -------------------------------------------------------------------

def test_ledger_records_only_newly_extracted_postings():
    entry = {"education_level": "not_mentioned", "education_required": "not_mentioned",
             "equivalent_experience_accepted": False, "years_experience_min": None,
             "work_arrangement": "not_mentioned", "responsibilities_summary": None,
             "other_requirements": None, "skills": [], "languages": []}
    spy = _SpyConnection(fetch=[("already",)])
    with _Swap(reqs, get_connection=spy):
        reqs.insert_requirements([{**entry, "id": "already"}, {**entry, "id": "fresh"}], lane="batch", batch_job_id=7)
    ledger = [s for s in spy.statements if s.startswith("INSERT INTO requirements_extraction_ledger")]
    assert len(ledger) == 1
    assert [r[0] for r in spy.rows] == ["fresh"] and spy.rows[0][1] == "batch" and spy.rows[0][2] == 7


# --- both lanes -------------------------------------------------------------------

def test_interactive_lane_spends_nothing_when_blocked():
    postings = [_posting(f"p{i}") for i in range(30)]
    blocked = lambda ids: guard.check_repeat_work(ids, lookup=_lookup(unexplained=set(ids)))  # noqa: E731
    with _Swap(reqs, extract_batch=_fail("extract_batch"), insert_requirements=_fail("insert_requirements")):
        stats = asyncio.run(reqs.extract_requirements(postings, pre_spend_check=blocked))
    assert stats["guard"] is not None and stats["guard"]["blocked"]
    assert stats["paid"] == 0 and stats["requirements_requests_used"] == 0


def test_interactive_lane_splits_paid_into_new_and_repeats():
    postings = [_posting(f"p{i}") for i in range(10)]
    check = lambda ids: guard.check_repeat_work(ids, lookup=_lookup(explained={"p0", "p1"}))  # noqa: E731

    async def _fake_extract(batch, valid_skills, counter):
        counter["requests"] += 1
        return []

    with _Swap(reqs, extract_batch=_fake_extract, insert_requirements=lambda *a, **k: None,
               SECONDS_BETWEEN_BATCHES=0):
        stats = asyncio.run(reqs.extract_requirements(postings, pre_spend_check=check))
    assert stats["paid"] == 10 and stats["repeats"] == 2 and stats["new"] == 8
    assert stats["new"] + stats["repeats"] == stats["paid"]


def test_batch_lane_creates_no_job_and_submits_nothing_when_blocked():
    postings = [_posting(f"p{i}") for i in range(200)]
    blocked = lambda ids: guard.check_repeat_work(ids, lookup=_lookup(unexplained=set(ids)))  # noqa: E731
    with _Swap(ingest, count_needing_requirements=lambda: 200,
               get_all_needing_requirements=lambda limit=None: postings, check_repeat_work=blocked), \
         _Swap(batch_jobs, get_active_job=lambda: None, create_job=_fail("create_job")), \
         _Swap(providers, batch=_fail("providers.batch")):
        job_id, info = asyncio.run(ingest._maybe_submit_batch())
    assert job_id is None and info["blocked"]


def test_duplicated_id_takes_one_batch_slot():
    postings = [_posting(f"p{i}") for i in range(150)] + [_posting("p0"), _posting("p1")]
    created: list = []

    class _FakeBatch:
        async def submit(self, requests):
            return "ref-1"

    def _create(provider, model, ids, est):
        created.append(list(ids))
        return 99

    clean = lambda ids: guard.check_repeat_work(ids, lookup=_lookup())  # noqa: E731
    with _Swap(ingest, count_needing_requirements=lambda: 152,
               get_all_needing_requirements=lambda limit=None: postings, check_repeat_work=clean,
               _require_batch_key=lambda: "k"), \
         _Swap(batch_jobs, get_active_job=lambda: None, create_job=_create,
               set_provider_ref=lambda *a: None), \
         _Swap(providers, batch=lambda *a, **k: _FakeBatch()):
        job_id, info = asyncio.run(ingest._maybe_submit_batch())
    assert job_id == 99 and len(created[0]) == 150 == len(set(created[0]))
    assert info == {"paid": 150, "new": 150, "repeats": 0}


# --- the steady state (Rule 15) ----------------------------------------------------

def test_steady_state_day_pays_for_nothing_and_deletes_nothing():
    with _Swap(ingest, get_all_needing_requirements=lambda limit=None: [],
               count_needing_requirements=lambda: 0, get_requirements_requests_used_today=lambda: 0), \
         _Swap(batch_jobs, reconcile=lambda hours: [], get_active_job=lambda: None,
               create_job=_fail("create_job")), \
         _Swap(reqs, extract_batch=_fail("extract_batch"),
               delete_requirements_for_reprocess=_fail("delete_requirements_for_reprocess")), \
         _Swap(providers, batch=_fail("providers.batch")):
        result = asyncio.run(ingest.run_requirements_phase())
    assert result["requirements_paid"] == 0 and result["requirements_new"] == 0
    assert result["requirements_repeats"] == 0 and result["guards"] == []
    assert result["requirements_phase"] == "nothing_to_do"


def test_reprocessing_delete_cap_is_recorded_not_raised():
    async def _fake_reclassify(postings, already_used_today=0):
        return {"cache_hits": 300, "heuristic_filtered": 0, "llm_classified": 0, "other_count": 0,
                "total_classified": 300, "stopped_early": False, "budget_reached": False,
                "llm_requests_used": 0, "changed_posting_ids": [f"p{i}" for i in range(250)]}

    spy = _SpyConnection()
    with _Swap(ingest, get_stale_for_reclassification=lambda v: [{"id": "x", "title": "t"}],
               reclassify_all=_fake_reclassify), _Swap(reqs, get_connection=spy):
        stats = asyncio.run(ingest.run_taxonomy_reprocessing_phase(already_used_today=0))
    assert stats["guard"] == "delete_cap_blocked" and stats["guard_detail"]["attempted_deletes"] == 250
    assert stats["requirements_deleted"] == 0 and spy.statements == []
    assert stats["total_classified"] == 250 and stats["reclassified_unchanged"] == 50


def test_incomplete_submit_is_named_on_the_run():
    stuck = {"id": 30, "posting_ids": [], "model": "m", "error": "submit did not complete",
             "provider_job_ref": None}
    with _Swap(ingest, get_all_needing_requirements=lambda limit=None: [],
               count_needing_requirements=lambda: 0, get_requirements_requests_used_today=lambda: 0), \
         _Swap(batch_jobs, reconcile=lambda hours: [stuck], get_active_job=lambda: None):
        result = asyncio.run(ingest.run_requirements_phase())
    assert result["guards"] == ["batch_submit_incomplete"] and result["guard_detail"]["batch_job_id"] == 30


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"ok  {name}")
    print(f"{len(tests)} passed")

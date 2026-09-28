"""
ingest.py's per-company fault isolation (backend/src/ingest.py::ingest_company).

The requirement: a company that fails must never take any other company down with it. The fetch
side of this was always true (SourceFetchError is caught per company). The DB-write side was not
— a real production run (2026-09-27, changes/2026-09-26-personio-adapter.md) hit a transient
Postgres connection timeout inside insert_new_postings() for one Ashby company; it propagated out
of ingest_company() uncaught, was caught only by run()'s outer per-*adapter* try/except, and
skipped every remaining company in that adapter's list for the rest of the run — not just the one
unlucky company. Fixed 2026-09-30, changes/2026-09-30-ashby-db-write-isolation.md.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_ingest_isolation.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ingest  # noqa: E402
from sources.base import FetchedPosting, SourceFetchError  # noqa: E402


class _FakeAdapter:
    """A minimal stand-in for a real SourceAdapter — no network, no DB."""
    def __init__(self, name: str, postings_by_company: dict[str, list[FetchedPosting]] | None = None,
                 fail_companies: set[str] | None = None):
        self.name = name
        self._postings = postings_by_company or {}
        self._fail = fail_companies or set()

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        if company in self._fail:
            raise SourceFetchError(f"{self.name} request failed for {company}")
        return self._postings.get(company, [FetchedPosting(source_ref="1", company=company, title="Role", raw_response={})])


def _patched_insert(monkeypatch_fn):
    """Context manager: swap ingest.insert_new_postings for `monkeypatch_fn`, restore after."""
    class _Patch:
        def __enter__(self):
            self._saved = ingest.insert_new_postings
            ingest.insert_new_postings = monkeypatch_fn
            return self
        def __exit__(self, *a):
            ingest.insert_new_postings = self._saved
    return _Patch()


def test_fetch_failure_is_isolated_per_company_no_regression():
    adapter = _FakeAdapter("greenhouse", fail_companies={"broken-co"})
    with _patched_insert(lambda source, postings: [f"{source}:{p.source_ref}" for p in postings]):
        result = ingest.ingest_company(adapter, "broken-co")
    assert result == {"source": "greenhouse", "company": "broken-co", "fetched": 0, "inserted": 0,
                       "error": "greenhouse request failed for broken-co"}


def test_db_write_failure_is_now_isolated_per_company_the_real_fix():
    adapter = _FakeAdapter("ashby")

    def _raises(source, postings):
        raise ConnectionError("connection timeout expired")  # same shape as the real 2026-09-27 incident

    with _patched_insert(_raises):
        result = ingest.ingest_company(adapter, "thought-machine")
    # The old bug: this call used to raise straight out of ingest_company(), never returning at all.
    assert result["error"] == "connection timeout expired"
    assert result["source"] == "ashby" and result["company"] == "thought-machine"
    assert result["fetched"] == 1 and result["inserted"] == 0  # fetched successfully; only the write failed


def test_one_bad_company_no_longer_skips_the_rest_of_the_adapters_list():
    """Reproduces the actual production symptom: zego (after thought-machine in COMPANIES) was
    never attempted because the whole company loop aborted. With the fix, iterating adapter.companies
    and calling ingest_company() per company (exactly what run()'s loop does) processes every one."""
    adapter = _FakeAdapter("ashby")
    calls = {"n": 0}

    def _insert(source, postings):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("connection timeout expired")  # only the first company's write fails
        return [f"{source}:{p.source_ref}" for p in postings]

    companies = ["synthesia", "thought-machine", "zego"]  # real order from sources/ashby.py, at the time
    with _patched_insert(_insert):
        results = [ingest.ingest_company(adapter, c) for c in companies]

    assert [r["company"] for r in results] == companies  # all three attempted, none skipped
    assert results[0]["error"] is not None and results[0]["inserted"] == 0   # synthesia: DB write failed
    assert results[1]["error"] is None and results[1]["inserted"] == 1       # thought-machine: recovered, succeeded
    assert results[2]["error"] is None and results[2]["inserted"] == 1       # zego: never skipped


def test_success_path_unchanged():
    adapter = _FakeAdapter("workable")
    with _patched_insert(lambda source, postings: [f"{source}:{p.source_ref}" for p in postings]):
        result = ingest.ingest_company(adapter, "starling-bank")
    assert result == {"source": "workable", "company": "starling-bank", "fetched": 1, "inserted": 1, "error": None}


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"PASS {name}")
    print(f"{len(tests)}/{len(tests)} passed")

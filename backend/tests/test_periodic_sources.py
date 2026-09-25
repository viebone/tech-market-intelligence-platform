"""
The periodic-source runner (backend/src/ingest_periodic.py; changes/2026-09-25-periodic-source-ingestion-in-job-sync.md).

The requirement these tests exist to prove: ONE STEP FAILING MUST NEVER BOTHER THE OTHERS — nor `job-sync`. They run REAL child
processes (small throwaway scripts), because that is the property that matters: an exception, a hard exit, a crash, a hang and a
missing script are all different ways to go wrong, and only a separate process survives all of them.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_periodic_sources.py
"""

import ast
import os
import sys
import tempfile
import textwrap
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ingest_periodic as ip  # noqa: E402
from ingest_periodic import (  # noqa: E402
    FAILED, LAUNCH_FAILED, OK, PERIODIC_STEPS, SKIPPED_MISCONFIGURED, TIMED_OUT, PeriodicStep, missing_env,
    run_periodic_sources, run_step,
)

SRC = Path(__file__).resolve().parent.parent / "src"
PY = sys.executable


class Sandbox:
    """A temp dir of tiny scripts that behave in specific ways, plus a marker file each one writes when it runs."""
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def script(self, name: str, body: str) -> str:
        (self.dir / name).write_text(textwrap.dedent(body), encoding="utf-8")
        return name

    def ran(self, marker: str) -> bool:
        return (self.dir / marker).exists()

    def step(self, name: str, script: str, timeout: int = 20, env: tuple[str, ...] = ()) -> PeriodicStep:
        return PeriodicStep(name=name, script=script, timeout_seconds=timeout, required_env=env, description="test")

    def close(self):
        self._tmp.cleanup()


def _marker_script(marker: str, then: str = "") -> str:
    return f"from pathlib import Path; Path(__file__).with_name({marker!r}).write_text('ran')\n{then}\n"


def _run(sb: Sandbox, steps, **kw):
    return run_periodic_sources(steps, python=PY, src_dir=sb.dir, env=dict(os.environ), **kw)


# ── the isolation guarantees ──────────────────────────────────────────────────

def test_a_step_that_exits_nonzero_does_not_stop_the_next_one():
    sb = Sandbox()
    try:
        a = sb.step("a", sb.script("a.py", _marker_script("a.ran", "import sys; sys.exit(1)")))
        b = sb.step("b", sb.script("b.py", _marker_script("b.ran")))
        results = _run(sb, [a, b])
        assert [(r.name, r.status) for r in results] == [("a", FAILED), ("b", OK)]
        assert sb.ran("a.ran") and sb.ran("b.ran")
        assert results[0].exit_code == 1 and results[1].exit_code == 0
    finally:
        sb.close()


def test_an_unhandled_exception_in_a_step_is_contained():
    sb = Sandbox()
    try:
        a = sb.step("a", sb.script("a.py", _marker_script("a.ran", "raise RuntimeError('boom')")))
        b = sb.step("b", sb.script("b.py", _marker_script("b.ran")))
        results = _run(sb, [a, b])
        assert results[0].status == FAILED and results[1].status == OK and sb.ran("b.ran")
    finally:
        sb.close()


def test_a_hard_crash_is_contained():
    # os._exit skips every handler and finally block — the case in-process try/except can never survive
    sb = Sandbox()
    try:
        a = sb.step("a", sb.script("a.py", _marker_script("a.ran", "import os; os._exit(139)")))
        b = sb.step("b", sb.script("b.py", _marker_script("b.ran")))
        results = _run(sb, [a, b])
        assert results[0].status == FAILED and results[0].exit_code == 139
        assert results[1].status == OK and sb.ran("b.ran")
    finally:
        sb.close()


def test_a_hung_step_is_killed_at_its_timeout_and_the_next_still_runs():
    sb = Sandbox()
    try:
        hung = sb.step("hung", sb.script("hung.py", _marker_script("hung.ran", "import time; time.sleep(60)")), timeout=2)
        after = sb.step("after", sb.script("after.py", _marker_script("after.ran")))
        started = time.monotonic()
        results = _run(sb, [hung, after])
        elapsed = time.monotonic() - started
        assert results[0].status == TIMED_OUT and results[1].status == OK and sb.ran("after.ran")
        assert elapsed < 15, f"the hung step held everything up for {elapsed:.0f}s — the timeout did not kill it"
    finally:
        sb.close()


def test_a_missing_script_is_a_launch_failure_not_a_crash():
    sb = Sandbox()
    try:
        gone = sb.step("gone", "does_not_exist.py")
        b = sb.step("b", sb.script("b.py", _marker_script("b.ran")))
        results = _run(sb, [gone, b])
        assert results[0].status == LAUNCH_FAILED and "not found" in results[0].detail
        assert results[1].status == OK
    finally:
        sb.close()


def test_a_misconfigured_step_is_skipped_loudly_and_never_launched():
    sb = Sandbox()
    try:
        needs = sb.step("needs", sb.script("needs.py", _marker_script("needs.ran")), env=("PERIODIC_TEST_SECRET",))
        fine = sb.step("fine", sb.script("fine.py", _marker_script("fine.ran")))
        env = {k: v for k, v in os.environ.items() if k != "PERIODIC_TEST_SECRET"}
        results = run_periodic_sources([needs, fine], python=PY, src_dir=sb.dir, env=env)
        assert results[0].status == SKIPPED_MISCONFIGURED and not sb.ran("needs.ran"), "a misconfigured step must not be launched"
        assert "PERIODIC_TEST_SECRET" in results[0].detail
        assert results[1].status == OK and sb.ran("fine.ran")
        # blank counts as missing; a set value is never echoed
        assert missing_env(needs, {"PERIODIC_TEST_SECRET": "  "}) == ["PERIODIC_TEST_SECRET"]
        assert missing_env(needs, {"PERIODIC_TEST_SECRET": "s3cret"}) == []
        assert "s3cret" not in results[0].detail
    finally:
        sb.close()


def test_every_step_runs_even_when_all_of_them_fail():
    sb = Sandbox()
    try:
        steps = [sb.step(n, sb.script(f"{n}.py", _marker_script(f"{n}.ran", "import sys; sys.exit(2)"))) for n in ("a", "b", "c")]
        results = _run(sb, steps)
        assert [r.status for r in results] == [FAILED, FAILED, FAILED] and all(sb.ran(f"{n}.ran") for n in "abc")
    finally:
        sb.close()


def test_the_runner_never_raises_even_if_its_own_inputs_are_broken():
    # a step object that explodes when touched, and a src_dir that does not exist — neither may escape
    class Exploding:
        name = "explodes"
        script = "x.py"
        timeout_seconds = 1
        required_env = ()
        @property
        def description(self):
            raise RuntimeError("bug")
    sb = Sandbox()
    try:
        ok = sb.step("ok", sb.script("ok.py", _marker_script("ok.ran")))
        results = run_periodic_sources([Exploding(), ok], python=PY, src_dir=sb.dir, env=dict(os.environ))
        assert results[-1].status == OK and sb.ran("ok.ran")
        run_periodic_sources([ok], python=PY, src_dir=sb.dir / "nope", env=dict(os.environ))     # must simply not raise
    finally:
        sb.close()


def test_dry_run_runs_nothing_and_reports_configuration():
    sb = Sandbox()
    try:
        s = sb.step("s", sb.script("s.py", _marker_script("s.ran")))
        results = _run(sb, [s], dry_run=True)
        assert results[0].status == ip.DRY_RUN and not sb.ran("s.ran") and results[0].ok
    finally:
        sb.close()


def test_only_selects_one_step():
    sb = Sandbox()
    try:
        a = sb.step("a", sb.script("a.py", _marker_script("a.ran")))
        b = sb.step("b", sb.script("b.py", _marker_script("b.ran")))
        results = _run(sb, [a, b], only="b")
        assert [r.name for r in results] == ["b"] and sb.ran("b.ran") and not sb.ran("a.ran")
    finally:
        sb.close()


# ── the real registry and the real hook ───────────────────────────────────────

def test_the_real_steps_are_the_two_documented_ones_and_their_scripts_exist():
    assert [s.name for s in PERIODIC_STEPS] == ["trusted_statistics", "scraped_sources"]
    for step in PERIODIC_STEPS:
        assert (SRC / step.script).exists(), f"{step.script} is missing"
        assert step.timeout_seconds > 0 and step.required_env
    by = {s.name: s for s in PERIODIC_STEPS}
    assert by["trusted_statistics"].required_env == ("STATISTICS_CONTACT",)
    assert "SCRAPER_CONTACT" in by["scraped_sources"].required_env
    # employment events keep their own service and are deliberately not part of this runner
    assert not any("employment" in s.script for s in PERIODIC_STEPS)


def test_the_real_steps_are_configured_or_skipped_never_crashing_when_env_is_empty():
    results = run_periodic_sources(PERIODIC_STEPS, dry_run=True, env={})
    assert {r.status for r in results} == {SKIPPED_MISCONFIGURED}       # nothing launched; each names what is missing
    assert "STATISTICS_CONTACT" in results[0].detail and "SCRAPER_CONTACT" in results[1].detail


def test_ingest_py_calls_the_runner_after_its_work_inside_a_finally():
    tree = ast.parse((SRC / "ingest.py").read_text(encoding="utf-8"))
    main_if = next(n for n in tree.body if isinstance(n, ast.If) and "__name__" in ast.dump(n.test))
    try_node = next(n for n in main_if.body if isinstance(n, ast.Try))
    body_src = ast.dump(ast.Module(try_node.body, []))
    final_src = ast.dump(ast.Module(try_node.finalbody, []))
    assert "asyncio" in body_src and "run" in body_src, "the job-postings run must be the try body"
    assert "run_periodic_sources_safely" in final_src, "the periodic runner must be in the finally, after the postings work"
    assert not try_node.handlers, "no except clause: a failure of run() must still propagate exactly as before"


def test_the_scraped_sources_script_exits_nonzero_on_an_adapter_error():
    # otherwise the runner would report a failed scrape as "ok"
    src = (SRC / "ingest_scraped_sources.py").read_text(encoding="utf-8")
    assert "sys.exit(0 if run() else 1)" in src and "return not any_failed" in src


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

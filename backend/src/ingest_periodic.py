"""
Periodic source ingestion — the runner `job-sync` calls after its own daily work.

    python ingest_periodic.py                       # every periodic step
    python ingest_periodic.py --only trusted_statistics
    python ingest_periodic.py --dry-run             # say what WOULD run and whether it is configured; run nothing

WHY THIS EXISTS (changes/2026-09-25-periodic-source-ingestion-in-job-sync.md)
Some sources publish on their own slow calendar — the ONS Vacancy Survey monthly, IT Jobs Watch weekly by the
terms it granted — and nothing used to run them: a scheduler entry that has to be remembered is a scheduler entry
that gets forgotten (IT Jobs Watch was found 7 days overdue). Rather than one more Railway service to configure
and forget, the existing daily `job-sync` cron (the one piece known to run every day) calls this after its own work.

HOW IT KEEPS THE STEPS FROM BOTHERING EACH OTHER (a hard requirement)
- Each step is its OWN CHILD PROCESS with its OWN wall-clock timeout. That survives what try/except cannot: a
  crash, a hard exit, running out of memory, and — through the timeout — a hung network call. A step that fails,
  crashes, hangs or is misconfigured cannot touch another step, nor `job-sync` itself.
- Every step already enforces its OWN cadence gate in code (ONS: at most one release check per 20 h, and only
  releases at least 2 days old; IT Jobs Watch: at most every 7 days, before any request is made), so running this
  daily is safe and idempotent — a step that is not due makes no request at all.
- A step whose required environment is missing is SKIPPED with a loud ERROR naming the missing variable(s) (never
  their values) — it is not launched and does not count as a run, so it cannot start a cadence clock.
- `run_periodic_sources()` never raises. `ingest.py` calls it in a `finally`, so job postings keep priority, the
  periodic steps still get their attempt even if the postings run crashed, and nothing here can change job-sync's
  own outcome.
- The child's own log output streams straight into this process's output (Railway logs) in real time; this
  runner adds a header per step and ONE summary line at the end.

ADDING A PERIODIC SOURCE: add a `PeriodicStep` to PERIODIC_STEPS — a script that enforces its own cadence gate,
exits 0 on success/not-due and non-zero on failure, and names the env vars it needs. Then document it in
DEPLOYMENT.md (job-sync section) and DATA_SOURCES.md. Do NOT add a source without its own in-code cadence gate:
this runner fires daily and relies on it.

Employment events are deliberately NOT here — they have their own Railway service and weekly cron
(DEPLOYMENT.md — Service: `employment-events`).
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("ingest_periodic")

SRC_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PeriodicStep:
    name: str
    script: str                          # a file in backend/src, run as `python <script>`
    timeout_seconds: int                 # hard wall-clock limit; the child is killed when it expires
    required_env: tuple[str, ...]        # all must be set (non-blank) or the step is skipped, loudly
    description: str


PERIODIC_STEPS: tuple[PeriodicStep, ...] = (
    PeriodicStep(
        name="trusted_statistics",
        script="ingest_trusted_statistics.py",
        timeout_seconds=900,
        required_env=("STATISTICS_CONTACT",),
        description="ONS Vacancy Survey (monthly release). Own gates: one check per 20 h; a release is ingested only once "
                    "it is 2 days old; a file is downloaded only when a newer release exists.",
    ),
    PeriodicStep(
        name="scraped_sources",
        script="ingest_scraped_sources.py",
        timeout_seconds=1500,
        required_env=("SCRAPER_CONTACT", "GEMINI_API_KEY_CLASSIFICATION"),
        description="IT Jobs Watch (weekly, by the permission it granted). Own gate: at most every 7 days, checked before any "
                    "request; with a daily runner it drifts to about every 8 days, which respects 'at most weekly'.",
    ),
)

# statuses
OK = "ok"                                      # exited 0 (including 'not due yet' — that is a normal, quiet success)
FAILED = "failed"                              # exited non-zero
TIMED_OUT = "timed_out"                        # killed at its timeout
SKIPPED_MISCONFIGURED = "skipped_misconfigured"  # required env missing — not launched
LAUNCH_FAILED = "launch_failed"                # the child could not be started at all
RUNNER_ERROR = "runner_error"                  # a bug in this runner — still isolated from the other steps
DRY_RUN = "dry_run"


@dataclass(frozen=True)
class StepResult:
    name: str
    status: str
    duration_seconds: float
    exit_code: int | None
    detail: str

    @property
    def ok(self) -> bool:
        return self.status in (OK, DRY_RUN)


def missing_env(step: PeriodicStep, env: dict[str, str] | None = None) -> list[str]:
    """Names (never values) of required variables that are unset or blank."""
    env = os.environ if env is None else env
    return [name for name in step.required_env if not (env.get(name) or "").strip()]


def run_step(
    step: PeriodicStep,
    *,
    python: str | None = None,
    src_dir: Path | None = None,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> StepResult:
    """Run ONE step in its own child process. Never raises."""
    started = time.monotonic()
    try:
        missing = missing_env(step, env)
        if missing:
            detail = f"required environment not set: {', '.join(missing)} — step NOT run"
            logger.error("periodic step %r SKIPPED (misconfigured): %s", step.name, detail)
            return StepResult(step.name, SKIPPED_MISCONFIGURED, 0.0, None, detail)
        if dry_run:
            return StepResult(step.name, DRY_RUN, 0.0, None, f"would run {step.script} (timeout {step.timeout_seconds}s); environment OK")

        script = (src_dir or SRC_DIR) / step.script
        if not script.exists():
            detail = f"script not found: {script}"
            logger.error("periodic step %r LAUNCH FAILED: %s", step.name, detail)
            return StepResult(step.name, LAUNCH_FAILED, time.monotonic() - started, None, detail)

        logger.info("===== periodic step: %s (%s, timeout %ds) =====", step.name, step.script, step.timeout_seconds)
        for stream in (sys.stdout, sys.stderr):      # keep our header ordered ahead of the child's output
            try:
                stream.flush()
            except Exception:                        # noqa: BLE001 — a closed stream must not stop the step
                pass
        proc = subprocess.run(                       # output is inherited: the child's own logs stream live
            [python or sys.executable, str(script)],
            cwd=str(src_dir or SRC_DIR),
            env=env,
            timeout=step.timeout_seconds,
        )
        duration = time.monotonic() - started
        if proc.returncode == 0:
            return StepResult(step.name, OK, duration, 0, "exited 0")
        detail = f"exited with code {proc.returncode} — see this step's log output above"
        logger.error("periodic step %r FAILED: %s", step.name, detail)
        return StepResult(step.name, FAILED, duration, proc.returncode, detail)
    except subprocess.TimeoutExpired:
        detail = f"still running after {step.timeout_seconds}s — killed"
        logger.error("periodic step %r TIMED OUT: %s", step.name, detail)
        return StepResult(step.name, TIMED_OUT, time.monotonic() - started, None, detail)
    except OSError as exc:
        logger.error("periodic step %r LAUNCH FAILED: %s", step.name, exc)
        return StepResult(step.name, LAUNCH_FAILED, time.monotonic() - started, None, f"could not start: {exc}")
    except Exception as exc:                         # noqa: BLE001 — a bug here must still not reach the other steps
        logger.exception("periodic step %r runner error: %s", step.name, exc)
        return StepResult(step.name, RUNNER_ERROR, time.monotonic() - started, None, f"runner error: {exc}")


def run_periodic_sources(
    steps: tuple[PeriodicStep, ...] | list[PeriodicStep] = PERIODIC_STEPS,
    *,
    only: str | None = None,
    dry_run: bool = False,
    python: str | None = None,
    src_dir: Path | None = None,
    env: dict[str, str] | None = None,
) -> list[StepResult]:
    """Run every step, each isolated from the others, then log ONE summary line. Never raises."""
    results: list[StepResult] = []
    try:
        for step in steps:
            if only and step.name != only:
                continue
            results.append(run_step(step, python=python, src_dir=src_dir, env=env, dry_run=dry_run))
        summary = " | ".join(f"{r.name}={r.status} ({r.duration_seconds:.1f}s)" for r in results) or "no steps"
        problems = [r for r in results if not r.ok]
        if problems:
            logger.error("PERIODIC SOURCES SUMMARY: %s — %d step(s) need attention: %s", summary, len(problems),
                         "; ".join(f"{r.name}: {r.detail}" for r in problems))
        else:
            logger.info("PERIODIC SOURCES SUMMARY: %s", summary)
    except Exception as exc:                          # noqa: BLE001 — the last line of defence; nothing may escape
        logger.exception("periodic sources runner failed: %s", exc)
    return results


def run_periodic_sources_safely() -> None:
    """What ingest.py calls (in a `finally`). Swallows everything short of KeyboardInterrupt/SystemExit."""
    try:
        run_periodic_sources()
    except Exception as exc:                          # noqa: BLE001
        logger.exception("periodic sources could not run: %s", exc)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Run the periodic source ingestions, each isolated.")
    ap.add_argument("--only", choices=[s.name for s in PERIODIC_STEPS], help="run just this step")
    ap.add_argument("--dry-run", action="store_true", help="report what would run and whether it is configured; run nothing")
    args = ap.parse_args()
    results = run_periodic_sources(only=args.only, dry_run=args.dry_run)
    for r in results:
        print(f"{r.name}: {r.status} — {r.detail}")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

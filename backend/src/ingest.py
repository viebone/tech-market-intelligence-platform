"""
Daily ingestion + classification entry point for market-health.

Run manually or via an external scheduler (Railway cron in production — see
railway.json):
    python ingest.py

For each company in each source adapter's curated list (Greenhouse, Lever,
Ashby — see backend/src/sources/), fetches that company's full job board,
dedupes by id, stores new postings in raw_postings. Classification then runs
once across everything newly ingested (not once per company) so the
title-based dedup cache in classification.py sees the widest possible pool
before spending any LLM call. Every run — including a failed one — is
recorded in ingestion_runs, so its outcome is inspectable after the fact
instead of existing only as console output. See
backend/specs/market-health/api.md — Business Logic.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import batch_jobs
import requirements as reqs
import sampling
from classification import DAILY_REQUEST_BUDGET, TAXONOMY_VERSION, classify_postings, reclassify_all
from db import init_schema
from ingestion_runs import (
    get_requests_used_today,
    get_requirements_requests_used_today,
    record_run,
)
from llm import providers
from raw_postings import (
    attach_ingestion_run,
    count_needing_requirements,
    get_all_needing_requirements,
    get_all_unclassified,
    get_postings_by_ids,
    get_stale_for_reclassification,
    insert_new_postings,
)
from requirements import REQUIREMENTS_DAILY_REQUEST_BUDGET, extract_requirements
from requirements_guard import RequirementsDeleteCapExceeded, check_repeat_work, severest
from sources import ALL_SOURCE_ADAPTERS
from sources.base import SourceFetchError

# Batch catch-up lane provider — one line to switch providers, per
# outcomes/ai-provider-flexibility.md. Model matches the interactive lane's
# EXTRACTION_MODEL (both prepaid project); key is the same dedicated credential.
_BATCH_PROVIDER = "gemini"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_company(adapter, company: str, payloads: dict | None = None, pending: set | None = None) -> dict:
    """
    Fetch and store new postings for one (adapter, company) pair. Never
    raises — a company that still fails after the adapter's own retries are
    exhausted is recorded with its error rather than propagated, so one bad
    company can't abort the run. See backend/specs/market-health/api.md —
    Business Logic — Ingestion — Fault isolation, per company.

    The fetch and the DB write are isolated separately (added 2026-09-30 —
    changes/2026-09-30-ashby-db-write-isolation.md, a real gap this docstring's
    "never raises" promise didn't actually keep before). A transient DB failure
    during insert_new_postings() — a connection timeout hit in production
    2026-09-27, `changes/2026-09-26-personio-adapter.md` — previously escaped
    this function uncaught, was caught only by run()'s outer per-*adapter* try/
    except, and aborted every remaining company in that adapter's list for the
    run, not just the one company with the bad luck. Both `existing_ids()` and
    the insert itself open their own connection via `with get_connection()`, so
    a failure here never leaves a partial write to roll back — safe to catch
    broadly, same as the fetch side.

    `payloads` / `pending` (2026-10-23 — Business Logic — Sampling): the run's in-memory payload
    map. Every newly inserted posting, and every still-undecided posting seen on its board again,
    has its raw_response held here until sampling.run_decision_phase() keeps it or not. Nothing is
    staged in the database, so a crash just leaves postings pending for the next run.
    """
    try:
        postings = adapter.fetch_company(company)
    except SourceFetchError as exc:
        logger.error("ingest[%s/%s]: failed, skipping this company: %s", adapter.name, company, exc)
        return {"source": adapter.name, "company": company, "fetched": 0, "inserted": 0, "error": str(exc)}

    try:
        new_ids = insert_new_postings(adapter.name, postings)
    except Exception as exc:
        logger.error("ingest[%s/%s]: fetched %d but failed to store them: %s", adapter.name, company, len(postings), exc)
        return {"source": adapter.name, "company": company, "fetched": len(postings), "inserted": 0, "error": str(exc)}

    if payloads is not None:
        wanted = set(new_ids) | (pending or set())
        for p in postings:
            pid = f"{adapter.name}:{p.source_ref}"
            if pid in wanted:
                payloads[pid] = p.raw_response

    logger.info(
        "ingest[%s/%s]: fetched %d, inserted %d new",
        adapter.name, company, len(postings), len(new_ids),
    )
    return {"source": adapter.name, "company": company, "fetched": len(postings), "inserted": len(new_ids), "error": None}


def _severest_phase(*phases: str) -> str:
    """Most severe requirements_phase wins when several things happened in one
    run — see backend/specs/market-health/api.md — Data Models — IngestionRun."""
    order = ["interactive_failed", "batch_submit_failed", "batch_collect_failed", "nothing_to_do", "ok"]
    return min((p for p in phases if p), key=order.index, default="ok")


async def run_taxonomy_reprocessing_phase(already_used_today: int) -> dict:
    """
    Folded into the daily run (2026-09-21 — changes/2026-09-21-fold-reprocessing-into-
    ingest.md) so a future taxonomy revision never again needs a human to remember to
    manually re-trigger reprocess_taxonomy.py for several days in a row — this runs every
    day, forever, on the same permanent cron ingest.py already has, and does nothing at
    all on the overwhelming majority of days when nothing is stale (get_stale_for_
    reclassification() returning empty is the fast, common case, checked first).

    `already_used_today` must already include THIS run's own classify_postings() spend
    (caller passes get_requests_used_today() + stats["llm_requests_used"], not just the
    pre-run count) — the daily ceiling is shared across both steps within one run, not
    only across separate runs (see outcomes/llm-spend-is-bounded-and-isolated.md; this is
    the same shape of gap as the cross-run budget bug that outcome's own signal names,
    research/2026-08-05-cross-run-daily-budget-gap.md, just within one run instead of
    across runs).

    Deletes posting_requirements rows only for postings whose role_category/track/
    specialization actually changed in this call (2026-10-10), so the SAME run's
    requirements phase (which runs right after this) picks them back up immediately — an
    improvement over reprocess_taxonomy.py's original two-script version, which had to
    wait for a later run to notice.

    Returns the same stats shape as classify_postings()/reclassify_all(), all-zero/False
    when there was nothing stale to do, plus (2026-10-23 — Repeat-work guardrails)
    `requirements_deleted`, `reclassified_unchanged` and `guard`/`guard_detail`.
    `total_classified` counts only postings whose classification actually changed; identical
    rewrites go to `reclassified_unchanged`, so a steady-state day never reads as "N classified".
    """
    empty_stats = {
        "cache_hits": 0, "heuristic_filtered": 0, "llm_classified": 0,
        "other_count": 0, "total_classified": 0,
        "stopped_early": False, "budget_reached": False, "llm_requests_used": 0,
        "requirements_deleted": 0, "reclassified_unchanged": 0, "guard": "ok", "guard_detail": {},
    }
    stale_backlog = get_stale_for_reclassification(TAXONOMY_VERSION)
    if not stale_backlog:
        return empty_stats

    logger.info(
        "reclassify: %d postings on a stale taxonomy_version (current: %s)",
        len(stale_backlog), TAXONOMY_VERSION,
    )
    stats = await reclassify_all(stale_backlog, already_used_today=already_used_today)
    logger.info("reclassify: done: %s", stats)

    # Only postings whose role_category/track/specialization actually changed get
    # their requirements cleared — never "everything on the current version", which
    # wiped every extracted posting daily from 2026-09-21 to 2026-10-10
    # (changes/2026-10-10-requirements-re-extraction-loop.md).
    changed = stats.pop("changed_posting_ids", [])
    rewritten = stats["total_classified"]
    stats.update({
        "total_classified": len(changed),
        "reclassified_unchanged": max(0, rewritten - len(changed)),
        "requirements_deleted": 0, "guard": "ok", "guard_detail": {},
    })
    if changed:
        try:
            stats["requirements_deleted"] = reqs.delete_requirements_for_reprocess(
                changed, reason="classification_changed",
            )
            logger.info(
                "reclassify: %d of %d reprocessed postings changed classification; their "
                "requirements are cleared for re-extraction", len(changed), rewritten,
            )
        except RequirementsDeleteCapExceeded as exc:
            # Nothing was deleted. The classification rewrite stands; a re-read this large is a
            # planned, manual step (reprocess_taxonomy.py with a change_ref), never a daily one.
            logger.warning("reclassify: %s — run reprocess_taxonomy.py deliberately if intended", exc)
            stats["guard"] = "delete_cap_blocked"
            stats["guard_detail"] = {"attempted_deletes": exc.attempted, "delete_cap": exc.cap}
    return stats


async def run_requirements_phase() -> dict:
    """The three-step requirements phase (see backend/specs/market-health/api.md
    — Business Logic — Requirements extraction — Batch catch-up lane):

      1. collect a finished batch job (if any) through the shared extraction path
      2. run the interactive lane, unchanged
      3. maybe submit ONE new batch job

    Returns everything record_run() needs, including `requirements_phase`
    (`ok` / `nothing_to_do` / `interactive_failed` / `batch_submit_failed` /
    `batch_collect_failed`). Each step's failure is contained: it is recorded
    and does not abort the others.
    """
    result = {
        "requirements_extracted": 0, "requirements_requests_used": 0,
        "requirements_budget_reached": False, "stopped_early": False,
        "requirements_phase": "ok", "batch_collected": 0, "batch_submitted_id": None,
        # Repeat-work guardrails (2026-10-23): paid = new + repeats, always.
        "requirements_paid": 0, "requirements_new": 0, "requirements_repeats": 0,
        "guards": [], "guard_detail": {}, "requirements_reused": 0,
    }
    phases: list[str] = []

    # --- reconcile stale batch rows before anything else -------------------
    for job in batch_jobs.reconcile(reqs.BATCH_STUCK_AFTER_HOURS):
        for pid in job["posting_ids"]:
            reqs.record_extraction_failure(pid, job["error"] or "batch job failed", job["model"])
        if job["provider_job_ref"] is None:
            # The submit never came back (jobs 30/31, 2026-10-09/10). Name it on the run rather
            # than leaving the dashboard to show a quiet 0 collected.
            result["guards"].append("batch_submit_incomplete")
            result["guard_detail"]["batch_job_id"] = job["id"]

    # --- step 1: collect a finished batch --------------------------------
    active = batch_jobs.get_active_job()
    if active and active["provider_job_ref"]:
        try:
            provider = providers.batch(active["provider"], active["model"],
                                       api_key=_require_batch_key())
            state = await provider.poll(active["provider_job_ref"])
            if state == "running":
                batch_jobs.mark_running(active["id"])
            elif state == "failed":
                for pid in active["posting_ids"]:
                    reqs.record_extraction_failure(pid, "batch job failed provider-side", active["model"])
                batch_jobs.mark_failed(active["id"], "provider reported failure")
                logger.warning("requirements batch %d failed provider-side", active["id"])
            elif state == "succeeded":
                batch_results = await provider.fetch(active["provider_job_ref"])
                postings = get_postings_by_ids(active["posting_ids"])
                collected = reqs.collect_batch_results(batch_results, postings, active["model"],
                                                       batch_job_id=active["id"])
                batch_jobs.mark_collected(active["id"])
                result["batch_collected"] = collected
                logger.info("requirements batch %d collected: %d postings", active["id"], collected)
        except Exception as exc:  # noqa: BLE001
            logger.exception("requirements batch collect failed: %s", exc)
            phases.append("batch_collect_failed")

    # --- step 1b: duplicate reuse (2026-10-23) — free, before any paid lane ---
    try:
        result["requirements_reused"] = sampling.reuse_duplicate_extractions()
    except Exception as exc:  # noqa: BLE001
        logger.exception("requirements duplicate reuse failed (paid lanes continue): %s", exc)

    # --- step 2: interactive lane (unchanged) ----------------------------
    try:
        needing = get_all_needing_requirements()
        used_today = get_requirements_requests_used_today()
        logger.info("requirements: %d in backlog; %d/%d of today's interactive budget used",
                    len(needing), used_today, REQUIREMENTS_DAILY_REQUEST_BUDGET)
        stats = await extract_requirements(needing, already_used_today=used_today,
                                           pre_spend_check=check_repeat_work)
        result.update({
            "requirements_extracted": stats["requirements_extracted"],
            "requirements_requests_used": stats["requirements_requests_used"],
            "requirements_budget_reached": stats["requirements_budget_reached"],
            "stopped_early": stats["stopped_early"],
        })
        _add_paid(result, stats["paid"], stats["new"], stats["repeats"])
        if stats["guard"] is not None:
            _record_block(result, "repeat_work_blocked_interactive", stats["guard"])
        if stats["stopped_early"]:
            phases.append("interactive_failed")
    except Exception as exc:  # noqa: BLE001
        logger.exception("requirements interactive lane crashed: %s", exc)
        phases.append("interactive_failed")

    # --- step 3: maybe submit one batch --------------------------------
    try:
        submitted_id, submit_info = await _maybe_submit_batch()
        result["batch_submitted_id"] = submitted_id
        if submit_info.get("blocked"):
            _record_block(result, "repeat_work_blocked_batch", submit_info["check"])
        elif submitted_id is not None:
            _add_paid(result, submit_info["paid"], submit_info["new"], submit_info["repeats"])
    except Exception as exc:  # noqa: BLE001
        logger.exception("requirements batch submit failed: %s", exc)
        phases.append("batch_submit_failed")

    if not phases and result["batch_collected"] == 0 and result["requirements_extracted"] == 0 \
            and result["batch_submitted_id"] is None:
        phases.append("nothing_to_do")

    result["requirements_phase"] = _severest_phase(*phases)
    return result


def _guard_fields(reclassify_stats: dict, requirements_stats: dict) -> dict:
    """Fold both phases' safeguard outcomes into requirements_guard (most severe) and
    guard_detail (everything that fired). A guard firing never makes the run `partial`."""
    fired = list(requirements_stats["guards"])
    detail = dict(requirements_stats["guard_detail"])
    if reclassify_stats["guard"] != "ok":
        fired.append(reclassify_stats["guard"])
        detail.update(reclassify_stats["guard_detail"])
    if fired:
        detail["fired"] = fired
    return {"requirements_guard": severest(fired), "guard_detail": detail}


def _add_paid(result: dict, paid: int, new: int, repeats: int) -> None:
    result["requirements_paid"] += paid
    result["requirements_new"] += new
    result["requirements_repeats"] += repeats


def _record_block(result: dict, guard: str, check: dict) -> None:
    """A lane refused to spend. Not a phase failure — nothing broke and nothing was spent — so
    it goes to requirements_guard / guard_detail, never requirements_phase."""
    result["guards"].append(guard)
    result["guard_detail"][guard] = {
        k: check[k] for k in ("selected", "repeats", "explained", "unexplained", "unexplained_ids", "thresholds")
    }


def _require_batch_key() -> str:
    import os
    return os.environ["GEMINI_API_KEY_REQUIREMENTS"]


async def _maybe_submit_batch() -> tuple[int | None, dict]:
    """Submit one batch job iff the backlog is worth it, none is in flight, and the repeat-work
    circuit breaker passes (2026-10-23). Returns (new batch_jobs.id or None, info) where info
    carries paid/new/repeats for a submit, or {"blocked": True, "check": ...} when the breaker
    refused — in which case no batch_jobs row is written and nothing is submitted."""
    if batch_jobs.get_active_job() is not None:
        return None, {}
    backlog = count_needing_requirements()
    if backlog < reqs.REQUIREMENTS_BATCH_MIN_BACKLOG:
        return None, {}

    postings = get_all_needing_requirements(limit=reqs.MAX_BATCH_POSTINGS)
    postings = list({p["id"]: p for p in postings}.values())  # a duplicate id never takes a slot
    check = check_repeat_work([p["id"] for p in postings])
    if check["blocked"]:
        logger.warning(
            "requirements batch NOT submitted: %d of %d selected postings were already extracted "
            "with no reprocess request (thresholds: >%d or >%.0f%%)",
            check["unexplained"], check["selected"], check["thresholds"]["count"],
            check["thresholds"]["share"] * 100,
        )
        return None, {"blocked": True, "check": check}
    prepped = reqs.prep_postings(postings)
    est = reqs.estimate_batch_cost_usd(prepped)
    if est > reqs.MAX_BATCH_USD:
        logger.warning(
            "requirements batch NOT submitted: estimate $%.4f exceeds MAX_BATCH_USD $%.2f "
            "for %d postings — a human must decide whether to raise the cap",
            est, reqs.MAX_BATCH_USD, len(postings),
        )
        return None, {}

    posting_ids = [p["id"] for p in postings]
    model = reqs.EXTRACTION_MODEL
    # Row first, THEN submit — the batch API is not idempotent.
    job_id = batch_jobs.create_job(_BATCH_PROVIDER, model, posting_ids, est)
    provider = providers.batch(_BATCH_PROVIDER, model, api_key=_require_batch_key())
    job_ref = await provider.submit(reqs.build_batch_requests(prepped))
    batch_jobs.set_provider_ref(job_id, job_ref)
    logger.info(
        "requirements batch %d submitted: %d postings, est $%.4f, ref %s",
        job_id, len(posting_ids), est, job_ref,
    )
    repeats = sum(1 for pid in posting_ids if pid in check["repeat_ids"])
    return job_id, {"paid": len(posting_ids), "new": len(posting_ids) - repeats, "repeats": repeats}


async def run() -> None:
    init_schema()
    started_at = datetime.now(timezone.utc)
    terms_processed: list[dict] = []
    payloads: dict[str, dict] = {}
    sampling_stats = {"postings_kept": 0, "postings_not_kept": 0, "postings_pending": 0}

    try:
        pending = sampling.pending_ids() if sampling.is_sampling_live(started_at) else set()
        for adapter in ALL_SOURCE_ADAPTERS:
            try:
                for company in adapter.companies:
                    terms_processed.append(ingest_company(adapter, company, payloads, pending))
            except Exception as exc:
                # Adapter-level failure outside any single company's fetch
                # (e.g. a bug in that adapter's response parsing) — recorded,
                # but must not abort the other adapters. See
                # backend/specs/market-health/api.md — Business Logic —
                # Ingestion — Fault isolation, per adapter.
                logger.exception("ingest[%s]: adapter failed outside per-company isolation: %s", adapter.name, exc)
                terms_processed.append(
                    {"source": adapter.name, "company": None, "fetched": 0, "inserted": 0, "error": str(exc)}
                )

        total_fetched = sum(t["fetched"] for t in terms_processed)
        total_inserted = sum(t["inserted"] for t in terms_processed)
        any_company_failed = any(t["error"] is not None for t in terms_processed)

        unclassified = get_all_unclassified()
        logger.info("classify: %d unclassified postings across all sources", len(unclassified))
        already_used_today = get_requests_used_today()
        logger.info("classify: %d/%d of today's LLM request budget already used by prior runs",
                    already_used_today, DAILY_REQUEST_BUDGET)
        stats = await classify_postings(unclassified, already_used_today=already_used_today)

        # Taxonomy backlog reprocessing — see run_taxonomy_reprocessing_phase's own
        # docstring. Skipped entirely if classify_postings() itself hit a real error this
        # run (stopped_early) rather than piling more retries onto an already-bad day; a
        # clean budget_reached stop is not a reason to skip, since reprocessing has its
        # own independent (correctly reduced) share of whatever's left today.
        reclassify_stats = {
            "cache_hits": 0, "heuristic_filtered": 0, "llm_classified": 0,
            "other_count": 0, "total_classified": 0,
            "stopped_early": False, "budget_reached": False, "llm_requests_used": 0,
            "requirements_deleted": 0, "reclassified_unchanged": 0, "guard": "ok", "guard_detail": {},
        }
        if not stats["stopped_early"]:
            try:
                reclassify_stats = await run_taxonomy_reprocessing_phase(
                    already_used_today=already_used_today + stats["llm_requests_used"],
                )
            except Exception as exc:  # noqa: BLE001 — mirrors requirements phase's own per-step isolation
                logger.exception("reclassify: taxonomy backlog reprocessing failed: %s", exc)
                reclassify_stats["stopped_early"] = True

        # Sampling decisions (2026-10-23 — Business Logic — Sampling): once classified, each new
        # posting is kept in full or not, once. No model call, no delete. A failure here leaves
        # postings pending for the next run and never blocks the requirements phase.
        try:
            sampling_stats = sampling.run_decision_phase(payloads)
        except Exception as exc:  # noqa: BLE001
            logger.exception("sampling: decision phase failed, postings stay pending: %s", exc)
        payloads.clear()

        # Requirements extraction runs as its own phase after classification,
        # only over postings classification already confirmed are real roles.
        # Two lanes: the interactive lane (own dedicated daily budget) plus a
        # Batch catch-up lane that drains an accumulated backlog. See
        # backend/specs/market-health/api.md — Business Logic — Requirements
        # extraction, and backend/BATCH_PROCESSING.md.
        requirements_stats = await run_requirements_phase()

    except Exception as exc:
        # Something outside per-company/per-adapter fault isolation went
        # wrong (e.g. the database itself is unreachable) — this run
        # produced nothing usable.
        logger.exception("Ingestion run failed: %s", exc)
        run_id = record_run(
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            status="failed",
            terms_processed=terms_processed,
            error_message=str(exc),
        )
        # Postings may have already been inserted (in ingest_company()) before
        # whatever failed here — still attach them to this run rather than
        # leaving them permanently unattributed. See raw_postings.
        # attach_ingestion_run() and backend/specs/pipeline-visibility/api.md.
        attach_ingestion_run(run_id, started_at)
        raise

    # budget_reached alone is a clean, intentional stop, not a degradation —
    # only an actual error makes this "partial". A crash in the requirements
    # interactive lane (requirements_phase == "interactive_failed") counts, the
    # same way a failed classification batch does. A batch-lane failure does
    # NOT (the batch is retried; the run's own work succeeded) — see
    # backend/specs/market-health/api.md — Data Models — IngestionRun.
    # Taxonomy reprocessing's own stopped_early/budget_reached are OR'd in —
    # same "either step having a real problem makes the run partial" logic,
    # extended to the new step rather than tracked separately (no new
    # IngestionRun columns; see changes/2026-09-21-fold-reprocessing-into-
    # ingest.md — reprocessing stats are summed into the existing fields).
    status = "partial" if (
        any_company_failed
        or stats["stopped_early"]
        or reclassify_stats["stopped_early"]
        or requirements_stats["requirements_phase"] == "interactive_failed"
    ) else "success"
    run_id = record_run(
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        status=status,
        terms_processed=terms_processed,
        total_fetched=total_fetched,
        total_inserted=total_inserted,
        total_classified=stats["total_classified"] + reclassify_stats["total_classified"],
        cache_hits=stats["cache_hits"] + reclassify_stats["cache_hits"],
        heuristic_filtered=stats["heuristic_filtered"] + reclassify_stats["heuristic_filtered"],
        llm_classified=stats["llm_classified"] + reclassify_stats["llm_classified"],
        other_count=stats["other_count"] + reclassify_stats["other_count"],
        budget_reached=stats["budget_reached"] or reclassify_stats["budget_reached"],
        llm_requests_used=stats["llm_requests_used"] + reclassify_stats["llm_requests_used"],
        requirements_extracted=requirements_stats["requirements_extracted"],
        requirements_requests_used=requirements_stats["requirements_requests_used"],
        requirements_budget_reached=requirements_stats["requirements_budget_reached"],
        requirements_phase=requirements_stats["requirements_phase"],
        batch_collected=requirements_stats["batch_collected"],
        batch_submitted_id=requirements_stats["batch_submitted_id"],
        postings_kept=sampling_stats["postings_kept"],
        postings_not_kept=sampling_stats["postings_not_kept"],
        postings_pending=sampling_stats["postings_pending"],
        requirements_reused=requirements_stats["requirements_reused"],
        requirements_paid=requirements_stats["requirements_paid"],
        requirements_new=requirements_stats["requirements_new"],
        requirements_repeats=requirements_stats["requirements_repeats"],
        requirements_deleted=reclassify_stats["requirements_deleted"],
        reclassified_unchanged=reclassify_stats["reclassified_unchanged"],
        **_guard_fields(reclassify_stats, requirements_stats),
    )
    # ingestion_runs' row for this run only exists from this point on — see
    # ingestion_runs.record_run()'s docstring — so raw_postings.ingestion_run_id
    # is backfilled here rather than set at insert time.
    attach_ingestion_run(run_id, started_at)
    logger.info("ingestion run recorded: status=%s", status)


if __name__ == "__main__":
    # The periodic sources (ONS Vacancy Survey, IT Jobs Watch) ride this daily cron — see ingest_periodic.py's docstring and
    # changes/2026-09-25-periodic-source-ingestion-in-job-sync.md. They run AFTER the job-postings work (postings keep priority and
    # can never be delayed by them) and in a `finally` (they still get their attempt if the postings run raised). Each step is its own
    # child process with its own timeout and its own in-code cadence gate; run_periodic_sources_safely() never raises, so nothing it does
    # can change this job's own outcome — if run() raised, that exception still propagates exactly as before.
    try:
        asyncio.run(run())
    finally:
        from ingest_periodic import run_periodic_sources_safely

        run_periodic_sources_safely()

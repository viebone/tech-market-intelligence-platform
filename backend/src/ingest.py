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
from classification import DAILY_REQUEST_BUDGET, classify_postings
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
    insert_new_postings,
)
from requirements import REQUIREMENTS_DAILY_REQUEST_BUDGET, extract_requirements
from sources import ALL_SOURCE_ADAPTERS
from sources.base import SourceFetchError

# Batch catch-up lane provider — one line to switch providers, per
# outcomes/ai-provider-flexibility.md. Model matches the interactive lane's
# EXTRACTION_MODEL (both prepaid project); key is the same dedicated credential.
_BATCH_PROVIDER = "gemini"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_company(adapter, company: str) -> dict:
    """
    Fetch and store new postings for one (adapter, company) pair. Never
    raises — a company that still fails after the adapter's own retries are
    exhausted is recorded with its error rather than propagated, so one bad
    company can't abort the run. See backend/specs/market-health/api.md —
    Business Logic — Ingestion — Fault isolation, per company.
    """
    try:
        postings = adapter.fetch_company(company)
    except SourceFetchError as exc:
        logger.error("ingest[%s/%s]: failed, skipping this company: %s", adapter.name, company, exc)
        return {"source": adapter.name, "company": company, "fetched": 0, "inserted": 0, "error": str(exc)}

    new_ids = insert_new_postings(adapter.name, postings)
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
    }
    phases: list[str] = []

    # --- reconcile stale batch rows before anything else -------------------
    for job in batch_jobs.reconcile(reqs.BATCH_STUCK_AFTER_HOURS):
        for pid in job["posting_ids"]:
            reqs.record_extraction_failure(pid, job["error"] or "batch job failed", job["model"])

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
                collected = reqs.collect_batch_results(batch_results, postings, active["model"])
                batch_jobs.mark_collected(active["id"])
                result["batch_collected"] = collected
                logger.info("requirements batch %d collected: %d postings", active["id"], collected)
        except Exception as exc:  # noqa: BLE001
            logger.exception("requirements batch collect failed: %s", exc)
            phases.append("batch_collect_failed")

    # --- step 2: interactive lane (unchanged) ----------------------------
    try:
        needing = get_all_needing_requirements()
        used_today = get_requirements_requests_used_today()
        logger.info("requirements: %d in backlog; %d/%d of today's interactive budget used",
                    len(needing), used_today, REQUIREMENTS_DAILY_REQUEST_BUDGET)
        stats = await extract_requirements(needing, already_used_today=used_today)
        result.update({
            "requirements_extracted": stats["requirements_extracted"],
            "requirements_requests_used": stats["requirements_requests_used"],
            "requirements_budget_reached": stats["requirements_budget_reached"],
            "stopped_early": stats["stopped_early"],
        })
        if stats["stopped_early"]:
            phases.append("interactive_failed")
    except Exception as exc:  # noqa: BLE001
        logger.exception("requirements interactive lane crashed: %s", exc)
        phases.append("interactive_failed")

    # --- step 3: maybe submit one batch --------------------------------
    try:
        submitted_id = await _maybe_submit_batch()
        result["batch_submitted_id"] = submitted_id
    except Exception as exc:  # noqa: BLE001
        logger.exception("requirements batch submit failed: %s", exc)
        phases.append("batch_submit_failed")

    if not phases and result["batch_collected"] == 0 and result["requirements_extracted"] == 0 \
            and result["batch_submitted_id"] is None:
        phases.append("nothing_to_do")

    result["requirements_phase"] = _severest_phase(*phases)
    return result


def _require_batch_key() -> str:
    import os
    return os.environ["GEMINI_API_KEY_REQUIREMENTS"]


async def _maybe_submit_batch() -> int | None:
    """Submit one batch job iff the backlog is worth it and none is in flight.
    Returns the new batch_jobs.id, or None."""
    if batch_jobs.get_active_job() is not None:
        return None
    backlog = count_needing_requirements()
    if backlog < reqs.REQUIREMENTS_BATCH_MIN_BACKLOG:
        return None

    postings = get_all_needing_requirements(limit=reqs.MAX_BATCH_POSTINGS)
    prepped = reqs.prep_postings(postings)
    est = reqs.estimate_batch_cost_usd(prepped)
    if est > reqs.MAX_BATCH_USD:
        logger.warning(
            "requirements batch NOT submitted: estimate $%.4f exceeds MAX_BATCH_USD $%.2f "
            "for %d postings — a human must decide whether to raise the cap",
            est, reqs.MAX_BATCH_USD, len(postings),
        )
        return None

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
    return job_id


async def run() -> None:
    init_schema()
    started_at = datetime.now(timezone.utc)
    terms_processed: list[dict] = []

    try:
        for adapter in ALL_SOURCE_ADAPTERS:
            try:
                for company in adapter.companies:
                    terms_processed.append(ingest_company(adapter, company))
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
    status = "partial" if (
        any_company_failed
        or stats["stopped_early"]
        or requirements_stats["requirements_phase"] == "interactive_failed"
    ) else "success"
    run_id = record_run(
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        status=status,
        terms_processed=terms_processed,
        total_fetched=total_fetched,
        total_inserted=total_inserted,
        total_classified=stats["total_classified"],
        cache_hits=stats["cache_hits"],
        heuristic_filtered=stats["heuristic_filtered"],
        llm_classified=stats["llm_classified"],
        other_count=stats["other_count"],
        budget_reached=stats["budget_reached"],
        llm_requests_used=stats["llm_requests_used"],
        requirements_extracted=requirements_stats["requirements_extracted"],
        requirements_requests_used=requirements_stats["requirements_requests_used"],
        requirements_budget_reached=requirements_stats["requirements_budget_reached"],
        requirements_phase=requirements_stats["requirements_phase"],
        batch_collected=requirements_stats["batch_collected"],
        batch_submitted_id=requirements_stats["batch_submitted_id"],
    )
    # ingestion_runs' row for this run only exists from this point on — see
    # ingestion_runs.record_run()'s docstring — so raw_postings.ingestion_run_id
    # is backfilled here rather than set at insert time.
    attach_ingestion_run(run_id, started_at)
    logger.info("ingestion run recorded: status=%s", status)


if __name__ == "__main__":
    asyncio.run(run())

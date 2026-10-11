"""
One-time taxonomy reprocessing pass (2026-08-11) — see
backend/specs/market-health/api.md — Business Logic — Taxonomy reprocessing,
and changes/2026-08-11-classification-taxonomy-redesign.md.

Deliberately a separate script, not folded into ingest.py: this is one-time
migration work, not a recurring daily concern, and keeping it out of
ingest.py's main flow avoids permanently complicating the ongoing pipeline
with logic that becomes dead weight once the backlog clears.

Safe to run repeatedly (same "Run now" pattern as ingest.py) — each
invocation only touches what's still on a stale taxonomy_version, so a
multi-day reprocessing pass naturally converges to zero remaining work.
Shares classification's existing daily budget/key (this is a larger-than-
usual backlog on the same budget, not a separately budgeted concern), and
requirements' own separate daily budget, same as ongoing operation.

Run manually:
    python reprocess_taxonomy.py

Two phases, in order every invocation — the order matters (see api.md):
  1. Classification reprocessing — reclassifies every posting still on a stale
     taxonomy_version from its title onto the current TAXONOMY_VERSION.
  2. Requirements reprocessing — deletes posting_requirements/posting_skills/
     posting_languages rows only for postings whose role_category/track/
     specialization actually changed in step 1, so the normal ingest.py backlog
     query picks them back up and re-extracts them under the new taxonomy.
     (Corrected 2026-10-10 — it used to delete every extracted posting on the
     current version; changes/2026-10-10-requirements-re-extraction-loop.md.)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from classification import DAILY_REQUEST_BUDGET, TAXONOMY_VERSION, reclassify_all
from db import init_schema
from ingestion_runs import get_requests_used_today, record_run
from raw_postings import get_stale_for_reclassification
from requirements import delete_requirements_for_reprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run() -> None:
    init_schema()
    started_at = datetime.now(timezone.utc)

    all_postings = get_stale_for_reclassification(TAXONOMY_VERSION)
    logger.info(
        "reprocess_taxonomy: %d postings on a stale taxonomy_version (current: %s)",
        len(all_postings), TAXONOMY_VERSION,
    )
    already_used_today = get_requests_used_today()
    logger.info(
        "reprocess_taxonomy: %d/%d of today's classification request budget already used "
        "(shared with ongoing daily classification)",
        already_used_today, DAILY_REQUEST_BUDGET,
    )
    classify_stats = await reclassify_all(all_postings, already_used_today=already_used_today)
    logger.info("reprocess_taxonomy: classification phase done: %s", classify_stats)

    # Ordering dependency (api.md — Business Logic — Taxonomy reprocessing): the
    # delete runs after the rewrite, and only for postings whose role_category/
    # track/specialization actually changed — never "everything on the current
    # version" (changes/2026-10-10-requirements-re-extraction-loop.md).
    reprocess_targets = classify_stats.pop("changed_posting_ids", [])
    logger.info(
        "reprocess_taxonomy: %d reprocessed postings changed classification; clearing their "
        "requirements for re-extraction", len(reprocess_targets),
    )
    delete_requirements_for_reprocess(reprocess_targets)

    status = "partial" if classify_stats["stopped_early"] else "success"
    record_run(
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        status=status,
        terms_processed=[],
        total_classified=classify_stats["total_classified"],
        cache_hits=classify_stats["cache_hits"],
        heuristic_filtered=classify_stats["heuristic_filtered"],
        llm_classified=classify_stats["llm_classified"],
        other_count=classify_stats["other_count"],
        budget_reached=classify_stats["budget_reached"],
        llm_requests_used=classify_stats["llm_requests_used"],
    )
    logger.info(
        "reprocess_taxonomy run recorded: status=%s. Deleted requirements for %d postings — "
        "they will be re-extracted by the next normal ingest.py run's requirements phase.",
        status, len(reprocess_targets),
    )


if __name__ == "__main__":
    asyncio.run(run())

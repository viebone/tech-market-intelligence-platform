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
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from classification import classify_postings
from db import init_schema
from ingestion_runs import record_run
from raw_postings import get_all_unclassified, insert_new_postings
from sources import ALL_SOURCE_ADAPTERS
from sources.base import SourceFetchError

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
        stats = await classify_postings(unclassified)

    except Exception as exc:
        # Something outside per-company/per-adapter fault isolation went
        # wrong (e.g. the database itself is unreachable) — this run
        # produced nothing usable.
        logger.exception("Ingestion run failed: %s", exc)
        record_run(
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            status="failed",
            terms_processed=terms_processed,
            error_message=str(exc),
        )
        raise

    status = "partial" if (any_company_failed or stats["stopped_early"]) else "success"
    record_run(
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        status=status,
        terms_processed=terms_processed,
        total_fetched=total_fetched,
        total_inserted=total_inserted,
        total_classified=stats["total_classified"],
        cache_hits=stats["cache_hits"],
        llm_classified=stats["llm_classified"],
        other_count=stats["other_count"],
    )
    logger.info("ingestion run recorded: status=%s", status)


if __name__ == "__main__":
    asyncio.run(run())

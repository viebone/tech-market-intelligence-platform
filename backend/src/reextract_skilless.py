"""
One-time requirements re-extraction for postings that got a `posting_requirements` row but
**zero `posting_skills`** — likely a genuine extraction miss, not "the posting lists no
skills". Deletes their requirements/skills/languages rows and re-extracts via the Gemini
**Batch API** on `GEMINI_API_KEY_REQUIREMENTS`.

See `changes/2026-09-06-unknown-reclassification.md`.

Run manually (backend/src/, requirements venv), naming the change request that authorises the
re-read (2026-10-23 — Repeat-work guardrails):
    python reextract_skilless.py --change-ref 2026-09-06-unknown-reclassification

Safe to re-run: it only picks postings still in the zero-skill state. Prints the batch job
ref. Not wired into `ingest.py`.

Note: `not_mentioned` education / work-arrangement and NULL years-of-experience are NOT
targeted — those are usually correct (the posting genuinely doesn't say), so re-extracting
them is wasted spend. Only the zero-skills case is a reliable "the extractor missed" signal.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

import requirements as reqs  # noqa: E402
from db import get_connection, init_schema  # noqa: E402
from llm import providers  # noqa: E402
from raw_postings import get_postings_by_ids  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30


def _zero_skill_ids() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT pr.posting_id
            FROM posting_requirements pr
            JOIN classifications c ON c.posting_id = pr.posting_id
            WHERE c.role_category IN ('Designer', 'Product Manager', 'Engineer')
              AND NOT EXISTS (SELECT 1 FROM posting_skills ps WHERE ps.posting_id = pr.posting_id)
            """
        ).fetchall()
    return [r[0] for r in rows]


async def main(change_ref: str) -> None:
    init_schema()

    ids = _zero_skill_ids()
    if not ids:
        print("Nothing to do — no extracted postings are missing skills.")
        return
    print(f"{len(ids)} extracted postings have zero skills — re-extracting.")

    postings = get_postings_by_ids(ids)
    # so ON CONFLICT DO NOTHING doesn't block re-insert; records reprocess requests so the re-read
    # is an explained repeat (2026-10-23 — Repeat-work guardrails)
    reqs.delete_requirements_for_reprocess(ids, reason="skill_gap_reextract", change_ref=change_ref,
                                           allow_bulk=True)

    prepped = reqs.prep_postings(postings)
    requests = reqs.build_batch_requests(prepped)

    batch = providers.batch("gemini", reqs.EXTRACTION_MODEL,
                             api_key=os.environ["GEMINI_API_KEY_REQUIREMENTS"])
    job_ref = await batch.submit(requests)
    print(f"Batch submitted — job ref: {job_ref} ({len(requests)} grouped requests)")
    print("Polling to completion (Ctrl+C is safe; re-run to resume)...")

    while True:
        state = await batch.poll(job_ref)
        print(f"  state: {state}")
        if state == "succeeded":
            break
        if state == "failed":
            raise SystemExit(f"Batch job failed provider-side: {job_ref}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    results = await batch.fetch(job_ref)
    inserted = reqs.collect_batch_results(results, postings, reqs.EXTRACTION_MODEL)

    with get_connection() as conn:
        still_zero = conn.execute(
            """
            SELECT count(*) FROM posting_requirements pr
            WHERE pr.posting_id = ANY(%s)
              AND NOT EXISTS (SELECT 1 FROM posting_skills ps WHERE ps.posting_id = pr.posting_id)
            """,
            (ids,),
        ).fetchone()[0]

    print()
    print(f"Re-extracted {inserted} requirements rows for {len(ids)} postings.")
    print(f"{len(ids) - still_zero} now have at least one skill; {still_zero} still have none "
          "(the posting genuinely lists no skills, or extraction failed again).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-extract postings that have requirements but no skills.")
    parser.add_argument("--change-ref", required=True, help="the change request authorising this re-read")
    asyncio.run(main(parser.parse_args().change_ref))

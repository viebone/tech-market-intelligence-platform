"""
One-time description-assisted recovery pass for classification gaps.

The main classification path is title-only by design, so any of role_category /
specialization / level / track can come back "unknown" when the title alone doesn't disclose
it (e.g. "Software Engineer" — no seniority word, so level is "unknown"). This pass
re-examines every posting with at least one "unknown" field, adding the **job description**,
and lets the model fill the gaps the description discloses. See
`changes/2026-09-06-unknown-reclassification.md` and `backend/specs/market-health/api.md` —
Business Logic — Classification — description-assisted recovery pass.

Run manually (backend/src/, classification venv):
    python reclassify_unknowns.py

Safe to re-run: only re-attempts rows still carrying a gap that this pass has not already
marked with its own `model` value (`classification.CLASSIFICATION_RECOVERY_MODEL` — bump the
model suffix there to force a redo with a newer model). Uses the Gemini **Batch API** on
`GEMINI_API_KEY_CLASSIFICATION` — off the interactive per-day request quota, Batch pricing.
Prints the batch job ref so an interrupted run can be checked in the Gemini console. Not
wired into `ingest.py`; not part of the daily pipeline.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from classification import (  # noqa: E402
    CLASSIFICATION_RECOVERY_MODEL,
    RECOVERY_MODEL,
    RECOVERY_SYSTEM_INSTRUCTION,
    _parse_response,
    _validate,
    build_unknown_recovery_prompt,
    update_classifications,
)
from db import get_connection, init_schema  # noqa: E402
from llm import providers  # noqa: E402
from llm.base import BatchRequest  # noqa: E402
from requirements import _extract_description  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30


def _fetch_unknowns() -> list[dict]:
    """Postings with at least one 'unknown' classification field that this pass hasn't
    already re-examined, oldest first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.posting_id, rp.title, rp.source, rp.raw_response
            FROM classifications c
            JOIN raw_postings rp ON rp.id = c.posting_id
            WHERE (c.role_category = 'unknown'
                   OR c.specialization = 'unknown'
                   OR c.level = 'unknown'
                   OR c.track = 'unknown')
              AND c.model IS DISTINCT FROM %s
            ORDER BY rp.fetched_at ASC
            """,
            (CLASSIFICATION_RECOVERY_MODEL,),
        ).fetchall()

    out: list[dict] = []
    for posting_id, title, source, raw_response in rows:
        description = _extract_description(source or "", raw_response or {})
        out.append({"id": posting_id, "title": title, "description": description})
    return out


async def main() -> None:
    init_schema()

    unknowns = _fetch_unknowns()
    if not unknowns:
        print("Nothing to do — no classification gaps left for this pass to re-examine.")
        return

    with_desc = sum(1 for p in unknowns if p["description"])
    print(f"{len(unknowns)} postings with a classification gap to re-examine "
          f"({with_desc} have a usable description), via {RECOVERY_MODEL}.")

    requests = [
        BatchRequest(
            custom_id=p["id"],
            prompt=build_unknown_recovery_prompt(p),
            system=RECOVERY_SYSTEM_INSTRUCTION,
        )
        for p in unknowns
    ]

    batch = providers.batch(
        "gemini", RECOVERY_MODEL, api_key=os.environ["GEMINI_API_KEY_CLASSIFICATION"]
    )
    job_ref = await batch.submit(requests)
    print(f"Batch submitted — job ref: {job_ref}")
    print("Polling to completion (Ctrl+C is safe; re-run to resume from the same set)...")

    while True:
        state = await batch.poll(job_ref)
        print(f"  state: {state}")
        if state == "succeeded":
            break
        if state == "failed":
            raise SystemExit(f"Batch job failed provider-side: {job_ref}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

    results = await batch.fetch(job_ref)

    updates: list[dict] = []
    failed = 0
    for r in results:
        if r.error or not r.text:
            failed += 1
            logger.warning("no result for %s: %s", r.custom_id, r.error or "empty")
            continue
        parsed = _parse_response(r.text)
        entry = parsed[0] if isinstance(parsed, list) and parsed else (parsed if isinstance(parsed, dict) else None)
        if not isinstance(entry, dict):
            failed += 1
            logger.warning("unparseable result for %s: %r", r.custom_id, r.text[:200])
            continue
        validated = _validate(entry)
        validated["id"] = r.custom_id            # trust the batch's custom_id, not the model echo
        validated["model"] = CLASSIFICATION_RECOVERY_MODEL
        updates.append(validated)

    still_unknown = Counter()
    for u in updates:
        for field in ("role_category", "specialization", "level", "track"):
            if u.get(field) == "unknown":
                still_unknown[field] += 1

    update_classifications(updates)

    role_outcome = Counter(u["role_category"] for u in updates)
    tracked = {"Designer", "Product Manager", "Engineer"}

    print()
    print(f"Applied {len(updates)} updates ({failed} unparseable/failed).")
    print("role_category:", dict(role_outcome.most_common()))
    print("fields still 'unknown' after the description pass:", dict(still_unknown))
    print(f"{sum(n for c, n in role_outcome.items() if c in tracked)} rows now have a tracked "
          f"role_category; {role_outcome.get('other', 0)} -> other; "
          f"{role_outcome.get('unknown', 0)} role_category still unknown.")


if __name__ == "__main__":
    asyncio.run(main())

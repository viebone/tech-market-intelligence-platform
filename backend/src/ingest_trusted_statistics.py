"""
Trusted external statistics ingestion entry point.

    python ingest_trusted_statistics.py                      # every registered publisher
    python ingest_trusted_statistics.py --source ons_vacancy_survey
    python ingest_trusted_statistics.py --force              # ignore the cadence gate (use sparingly)

Safe to invoke as often as you like from any scheduler — the once-a-day check cadence is enforced in
code (trusted_stats.base.ingest_adapter, against statistics_ingestion_runs), BEFORE any request is made,
so a run that is not due makes no network request at all and constructs nothing. A new publisher release
is downloaded only when its own release date is newer than what is stored; an unchanged file or value is
never re-stored. Idempotent.

Requires STATISTICS_CONTACT (a real contact, used in the User-Agent on every request) — refuses to run
otherwise. See backend/.env.example.

Deliberately its own entry point (not folded into ingest.py / ingest_scraped_sources.py): a different
data shape, a different fetch mechanism (a publisher's own data files, no HTML), and its own cadence.

Spec: backend/specs/trusted-statistics/api.md; map and recipe: backend/TRUSTED_STATISTICS.md.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from db import init_schema  # noqa: E402
from statistics_storage import PostgresStatisticsStorage  # noqa: E402
from trusted_stats import ALL_STATISTICS_ADAPTERS, PoliteFetcher, StatisticsConfigError, ingest_adapter  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest trusted external statistics.")
    ap.add_argument("--source", help="only this publisher (a TRUSTED_PUBLISHERS key)")
    ap.add_argument("--force", action="store_true", help="ignore the cadence gate")
    args = ap.parse_args()

    init_schema()
    storage = PostgresStatisticsStorage()
    adapters = [a for a in ALL_STATISTICS_ADAPTERS if not args.source or a.source == args.source]
    if not adapters:
        print(f"no registered adapter named {args.source!r}", file=sys.stderr)
        return 2

    exit_code = 0
    for adapter in adapters:
        try:
            result = ingest_adapter(adapter, storage, lambda a=adapter: PoliteFetcher(a.source), force=args.force)
        except StatisticsConfigError as exc:
            logger.error("ingest_trusted_statistics[%s]: refused to run: %s", adapter.source, exc)
            exit_code = 1
            continue
        except Exception as exc:                       # one publisher failing must never stop the others
            logger.exception("ingest_trusted_statistics[%s]: failed: %s", adapter.source, exc)
            exit_code = 1
            continue
        print(f"{adapter.source}: {result.outcome}")
        for m in result.messages:
            print(f"  {m}")
        if result.outcome in ("rejected_validation", "failed"):
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

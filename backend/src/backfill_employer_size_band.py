"""
One-off backfill: re-derive raw_postings.employer_size_band from employer_headcount.py.

    python backfill_employer_size_band.py                # DRY RUN (default): prints what would change, writes nothing
    python backfill_employer_size_band.py --apply        # applies the change, one transaction
    python backfill_employer_size_band.py --log out.json # (either mode) also write the old->new table as JSON

Why this exists (changes/2026-09-25-employer-size-standard-bands.md, Step 5): before 2026-09-25 the
column held one of the retired platform labels (Startup / Small/Growth / Medium / Large / Medium/Small).
It now holds an ONS band code ('1-9', '10-49', '50-249', '250-2499', '2500+'), 'ambiguous', or NULL,
derived from a cited headcount range. New postings get the new value at ingestion
(raw_postings.insert_new_postings -> size_band_for); this brings the ALREADY-STORED rows in line so no
stale label is left behind.

A deliberate, narrow exception to db.py's "no backfill" note for the derived employer columns, approved
by the PM on 2026-09-25 — raw_postings' immutability exists to protect `raw_response` (the only chance
to capture what a company published), and this touches only a derived metadata snapshot, exactly like
raw_postings.py's existing UPDATE of ingestion_run_id. It updates NOTHING else.

Behaviour:
- One row-count-checked UPDATE per company, only where the stored value differs (IS DISTINCT FROM), so
  it is idempotent — safe to re-run, and safe to re-run AFTER deploying the new code (an older deployed
  ingest may have inserted rows with an old label in the meantime).
- A company present in raw_postings but in NEITHER COMPANY_HEADCOUNT nor UNKNOWN_HEADCOUNT (e.g. a
  company no longer tracked) is reported and LEFT UNTOUCHED — this script never invents a value.
- The derived band is the SNAPSHOT; the source of truth stays employer_headcount.COMPANY_HEADCOUNT.
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from db import get_connection  # noqa: E402  (needs DATABASE_URL, loaded above)
from employer_headcount import COMPANY_HEADCOUNT, UNKNOWN_HEADCOUNT, size_band_for  # noqa: E402


def plan(rows: list[tuple[str | None, str | None, int]]) -> tuple[list[dict], list[dict]]:
    """
    rows = (company, stored_band, row_count) grouped from raw_postings.
    Returns (changes, untouched): what would be updated, and companies deliberately left alone.
    Pure — no database access — so it can be tested.
    """
    changes: list[dict] = []
    untouched: list[dict] = []
    for company, stored, n in rows:
        if company is None:
            untouched.append({"company": None, "stored": stored, "rows": n, "reason": "no company on the row"})
            continue
        if company not in COMPANY_HEADCOUNT and company not in UNKNOWN_HEADCOUNT:
            untouched.append({"company": company, "stored": stored, "rows": n, "reason": "not in the headcount lookup — left untouched, never guessed"})
            continue
        new = size_band_for(company)
        if stored != new:
            changes.append({"company": company, "old": stored, "new": new, "rows": n})
    return changes, untouched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="actually write the change (default is a dry run)")
    ap.add_argument("--log", help="also write the old->new table to this JSON file")
    args = ap.parse_args()

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT company, employer_size_band, count(*) FROM raw_postings GROUP BY company, employer_size_band"
        ).fetchall()
        changes, untouched = plan([(c, b, int(n)) for c, b, n in rows])

        total = sum(c["rows"] for c in changes)
        print(f"{'APPLY' if args.apply else 'DRY RUN'} — {len(changes)} (company, old value) groups, {total} rows would change")
        for c in sorted(changes, key=lambda x: (x["company"], str(x["old"]))):
            print(f"  {c['company']:<20} {str(c['old']):<14} -> {str(c['new']):<10} {c['rows']:>6} rows")
        for u in untouched:
            print(f"  UNTOUCHED {u['company']!s:<14} stored={u['stored']!s:<14} {u['rows']:>6} rows — {u['reason']}")

        if args.log:
            with open(args.log, "w", encoding="utf-8") as fh:
                json.dump({"applied": args.apply, "changes": changes, "untouched": untouched}, fh, indent=2)
            print(f"log written to {args.log}")

        if not args.apply:
            print("\nDry run only — nothing written. Re-run with --apply to write.")
            conn.rollback()
            return 0

        updated = 0
        with conn.cursor() as cur:
            for company in sorted({c["company"] for c in changes}):
                cur.execute(
                    "UPDATE raw_postings SET employer_size_band = %s "
                    "WHERE company = %s AND employer_size_band IS DISTINCT FROM %s",
                    (size_band_for(company), company, size_band_for(company)),
                )
                updated += cur.rowcount
        if updated != total:
            conn.rollback()
            print(f"\nABORTED: planned {total} rows but updated {updated}; rolled back, nothing written.", file=sys.stderr)
            return 1
        conn.commit()
        print(f"\nApplied: {updated} rows updated across {len({c['company'] for c in changes})} companies.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

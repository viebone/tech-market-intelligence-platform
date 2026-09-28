"""
One-off backfill: re-derive raw_postings.country via the fixed normalize_country().

    python backfill_country_normalization.py                # DRY RUN (default): prints what would change, writes nothing
    python backfill_country_normalization.py --apply        # applies the change, one transaction
    python backfill_country_normalization.py --log out.json # (either mode) also write the old->new table as JSON

Why this exists (changes/2026-09-28-uk-gb-country-normalization-bug.md): before this fix,
normalize_country()'s "already 2 letters, assume already-ISO" shortcut ran before the
COUNTRY_NAME_TO_ISO2 dict lookup, so a raw "UK" (Ashby's addressCountry, or the last segment of
Greenhouse's "City, UK" office string) was stored as "UK" instead of the real ISO 3166-1 alpha-2
code "GB" — the dict's own "uk": "GB" entry was unreachable for exactly the input it exists to
catch. New postings get the corrected value at ingestion (sources/base.py's normalize_country,
called from ashby.py/greenhouse.py/workable.py); this brings the ALREADY-STORED rows in line so
no stale "UK" value is left behind.

A deliberate, narrow exception to db.py's "no backfill" note for the derived location columns,
following the exact precedent already established for employer_size_band
(backfill_employer_size_band.py, changes/2026-09-25-employer-size-standard-bands.md) —
raw_postings' immutability exists to protect raw_response (the only chance to capture what a
company published), and this touches only a derived metadata snapshot. It updates NOTHING else.

Behaviour:
- Generic, not hardcoded to "UK" -> "GB": re-runs normalize_country() on every distinct
  ALREADY-STORED country value and updates only where the recomputed value actually differs — so
  it automatically catches any other value this fix's reordering happens to correct, not just the
  one confirmed today.
- One row-count-checked UPDATE per distinct old value, only where the stored value differs, so it
  is idempotent — safe to re-run, and safe to re-run after deploying the new code (an older
  deployed ingest may have inserted rows with the old, wrong value in the meantime).
- A NULL country is left untouched (normalize_country(None) is None — nothing to correct).
"""

from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from db import get_connection  # noqa: E402  (needs DATABASE_URL, loaded above)
from sources.base import normalize_country  # noqa: E402


def plan(rows: list[tuple[str | None, int]]) -> list[dict]:
    """
    rows = (stored_country, row_count) grouped from raw_postings.
    Returns what would be updated. Pure — no database access — so it can be tested.
    """
    changes: list[dict] = []
    for stored, n in rows:
        if stored is None:
            continue
        new = normalize_country(stored)
        if new != stored:
            changes.append({"old": stored, "new": new, "rows": n})
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", action="store_true", help="actually write the change (default is a dry run)")
    ap.add_argument("--log", help="also write the old->new table to this JSON file")
    args = ap.parse_args()

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT country, count(*) FROM raw_postings GROUP BY country"
        ).fetchall()
        changes = plan([(c, int(n)) for c, n in rows])

        total = sum(c["rows"] for c in changes)
        print(f"{'APPLY' if args.apply else 'DRY RUN'} — {len(changes)} old value(s), {total} rows would change")
        for c in sorted(changes, key=lambda x: x["old"]):
            print(f"  {c['old']:<10} -> {str(c['new']):<10} {c['rows']:>6} rows")

        if args.log:
            with open(args.log, "w", encoding="utf-8") as fh:
                json.dump({"applied": args.apply, "changes": changes}, fh, indent=2)
            print(f"log written to {args.log}")

        if not args.apply:
            print("\nDry run only — nothing written. Re-run with --apply to write.")
            conn.rollback()
            return 0

        updated = 0
        with conn.cursor() as cur:
            for c in changes:
                cur.execute(
                    "UPDATE raw_postings SET country = %s WHERE country = %s",
                    (c["new"], c["old"]),
                )
                updated += cur.rowcount
        if updated != total:
            conn.rollback()
            print(f"\nABORTED: planned {total} rows but updated {updated}; rolled back, nothing written.", file=sys.stderr)
            return 1
        conn.commit()
        print(f"\nApplied: {updated} rows updated across {len(changes)} old value(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

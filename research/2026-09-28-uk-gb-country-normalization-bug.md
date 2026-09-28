source: bug
date: 2026-09-28

Surfaced by the new Data Coverage & Quality admin view
(`changes/2026-09-28-data-insight-coverage-quality-admin-view.md`), whose By Country list showed
`GB` and `UK` as two separate rows (801 and 176 postings respectively, per that change's own
Decision Log) instead of one. The operator asked to fix this as a follow-up
(this conversation, "continue" → "Fix the GB/UK country bug").

Root cause confirmed empirically against the live production database (not guessed):

`sources/base.py`'s `normalize_country()`:
```python
def normalize_country(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = raw.strip()
    if len(cleaned) == 2:
        return cleaned.upper()
    return COUNTRY_NAME_TO_ISO2.get(cleaned.lower())
```
checks "is this already 2 letters, assume it's a valid ISO-2 code" **before** checking
`COUNTRY_NAME_TO_ISO2`. `COUNTRY_NAME_TO_ISO2` already has `"uk": "GB"` — but that entry is
unreachable dead code for any 2-letter raw input, because the length check fires first and
returns the raw value uppercased instead.

Confirmed against two independent real sources, both of which do call `normalize_country()`:
- **Ashby** (`motorway`, 63 postings): raw `address.postalAddress.addressCountry` is literally
  `"UK"` (not `"United Kingdom"`) — 2 letters, hits the early-return branch, stored as `"UK"`.
- **Greenhouse** (`ripple`, 113 postings): raw office string is `"London, UK"` —
  `_extract_location()` splits on comma and passes the last segment (`"UK"`) to
  `normalize_country()` — same early-return bug.

Both should have normalized to `"GB"` — the correct ISO 3166-1 alpha-2 code for the United
Kingdom (`"UK"` is a common colloquial abbreviation, not the real ISO code).

**Lever checked and ruled out as a contributor**: `lever.py` bypasses `normalize_country()`
entirely (`country=(p.get("country") or "").upper() or None` — direct passthrough, per
`backend/specs/market-health/api.md`'s own documented claim that Lever's raw `country` field is
"already a clean ISO code"). All 123 real Lever postings in production today are tagged `"GB"`,
never `"UK"` — Lever's raw API values are, in practice, already correct. This is a separate
inconsistency (one adapter skips the shared normalization path the other four use) worth noting
but not itself producing any wrong value today — out of scope for this fix, which targets the one
function with a confirmed, live, wrong output.

Total affected rows as of this investigation: 176 (63 `ashby` + 113 `greenhouse`), all real,
already-ingested postings whose `country` should read `"GB"`.

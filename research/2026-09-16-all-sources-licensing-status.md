source: stakeholder-request
date: 2026-09-16

> "is it live now? all good now. we should list all the sources, and put pending if not
> confirmed or not licensed if cannot be used. as off now all data should be pending if not
> confirmed. we don't have any rejected just yet"

## Reading of the ask

Two distinct requests:

1. **A single, computed three-state status per source** — "Pending" (not yet confirmed),
   "Not licensed" (confirmed, but cannot currently be used), or implicitly a third "OK" state —
   replacing two separate booleans (`confirmed`, `permits_commercial_use`) a reader had to
   combine themselves.
2. **"List all the sources"** — surfaced a real gap: the admin licensing view and the code
   registry it read from (`scraping/licences.py`) only covered the one *scraped* source
   (IT Jobs Watch). The four employment-event API sources (SEC EDGAR, UK Companies House,
   Eurofound ERM, US WARN via WARN Firehose) had real, already-researched licence findings
   (`research/2026-09-16-existing-source-licensing-audit.md`) sitting only in `LICENSING.md`'s
   markdown table — never wired into actual code or the admin view.

## What "we don't have any rejected just yet" confirms

This is the validating fact behind the status-computation design: "not licensed" must only
trigger when a source is *both* confirmed *and* currently blocked from use (i.e.
`TMIP_COMMERCIAL_MODE` is on and the licence doesn't clear it) — never merely "unconfirmed."
With the commercial-use gate off today, and IT Jobs Watch (the one confirmed-but-NC source)
therefore currently usable, the honest state really is: 3 Licensed, 2 Pending, 0 Not licensed.
Confirmed against the real registry after building it — see `changes/2026-09-16-admin-licensing-visibility.md`'s
decision log for the full implementation record.

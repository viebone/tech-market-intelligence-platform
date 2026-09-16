source: stakeholder-request
date: 2026-09-16

Related: `research/2026-09-16-commercial-mode-kill-switch.md`, `research/2026-09-16-existing-source-licensing-audit.md`
— this request follows directly from that work, asking for it to be visible in the admin
dashboard rather than only in code/markdown docs.

> "it could be good to open an area in the admin to check licensed vs unlicensed sources, so we
> can see there the license and maybe we can include there the license to demonstrate and
> specify under which terms i can use the data"

## Reading of the ask

A new, read-only view in the existing operator-only admin dashboard (`admin_main.py`, the same
surface as Postings / Ingestion Runs / Employment Events) listing every registered data source's
licence status — variant, confirmed or not, commercial-use permitted or not, the exact
attribution text, and a link to the licence itself — so the operator can check this without
opening `LICENSING.md` or reading code, and can point to the actual licence terms under which
this platform is using each source's data.

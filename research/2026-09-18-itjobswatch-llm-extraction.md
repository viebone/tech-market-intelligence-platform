source: user-feedback
date: 2026-09-18

> "shouldn't we get it raw and then pass it to the llm maybe in batch to safe money? [...]
> I lean towards using llm batch which will safe money and also keep the data accurate.
> Please, before proceed, tell me exaclty which data are we storing raw, which data are we
> going to ask the llm to extract, how that data will be stored, how that data will be used
> and how we are going to make so that we don't go on every ingestion going through the same
> data once and again."

## What prompted this

The real IT Jobs Watch ingestion ran for the first time on 2026-09-16 (real requests, robots.txt
respected, 3 pages fetched — see `research/2026-09-16-itjobswatch-real-page-verification.md`).
Inspecting the actual stored rows against the actual cached HTML (not the earlier WebFetch
paraphrase) found the regex-based parser (`scraping/itjobswatch.py`) extracting real but wrong
values: table row word order was backwards (assumed "{num} {label}", real structure is
"{label} {num-current} {num-2025} {num-2024}", a 3-column historical table), the currency symbol
isn't decoding as `£`, and the skill list format is reversed ("{rank} {job_count} (pct%) {name}",
not "{name} (pct%)"). Concretely: `rank`/`vacancy_count` picked up numbers from adjacent table
cells, all 5 salary percentiles landed `NULL`, and every `skill_name` is garbled (e.g.
`"Roadmaps 2 162"` instead of `"Roadmaps"`).

## Decision

Replace regex extraction with LLM-based extraction (Gemini, via the existing `llm/` provider
abstraction, `gemini-2.5-flash` — same model `classification.py` already uses for exactly this
kind of "extract structured facts from messy real text" job). Full design agreed with the user,
recorded in `changes/2026-09-18-itjobswatch-llm-extraction.md`.

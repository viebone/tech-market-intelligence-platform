"""
PostgreSQL connection helper and schema for the market-health ingestion pipeline.

First real database usage in this product — everything else still runs on
in-memory mock data (see mock_data.py). See backend/specs/market-health/api.md
for the raw_postings / classifications data model this schema implements.

A short-lived connection per call, not a pool: this feature's query volume
(one small aggregation query per API request, a handful of ingestion batches
a day) doesn't need pooling, and psycopg_pool's background connection worker
was hanging in local Windows dev even though a direct psycopg.connect()
succeeded instantly.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg


@contextmanager
def get_connection():
    database_url = os.environ["DATABASE_URL"]
    # connect_timeout guards against a "localhost" DSN stalling on IPv6
    # resolution before falling back to IPv4 — seen hanging indefinitely in
    # local Windows dev with no timeout set. Prefer 127.0.0.1 in DATABASE_URL.
    with psycopg.connect(database_url, connect_timeout=10) as conn:
        yield conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_postings (
    id                 TEXT PRIMARY KEY,
    role_family_query  TEXT,
    title              TEXT NOT NULL,
    raw_response       JSONB NOT NULL,
    fetched_at         TIMESTAMPTZ NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Multi-source ingestion migration (2026-08-03): raw_postings already has
-- live production rows from Adzuna, so this evolves the existing table
-- rather than assuming a fresh CREATE. See backend/specs/market-health/
-- api.md — Data Models — RawPosting (migration note) and Tech Decisions —
-- Schema migration is ALTER TABLE, not just CREATE TABLE IF NOT EXISTS.
-- Idempotent — safe to run on every startup, same as the CREATE statements.
ALTER TABLE raw_postings ALTER COLUMN role_family_query DROP NOT NULL;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS source TEXT;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS source_ref TEXT;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS company TEXT;
UPDATE raw_postings SET source = 'adzuna', source_ref = id WHERE source IS NULL;

CREATE TABLE IF NOT EXISTS classifications (
    id                 SERIAL PRIMARY KEY,
    posting_id         TEXT NOT NULL REFERENCES raw_postings(id),
    role_category      TEXT NOT NULL,
    sub_specialization TEXT,
    seniority          TEXT,
    track              TEXT,
    taxonomy_version   TEXT NOT NULL,
    model              TEXT NOT NULL,
    classified_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (posting_id)
);

-- Compensation Signal / enriched Demand Signal migration (2026-08-04):
-- raw_postings already has live production rows, so this evolves the
-- existing table rather than assuming a fresh CREATE. See
-- backend/specs/market-health/api.md — Data Models — RawPosting (migration
-- note 2026-08-04). No backfill against existing rows — these are derived
-- at ingestion time going forward; existing rows simply keep them NULL.
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS country TEXT;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS salary_min INTEGER;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS salary_max INTEGER;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS salary_currency TEXT;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS salary_confidence TEXT;
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS salary_extraction_method TEXT;

-- Skills/industry migration (2026-08-09): raw_postings already has live
-- production rows, same evolve-not-recreate pattern. See
-- backend/specs/market-health/api.md — Data Models — RawPosting (migration
-- note 2026-08-09). No backfill — industry is populated at ingestion time
-- going forward; existing rows keep it NULL (never re-fetched, per the id
-- dedupe invariant, so there is no future moment that would fill it in).
ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS industry TEXT;

CREATE INDEX IF NOT EXISTS idx_raw_postings_fetched_at ON raw_postings (fetched_at);
CREATE INDEX IF NOT EXISTS idx_raw_postings_source ON raw_postings (source);
CREATE INDEX IF NOT EXISTS idx_raw_postings_country ON raw_postings (country);
CREATE INDEX IF NOT EXISTS idx_classifications_role_category ON classifications (role_category);

-- Requirements Signal tables (2026-08-09): brand new tables, not evolving an
-- existing one — plain CREATE TABLE IF NOT EXISTS is sufficient, no ALTER
-- TABLE dance needed. See backend/specs/market-health/api.md — Data Models —
-- PostingRequirements/PostingSkill/PostingLanguage.
CREATE TABLE IF NOT EXISTS posting_requirements (
    posting_id             TEXT PRIMARY KEY REFERENCES raw_postings(id),
    education_level        TEXT NOT NULL DEFAULT 'not_mentioned',
    responsibilities_summary TEXT,
    other_requirements     TEXT,
    model                  TEXT NOT NULL,
    extracted_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS posting_skills (
    id                 SERIAL PRIMARY KEY,
    posting_id         TEXT NOT NULL REFERENCES raw_postings(id),
    skill              TEXT NOT NULL,
    requirement_level  TEXT NOT NULL,
    UNIQUE (posting_id, skill)
);

CREATE TABLE IF NOT EXISTS posting_languages (
    id                 SERIAL PRIMARY KEY,
    posting_id         TEXT NOT NULL REFERENCES raw_postings(id),
    language           TEXT NOT NULL,
    requirement_level  TEXT NOT NULL,
    UNIQUE (posting_id, language)
);

-- idx_posting_skills_skill's column reference is fixed up post-rename, below
-- (2026-08-11 migration) — CREATE INDEX IF NOT EXISTS still validates the
-- column list even when the index name already exists, so a static
-- reference to the pre-rename "skill" column here would fail on every
-- startup after the first (confirmed the hard way against real production).
CREATE INDEX IF NOT EXISTS idx_posting_skills_posting_id ON posting_skills (posting_id);
CREATE INDEX IF NOT EXISTS idx_posting_languages_posting_id ON posting_languages (posting_id);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id                 SERIAL PRIMARY KEY,
    started_at         TIMESTAMPTZ NOT NULL,
    completed_at       TIMESTAMPTZ,
    status             TEXT NOT NULL,
    terms_processed    JSONB NOT NULL DEFAULT '[]',
    total_fetched      INTEGER NOT NULL DEFAULT 0,
    total_inserted     INTEGER NOT NULL DEFAULT 0,
    total_classified   INTEGER NOT NULL DEFAULT 0,
    cache_hits         INTEGER NOT NULL DEFAULT 0,
    llm_classified     INTEGER NOT NULL DEFAULT 0,
    other_count        INTEGER NOT NULL DEFAULT 0,
    other_rate         REAL NOT NULL DEFAULT 0.0,
    anomalies          JSONB NOT NULL DEFAULT '[]',
    error_message      TEXT
);

-- Classification LLM-call-reduction migration (2026-08-04): ingestion_runs
-- already has live production rows, so this evolves the existing table
-- rather than assuming a fresh CREATE. See backend/specs/market-health/
-- api.md — Data Models — IngestionRun. Idempotent — safe to run on every
-- startup, same pattern as raw_postings' 2026-08-03 migration above.
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS heuristic_filtered INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS budget_reached BOOLEAN NOT NULL DEFAULT false;

-- Cross-run daily budget migration (2026-08-05): ingestion_runs already has
-- live production rows, so this evolves the existing table rather than
-- assuming a fresh CREATE. See backend/specs/market-health/api.md — Data
-- Models — IngestionRun. Idempotent — safe to run on every startup.
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS llm_requests_used INTEGER NOT NULL DEFAULT 0;

-- Requirements extraction migration (2026-08-09): same idempotent pattern,
-- kept separate from the classification fields above (Business Logic —
-- Requirements extraction — own dedicated budget, not a shared pool).
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS requirements_extracted INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS requirements_requests_used INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS requirements_budget_reached BOOLEAN NOT NULL DEFAULT false;

-- Classification taxonomy redesign migration (2026-08-11): the one deliberate
-- non-additive migration in this file — see backend/specs/market-health/
-- api.md — Data Models — Classification (migration note) for the full
-- reasoning. RENAME COLUMN has no native IF EXISTS-style guard in Postgres,
-- so the renames are wrapped in DO blocks that check information_schema
-- first, keeping this idempotent across repeated startups the same as every
-- other statement here.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'classifications' AND column_name = 'sub_specialization'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'classifications' AND column_name = 'specialization'
    ) THEN
        ALTER TABLE classifications RENAME COLUMN sub_specialization TO specialization;
    END IF;
END $$;

-- seniority's stored values are actively wrong for the population this
-- revision fixes (see job-classification.md — Level), not merely
-- incomplete — dropped rather than preserved, since there is no valid
-- mapping from the old lossy values to the new ones; level is re-derived
-- from title by the reprocessing pass instead.
ALTER TABLE classifications DROP COLUMN IF EXISTS seniority;
ALTER TABLE classifications ADD COLUMN IF NOT EXISTS level TEXT;
ALTER TABLE classifications ADD COLUMN IF NOT EXISTS classification_confidence TEXT;

-- Requirements Signal fields (2026-08-11): purely additive, same pattern as
-- every posting_requirements migration before it.
ALTER TABLE posting_requirements ADD COLUMN IF NOT EXISTS education_required TEXT;
ALTER TABLE posting_requirements ADD COLUMN IF NOT EXISTS equivalent_experience_accepted BOOLEAN;
ALTER TABLE posting_requirements ADD COLUMN IF NOT EXISTS years_experience_min INTEGER;
ALTER TABLE posting_requirements ADD COLUMN IF NOT EXISTS work_arrangement TEXT;

-- posting_skills restructure (2026-08-11): skill -> skill_group rename plus
-- a new raw_skill column, same DO-block guard pattern as classifications'
-- rename above. Existing skill_group values are preserved (still valid
-- closed-set values, just missing their raw_skill counterpart until
-- reprocessed) — this is additive-plus-rename, not the same "actively
-- wrong data" case as classifications.seniority.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'posting_skills' AND column_name = 'skill'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'posting_skills' AND column_name = 'skill_group'
    ) THEN
        ALTER TABLE posting_skills RENAME COLUMN skill TO skill_group;
    END IF;
END $$;
ALTER TABLE posting_skills ADD COLUMN IF NOT EXISTS raw_skill TEXT;

-- UNIQUE(posting_id, skill) no longer fits now that multiple raw mentions
-- can share one skill_group (e.g. "Kafka" and "Spark" both under "Data
-- engineering / big data") — replaced with UNIQUE(posting_id, raw_skill).
-- RENAME COLUMN does not rename the constraint that referenced the old
-- column name, so the old constraint is dropped explicitly by its
-- (Postgres-default) auto-generated name and the new one added, each
-- guarded so this stays idempotent across repeated startups.
ALTER TABLE posting_skills DROP CONSTRAINT IF EXISTS posting_skills_posting_id_skill_key;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'posting_skills_posting_id_raw_skill_key'
    ) THEN
        ALTER TABLE posting_skills
            ADD CONSTRAINT posting_skills_posting_id_raw_skill_key UNIQUE (posting_id, raw_skill);
    END IF;
END $$;

-- New index for the raw_skill breakdown query_requirements_data now needs
-- (Business Logic — query tools).
CREATE INDEX IF NOT EXISTS idx_posting_skills_raw_skill ON posting_skills (raw_skill);

-- Corrected, post-rename column reference for the index originally created
-- (pre-2026-08-11) as `idx_posting_skills_skill ON posting_skills (skill)`.
-- On an already-migrated database this index already exists under this name
-- and IF NOT EXISTS skips it (now safely, since skill_group genuinely
-- exists). On a fresh database this is what actually creates it, since the
-- original early CREATE INDEX statement above was removed for the reason
-- explained there.
CREATE INDEX IF NOT EXISTS idx_posting_skills_skill ON posting_skills (skill_group);
"""


def init_schema() -> None:
    """Create raw_postings / classifications if they don't exist yet. Idempotent."""
    with get_connection() as conn:
        conn.execute(SCHEMA)

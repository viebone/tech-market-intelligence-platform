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

CREATE INDEX IF NOT EXISTS idx_raw_postings_fetched_at ON raw_postings (fetched_at);
CREATE INDEX IF NOT EXISTS idx_raw_postings_source ON raw_postings (source);
CREATE INDEX IF NOT EXISTS idx_classifications_role_category ON classifications (role_category);

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
"""


def init_schema() -> None:
    """Create raw_postings / classifications if they don't exist yet. Idempotent."""
    with get_connection() as conn:
        conn.execute(SCHEMA)

"""
Registry of every live job-data source adapter, mirroring llm/providers.py's
factory-module pattern. ingest.py loops over ALL_SOURCE_ADAPTERS — adding a
fourth source means adding one adapter here, no change to orchestration,
raw_postings.py, or classification.py.
"""

from sources.ashby import AshbyAdapter
from sources.base import FetchedPosting, SourceAdapter, SourceFetchError
from sources.greenhouse import GreenhouseAdapter
from sources.lever import LeverAdapter

ALL_SOURCE_ADAPTERS: list[SourceAdapter] = [
    GreenhouseAdapter(),
    LeverAdapter(),
    AshbyAdapter(),
]

__all__ = ["ALL_SOURCE_ADAPTERS", "FetchedPosting", "SourceAdapter", "SourceFetchError"]

"""
Full-coverage traceability check: every adapter registered anywhere in this
codebase — job-posting sources, employment-event sources, scraped sources —
must have a corresponding entry in source_licences.SOURCE_LICENCES. This is
what makes "every bit of data can be tracked against a licence"
(research/2026-09-16-all-sources-licensing-status.md) an enforced fact
rather than a hope someone remembers to keep true by hand: add a new
adapter anywhere without registering its licence, and this test fails.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv_linux/bin/python ../tests/test_source_licences.py
    (or, on Windows, ./venv/Scripts/python ../tests/test_source_licences.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sources import ALL_SOURCE_ADAPTERS  # noqa: E402
from employment_events import ALL_EMPLOYMENT_EVENT_ADAPTERS  # noqa: E402
from scraping import ALL_SCRAPED_SOURCE_ADAPTERS  # noqa: E402
from trusted_stats import ALL_STATISTICS_ADAPTERS  # noqa: E402
from source_licences import SOURCE_LICENCES, LicenceNotRegisteredError, get_licence  # noqa: E402


def _all_registered_adapter_names() -> set[str]:
    """Every source name this codebase actually fetches data from, across
    all three adapter categories — job postings, employment events, and
    scraped sources. Deliberately reads the real registries (ALL_SOURCE_
    ADAPTERS etc.), not a hardcoded list, so this test fails the moment a
    new adapter is added anywhere without this file being touched."""
    names: set[str] = set()
    names.update(adapter.name for adapter in ALL_SOURCE_ADAPTERS)
    names.update(adapter.name for adapter in ALL_EMPLOYMENT_EVENT_ADAPTERS)
    names.update(adapter_cls.name for adapter_cls in ALL_SCRAPED_SOURCE_ADAPTERS)  # classes, not instances
    names.update(adapter.source for adapter in ALL_STATISTICS_ADAPTERS)  # trusted external statistics (added 2026-09-25)
    return names


def test_every_registered_adapter_has_a_licence_entry():
    missing = _all_registered_adapter_names() - set(SOURCE_LICENCES)
    assert not missing, (
        f"These adapters fetch real data but have no source_licences.py entry: {missing}. "
        f"Register a SourceLicence for each before this can pass — see the module docstring."
    )


def test_every_licence_entry_corresponds_to_a_real_adapter():
    # The reverse check — catches a stale registry entry for a source that
    # was retired/renamed, which would otherwise sit there forever looking
    # like real coverage for something that no longer fetches anything.
    real_names = _all_registered_adapter_names()
    stale = set(SOURCE_LICENCES) - real_names
    assert not stale, (
        f"source_licences.py has entries for sources with no matching adapter anywhere: "
        f"{stale}. Either the adapter was removed (retire this entry) or the name drifted "
        f"out of sync (fix the key)."
    )


def test_get_licence_resolves_for_every_real_adapter():
    # Belt-and-braces: not just "the key exists" but "get_licence() actually
    # returns something usable" for every real source.
    for name in _all_registered_adapter_names():
        licence = get_licence(name)
        assert licence.source == name
        assert licence.licence  # non-empty — never a blank placeholder
        assert licence.attribution_text
        assert licence.data_summary, f"{name} has no data_summary — what do we actually take from it?"


def test_unregistered_source_still_raises():
    raised = False
    try:
        get_licence("some-adapter-nobody-wrote-yet")
    except LicenceNotRegisteredError:
        raised = True
    assert raised


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

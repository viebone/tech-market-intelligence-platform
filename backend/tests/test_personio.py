"""
Personio XML-feed adapter (changes/2026-09-26-personio-adapter.md).

Offline — the feed shapes below are trimmed copies of real responses read on
2026-09-26 (Stark, Capmo, Personio's own board, and the 307 an unknown slug gets).

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_personio.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx  # noqa: E402

import requirements  # noqa: E402
import sources.personio as personio  # noqa: E402
from sources import ALL_SOURCE_ADAPTERS, SourceFetchError  # noqa: E402

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>

<workzag-jobs>

<position>
    <id>1834171</id>
    <subcompany>Personio SE &amp; Co. KG</subcompany>
    <office>Munich</office>
    <additionalOffices>
        <office>Berlin</office>
        <office>Dublin</office>
    </additionalOffices>
    <department>Product and Tech</department>
    <recruitingCategory>Engineering</recruitingCategory>
    <name>Staff Software Engineer, Data Platform</name>
    <jobDescriptions>
        <jobDescription>
            <name>The Role</name>
            <value>
                <![CDATA[<strong>Hybrid</strong> in Munich &amp; Dublin. Python and Kafka.]]>
            </value>
        </jobDescription>
        <jobDescription>
            <name>What you&#039;ll do</name>
            <value>
                <![CDATA[<ul><li>Own the platform</li></ul>]]>
            </value>
        </jobDescription>
    </jobDescriptions>
    <employmentType>permanent</employmentType>
    <seniority>experienced</seniority>
    <schedule>full-time</schedule>
    <keywords>Kafka,Python</keywords>
    <createdAt>2026-09-01T10:00:00+00:00</createdAt>
</position>

<position>
    <id>2777374</id>
    <office>Madrid</office>
    <department>Marketing</department>
    <name>SEO Marketing Manager</name>
    <jobDescriptions></jobDescriptions>
    <employmentType>permanent</employmentType>
    <createdAt>2017-05-23T07:50:24+00:00</createdAt>
</position>

<position>
    <id>1834171</id>
    <office>Duplicate of the first id</office>
    <name>Staff Software Engineer, Data Platform (dup)</name>
</position>

</workzag-jobs>
"""

EMPTY_FEED = b'<?xml version="1.0" encoding="UTF-8"?>\n\n<workzag-jobs>\n\n\n</workzag-jobs>\n'


def _raises(fn) -> bool:
    try:
        fn()
    except SourceFetchError:
        return True
    return False


_REAL_CLIENT = httpx.Client


def _adapter_over(handler) -> personio.PersonioAdapter:
    """A real PersonioAdapter whose HTTP client is routed to `handler` (no network)."""

    def factory(*args, **kwargs):
        return _REAL_CLIENT(transport=httpx.MockTransport(handler), **kwargs)

    personio.httpx.Client = factory
    return personio.PersonioAdapter()


def test_registered_and_named():
    assert "personio" in {a.name for a in ALL_SOURCE_ADAPTERS}
    assert personio.PersonioAdapter.name == "personio"
    assert personio.COMPANIES and len(set(personio.COMPANIES)) == len(personio.COMPANIES)


def test_one_posting_per_distinct_position_id():
    postings = personio.parse_feed("personio", FEED)
    assert [p.source_ref for p in postings] == ["personio/1834171", "personio/2777374"]  # the dup id is dropped
    first = postings[0]
    assert first.company == "personio"
    assert first.title == "Staff Software Engineer, Data Platform"  # the position's own <name>, not a jobDescription's
    assert first.city == "Munich"
    assert first.country is None                                     # never inferred from a city
    assert first.salary_min is None and first.salary_max is None


def test_raw_response_is_the_feed_shape_verbatim():
    raw = personio.parse_feed("personio", FEED)[0].raw_response
    assert raw["id"] == "1834171"
    assert raw["subcompany"] == "Personio SE & Co. KG"
    assert raw["additionalOffices"] == ["Berlin", "Dublin"]
    assert raw["keywords"] == "Kafka,Python"
    assert raw["createdAt"] == "2026-09-01T10:00:00+00:00"           # kept, even when stale, never filtered
    assert [d["name"] for d in raw["jobDescriptions"]] == ["The Role", "What you'll do"]
    assert "<strong>Hybrid</strong>" in raw["jobDescriptions"][0]["value"]


def test_empty_descriptions_and_empty_board_are_ordinary():
    stale = personio.parse_feed("personio", FEED)[1]
    assert stale.raw_response["jobDescriptions"] == []
    assert personio.parse_feed("moss", EMPTY_FEED) == []


def test_malformed_or_unsafe_xml_fails_that_company_only():
    assert _raises(lambda: personio.parse_feed("x", b"<workzag-jobs><position>"))            # truncated
    assert _raises(lambda: personio.parse_feed("x", b"<html><body>Career Site</body></html>"))  # wrong root
    bomb = b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY a "aaaa">]><workzag-jobs>&a;</workzag-jobs>'
    assert _raises(lambda: personio.parse_feed("x", bomb))                                   # DTD/entity refused
    assert _raises(lambda: personio.parse_feed("x", b"<a/>" + b" " * (personio.MAX_FEED_BYTES + 1)))  # oversize


def test_unknown_slug_redirect_is_a_fetch_error_not_an_empty_board():
    # Real behaviour, 2026-09-26: a board that doesn't exist answers 307 -> https://personio.com.
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(307, headers={"Location": "https://personio.com"})

    adapter = _adapter_over(handler)
    try:
        assert _raises(lambda: adapter.fetch_company("no-such-employer"))
    finally:
        personio.httpx.Client = _REAL_CLIENT
    assert len(seen) == 1                                   # not retried, and the redirect was not followed
    assert seen[0].url.host == "no-such-employer.jobs.personio.de"


def test_fetch_company_hits_the_feed_url_with_an_identifying_user_agent():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=FEED, headers={"Content-Type": "text/xml"})

    adapter = _adapter_over(handler)
    try:
        postings = adapter.fetch_company("stark")
    finally:
        personio.httpx.Client = _REAL_CLIENT
    assert len(postings) == 2 and postings[0].source_ref == "stark/1834171"
    assert str(seen[0].url) == "https://stark.jobs.personio.de/xml"
    assert seen[0].headers["User-Agent"] == personio.USER_AGENT


def test_requirements_extraction_reads_personio_descriptions():
    raw = personio.parse_feed("personio", FEED)[0].raw_response
    text = requirements._extract_description("personio", raw)
    assert "Hybrid" in text and "Python and Kafka" in text and "Own the platform" in text
    assert "<" not in text                                             # tags stripped like every other source
    assert requirements._extract_description("personio", {"jobDescriptions": []}) == ""


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print(f"PASS {name}")
    print(f"{len(tests)}/{len(tests)} passed")

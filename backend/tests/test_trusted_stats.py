"""
Trusted external statistics — backend/specs/trusted-statistics/api.md.

Runs entirely offline (no database, no network): the parser is tested against the REAL ONS files
(tests/fixtures/, published 2026-09-15) with expected values taken from ONS's own figures; the orchestrator
against an in-memory storage fake and a fake fetcher that serves those real files.

What this enforces:
- parse(): every series, period, flag and footnote rule from the spec, on real data;
- validate(): each check REJECTS a release when its condition is violated (sum-of-parts, contiguity,
  plausibility, missing series, cross-file agreement);
- the vintage rule (unchanged skipped, changed stored, provisional confirmed stored, repeated flag not noise);
- the orchestrator: the cadence gate makes NO request, a released-already release is never downloaded, a
  rejected release stores nothing, an identical file is never re-parsed, an unregistered publisher/licence is
  a hard error, one failure never raises out;
- the polite fetcher: refuses without STATISTICS_CONTACT, identifies itself, honours robots.txt (a 404 or an
  HTML "page not found" states no restrictions), retries only transient failures;
- registry completeness (adapter <-> TRUSTED_PUBLISHERS <-> SOURCE_LICENCES) and crosswalk completeness.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv/Scripts/python ../tests/test_trusted_stats.py
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import industries  # noqa: E402
from source_licences import SOURCE_LICENCES, LicenceNotRegisteredError  # noqa: E402
from statistics_storage import decide_vintage  # noqa: E402
from trusted_stats import (  # noqa: E402
    ALL_STATISTICS_ADAPTERS, TRUSTED_PUBLISHERS, FetchedStatistic, LayoutError, OnsVacancySurveyAdapter, ParsedRelease,
    PoliteFetcher, ReleaseRef, StatisticsConfigError, StatisticsFetchError, ingest_adapter, is_due_from_last_run,
)
from trusted_stats.crosswalks import OUR_INDUSTRY_TO_SIC_SECTION, sic_section_for  # noqa: E402
from trusted_stats.ons_vacancy import parse_period, status_from_flag  # noqa: E402
from trusted_stats.registry import TrustedPublisher  # noqa: E402
from trusted_stats.sic import SIC_2007_SECTIONS, VACANCY_SURVEY_SECTIONS  # noqa: E402
from trusted_stats.xlsx_reader import XlsxError, read_workbook  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
VACS02_BYTES = (FIX / "ons_vacs02_sep2026.xlsx").read_bytes()
VACS03_BYTES = (FIX / "ons_vacs03_sep2026.xlsx").read_bytes()
REF02 = ReleaseRef("VACS02", date(2026, 9, 15), "u", "u/vacs02sep2026.xlsx", "vacs02sep2026.xlsx")
REF03 = ReleaseRef("VACS03", date(2026, 9, 15), "u", "u/vacs03sep2026.xlsx", "vacs03sep2026.xlsx")
ADAPTER = OnsVacancySurveyAdapter()


def _parsed(ref=REF03, data=VACS03_BYTES) -> ParsedRelease:
    return ADAPTER.parse(ref, data)


def _latest(parsed: ParsedRelease) -> dict[str, FetchedStatistic]:
    newest = max(o.period_start for o in parsed.observations)
    return {o.series_code: o for o in parsed.observations if o.period_start == newest}


# ── xlsx reader ───────────────────────────────────────────────────────────────

def test_reader_reads_the_real_workbooks():
    assert set(read_workbook(VACS03_BYTES)) == {"VACS03"}
    assert set(read_workbook(VACS02_BYTES)) == {"levels", "job openings rate"}


def test_reader_refuses_non_workbooks_and_absurd_sizes():
    for bad in (b"not a zip", b""):
        try:
            read_workbook(bad)
        except XlsxError:
            continue
        raise AssertionError("a non-workbook was accepted")
    try:
        read_workbook(b"x" * (21 * 1024 * 1024))
    except XlsxError:
        pass
    else:
        raise AssertionError("an oversized file was accepted")


# ── parse: VACS03 (size of business), against ONS's own figures ───────────────

def test_vacs03_latest_values_match_the_published_figures():
    p = _parsed()
    latest = _latest(p)
    assert {k: v.value for k, v in latest.items()} == {"AP2Y": 702.0, "ALY5": 91.0, "ALY6": 99.0, "ALY7": 103.0, "ALY8": 169.0, "ALY9": 240.0}
    assert all(o.period_label == "Jun-Aug 2026" and o.value_status == "provisional" for o in latest.values())
    assert (latest["AP2Y"].period_start, latest["AP2Y"].period_end) == (date(2026, 6, 1), date(2026, 8, 31))


def test_vacs03_history_and_series_definitions():
    p = _parsed()
    assert len({o.period_start for o in p.observations}) == 303
    assert len(p.series) == 6
    first = min(o.period_start for o in p.observations)
    assert first == date(2001, 4, 1)
    sizes = {d.series_code: d.dimensions["size_band"]["code"] for d in p.series if d.dimension_type == "size_band"}
    assert sizes == {"ALY5": "1-9", "ALY6": "10-49", "ALY7": "50-249", "ALY8": "250-2499", "ALY9": "2500+"}
    for d in p.series:
        assert d.unit == "thousand vacancies" and d.unit_scale == 1000 and d.period_type == "rolling_3_month"
        assert d.designation == "accredited_official_statistics"
        assert d.seasonal_adjustment == "seasonally_adjusted"      # from ONS's methodology; the file is silent
        assert "Great Britain" in d.coverage_note and "agriculture, forestry and fishing" in d.coverage_note
        assert d.dimensions["geography"]["code"] == "K02000001"
    assert "2 to 9" in next(d for d in p.series if d.series_code == "ALY5").definition_note


def test_period_labels_including_the_stray_space_and_year_crossing():
    assert parse_period("Jun-Aug 2026") == (date(2026, 6, 1), date(2026, 8, 31), "Jun-Aug 2026")
    assert parse_period("Nov- Jan 2002") == (date(2001, 11, 1), date(2002, 1, 31), "Nov-Jan 2002")   # the real stray space
    assert parse_period("Dec-Feb 2024")[:2] == (date(2023, 12, 1), date(2024, 2, 29))                 # leap year
    for bad in ("Change on quarter", "Jun-Aug", "Xxx-Aug 2026", ""):
        try:
            parse_period(bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad!r}")


def test_flags_map_to_statuses():
    assert [status_from_flag(f) for f in ("(p)", "(r)", "", None, "(P)", "(x)")] == ["provisional", "revised", "final", "final", "provisional", "unknown"]


# ── parse: VACS02 (industry) ──────────────────────────────────────────────────

def test_vacs02_series_values_and_labels():
    p = _parsed(REF02, VACS02_BYTES)
    assert len(p.series) == 20                                     # AP2Y + 18 sections B-S + the G-S aggregate
    latest = _latest(p)
    assert latest["AP2Y"].value == 702.0
    assert latest["JP9P"].value == 36.0                            # section J, Information and communication
    assert latest["JP9W"].value == 121.0                           # section Q, Human health and social work
    assert latest["JP9Z"].value == 615.0                           # G-S total services
    by_id = {d.series_code: d for d in p.series}
    assert by_id["JP9P"].dimensions["industry"] == {"system": "SIC2007_section", "code": "J", "label": "Information and communication"}
    assert by_id["JP9Z"].dimensions["industry"]["system"] == "SIC2007_aggregate"
    # header artefacts ("Manu-    facturing", "Construc-tion") never reach a label — labels come from sic.py
    assert "Manufacturing" in by_id["JP9I"].title and "Manu-" not in by_id["JP9I"].title
    assert not any("-  " in d.title or "Construc-" in d.title for d in p.series)
    # divisions 45/46/47 (columns W-Y) have no series ID in the file — deliberately not ingested
    assert {d.series_code for d in p.series} == {"AP2Y", "JP9Z", *[f"JP9{c}" for c in "HIJKLMNOPQRSTUVWXY"]}   # 18 sections B-S


def test_vacs02_footnote_2_marks_series_not_seasonally_adjusted():
    p = _parsed(REF02, VACS02_BYTES)
    by_id = {d.series_code: d for d in p.series}
    not_adjusted = {sid for sid, d in by_id.items() if d.seasonal_adjustment == "not_adjusted"}
    assert {"JP9R"} <= not_adjusted                                # Real estate activities — footnote 2 in the file
    assert by_id["JP9R"].definition_note.count("Not seasonally adjusted") >= 1
    assert by_id["JP9P"].seasonal_adjustment == "seasonally_adjusted"
    assert by_id["AP2Y"].seasonal_adjustment == "seasonally_adjusted"


def test_vacs02_footnote_3_is_a_coverage_note_not_an_adjustment_note():
    by_id = {d.series_code: d for d in _parsed(REF02, VACS02_BYTES).series}
    admin = by_id["JP9T"]                                          # Administrative and support service activities
    assert admin.seasonal_adjustment == "seasonally_adjusted"
    assert "employment agencies" in admin.coverage_note and "Footnote 3" in admin.coverage_note


def test_vacs02_sheet_missing_is_a_layout_error():
    try:
        ADAPTER.parse(REF03, VACS02_BYTES)                         # VACS03 expects sheet 'VACS03'; this workbook has 'levels'
    except LayoutError:
        return
    raise AssertionError("wrong workbook accepted")


# ── validate ──────────────────────────────────────────────────────────────────

def test_real_files_validate_and_agree_with_each_other():
    p02, p03 = _parsed(REF02, VACS02_BYTES), _parsed(REF03, VACS03_BYTES)
    assert ADAPTER.validate(p02) == [] and ADAPTER.validate(p03) == []
    assert ADAPTER.validate_set([p02, p03]) == []                  # AP2Y identical in both files, every shared period


def _replace(parsed: ParsedRelease, fn) -> ParsedRelease:
    return ParsedRelease(parsed.dataset_code, parsed.series, [fn(o) for o in parsed.observations if fn(o) is not None])


def _swap_values(o: FetchedStatistic) -> FetchedStatistic | None:
    # misalign two size columns at the newest period: the classic "columns shifted" failure
    if o.period_label == "Jun-Aug 2026" and o.series_code in ("ALY5", "ALY9"):
        return FetchedStatistic(o.series_code, o.period_start, o.period_end, o.period_label, 900.0, o.value_status, o.raw_cell)
    return o


def test_sum_of_parts_rejects_misaligned_columns():
    fails = ADAPTER.validate(_replace(_parsed(), _swap_values))
    assert any("sum of parts" in f for f in fails), fails


def test_contiguity_rejects_a_missing_month():
    p = _parsed()
    drop = date(2020, 5, 1)
    fails = ADAPTER.validate(_replace(p, lambda o: None if o.period_start == drop else o))
    assert any("not contiguous" in f for f in fails), fails


def test_plausibility_rejects_a_unit_slip():
    fails = ADAPTER.validate(_replace(_parsed(), lambda o: FetchedStatistic(o.series_code, o.period_start, o.period_end, o.period_label, o.value * 1000, o.value_status, o.raw_cell)))
    assert any("plausible" in f for f in fails), fails


def test_a_missing_series_is_rejected_and_a_lost_newest_period_is_rejected():
    p = _parsed()
    assert ADAPTER.validate(ParsedRelease(p.dataset_code, p.series, [o for o in p.observations if o.series_code != "ALY7"]))
    newest = max(o.period_start for o in p.observations)
    fails = ADAPTER.validate(_replace(p, lambda o: None if (o.series_code == "ALY6" and o.period_start == newest) else o))
    assert any("newest period" in f for f in fails), fails


def test_cross_file_check_rejects_disagreeing_totals():
    p02, p03 = _parsed(REF02, VACS02_BYTES), _parsed(REF03, VACS03_BYTES)
    bad = _replace(p03, lambda o: FetchedStatistic(o.series_code, o.period_start, o.period_end, o.period_label, o.value + 5 if (o.series_code == "AP2Y" and o.period_label == "Jun-Aug 2026") else o.value, o.value_status, o.raw_cell))
    assert ADAPTER.validate_set([p02, bad])


# ── the vintage rule ──────────────────────────────────────────────────────────

def test_vintage_rule():
    assert decide_vintage(None, 702.0, "provisional") == ("new", "provisional")
    assert decide_vintage((702.0, "final"), 702.0, "final") == ("unchanged", None)
    assert decide_vintage((702.0, "provisional"), 702.0, "provisional") == ("unchanged", None)
    # a provisional value that is now confirmed at the same value IS stored (as the new status)
    assert decide_vintage((702.0, "provisional"), 702.0, "final") == ("revised", "final")
    # a changed value: still-provisional stays provisional; anything else is 'revised'
    assert decide_vintage((700.0, "provisional"), 702.0, "provisional") == ("revised", "provisional")
    assert decide_vintage((700.0, "final"), 702.0, "final") == ("revised", "revised")
    assert decide_vintage((700.0, "final"), 702.0, "revised") == ("revised", "revised")
    # a repeated '(r)' flag on an UNCHANGED value never creates a row (a month of noise otherwise)
    assert decide_vintage((702.0, "revised"), 702.0, "revised") == ("unchanged", None)
    assert decide_vintage((702.0, "final"), 702.0, "revised") == ("unchanged", None)


# ── fakes for the orchestrator ────────────────────────────────────────────────

class FakeFetcher:
    """Serves the REAL files; records every request so 'no request made' is assertable."""
    def __init__(self):
        self.requests: list[str] = []

    def get_json(self, url):
        self.requests.append(url)
        code = "VACS02" if "vacs02" in url or "byindustry" in url else "VACS03"
        file = "vacs02sep2026.xlsx" if code == "VACS02" else "vacs03sep2026.xlsx"
        return {"uri": f"/x/{code.lower()}/current", "downloads": [{"file": file}],
                "versions": [{"updateDate": "2026-08-18T06:00:00.000Z"}, {"updateDate": "2026-09-15T06:00:00.000Z"}],
                "description": {"releaseDate": "2016-08-16T23:00:00.000Z"}}

    def get_bytes(self, url):
        self.requests.append(url)
        return VACS02_BYTES if "vacs02" in url else VACS03_BYTES


class FakeStorage:
    def __init__(self):
        self.releases: dict[tuple, dict] = {}
        self.hashes: set[tuple] = set()
        self.runs: list[dict] = []
        self.stored: list[dict] = []
        self.last_run: datetime | None = None
        self.latest: dict[tuple, tuple] = {}

    def get_last_run_at(self, source): return self.last_run
    def release_ingested(self, source, dataset_code, release_date): return self.releases.get((source, dataset_code, release_date), {}).get("status") == "ingested"
    def release_hash_seen(self, source, dataset_code, content_hash): return (source, dataset_code, content_hash) in self.hashes

    def store_release(self, *, source, ref, content_hash, parsed, licence, fetched_at):
        counts = {"new": 0, "revised": 0, "unchanged": 0}
        for o in parsed.observations:
            action, status = decide_vintage(self.latest.get((o.series_code, o.period_start)), o.value, o.value_status)
            counts["new" if action == "new" else action] += 1
            if action != "unchanged":
                self.latest[(o.series_code, o.period_start)] = (o.value, status)
        self.releases[(source, ref.dataset_code, ref.release_date)] = {"status": "ingested"}
        self.hashes.add((source, ref.dataset_code, content_hash))
        out = {"release_id": f"{source}:{ref.dataset_code}:{ref.release_date}", "rows_parsed": len(parsed.observations),
               "observations_new": counts["new"], "observations_revised": counts["revised"], "observations_unchanged": counts["unchanged"], "licence": licence}
        self.stored.append(out)
        return out

    def record_release_only(self, *, source, ref, content_hash, status, summary, fetched_at):
        self.releases[(source, ref.dataset_code, ref.release_date)] = {"status": status, "summary": summary}

    def record_run(self, *, source, ran_at, outcome, release_id, message):
        self.runs.append({"outcome": outcome, "release_id": release_id, "message": message})
        if outcome != "skipped_not_due":
            self.last_run = ran_at


NOW = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)


def _run(storage, fetcher=None, adapter=ADAPTER, **kw):
    fetcher = fetcher or FakeFetcher()
    return ingest_adapter(adapter, storage, lambda: fetcher, now=kw.pop("now", NOW), **kw), fetcher


# ── orchestrator ──────────────────────────────────────────────────────────────

def test_discover_uses_the_newest_version_date_never_the_stale_release_date():
    refs = ADAPTER.discover(FakeFetcher())
    assert {r.dataset_code: r.release_date for r in refs} == {"VACS02": date(2026, 9, 15), "VACS03": date(2026, 9, 15)}
    assert all(r.file_url.endswith(".xlsx") for r in refs)
    # ONS serves files through /file?uri=<path>, NOT the bare path (which 404s) — the first live run found this,
    # because the fakes above serve bytes for any URL. Pin the exact shape.
    assert all(r.file_url.startswith("https://www.ons.gov.uk/file?uri=/x/") and "/current/vacs0" in r.file_url for r in refs), [r.file_url for r in refs]


def test_first_run_stores_everything_and_records_the_run():
    s = FakeStorage()
    result, _ = _run(s)
    assert result.outcome == "new_release_ingested"
    assert len(s.stored) == 2 and s.runs[-1]["outcome"] == "new_release_ingested"
    by_ds = {x["release_id"].split(":")[1]: x for x in s.stored}
    # VACS02 is processed first: 20 series x 303 periods, all new
    assert by_ds["VACS02"]["observations_new"] == 20 * 303 and by_ds["VACS02"]["observations_revised"] == 0
    # VACS03 then finds AP2Y already stored by the first file — counted unchanged, never duplicated — and adds the 5 size series
    assert by_ds["VACS03"]["observations_new"] == 5 * 303 and by_ds["VACS03"]["observations_unchanged"] == 303
    assert all(x["licence"]["licence_confirmed"] for x in s.stored)


def test_an_already_ingested_release_is_never_downloaded_again():
    s = FakeStorage()
    _run(s)
    s.last_run = NOW - timedelta(hours=48)                         # due again, but nothing new is published
    result, fetcher = _run(s, now=NOW)
    assert result.outcome == "no_new_release"
    assert not any(u.endswith(".xlsx") for u in fetcher.requests), fetcher.requests   # only the cheap JSON discovery


def test_the_cadence_gate_makes_no_request_and_constructs_nothing():
    s = FakeStorage()
    s.last_run = NOW - timedelta(hours=2)
    def boom():
        raise AssertionError("the fetcher must not even be constructed when the run is not due")
    result = ingest_adapter(ADAPTER, s, boom, now=NOW)
    assert result.outcome == "skipped_not_due" and s.stored == []
    # ... and --force overrides it
    forced = ingest_adapter(ADAPTER, s, lambda: FakeFetcher(), now=NOW, force=True)
    assert forced.outcome == "new_release_ingested"


def test_a_failed_validation_rejects_the_release_and_stores_nothing():
    class BadAdapter(OnsVacancySurveyAdapter):
        def validate(self, parsed):
            return ["forced failure"]
    s = FakeStorage()
    result, _ = _run(s, adapter=BadAdapter())
    assert result.outcome == "rejected_validation" and s.stored == []
    assert s.releases[("ons_vacancy_survey", "VACS03", date(2026, 9, 15))]["status"] == "rejected_validation"


def test_a_layout_error_is_a_rejection_not_a_crash():
    class Garbled(FakeFetcher):
        def get_bytes(self, url):
            self.requests.append(url)
            return b"this is not a workbook"
    s = FakeStorage()
    result, _ = _run(s, fetcher=Garbled())
    assert result.outcome == "rejected_validation" and s.stored == []


def test_an_identical_file_is_recorded_but_never_reparsed():
    s = FakeStorage()
    _run(s)
    # the publisher re-stamps a byte-identical file under a NEW release date
    class Restamped(FakeFetcher):
        def get_json(self, url):
            d = super().get_json(url)
            d["versions"].append({"updateDate": "2026-10-20T06:00:00.000Z"})
            return d
    later = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)      # the 20 Oct release is 3 days old — past the 2-day settle
    s.last_run = NOW
    before = len(s.stored)
    result, _ = _run(s, fetcher=Restamped(), now=later)
    assert result.outcome == "no_new_release" and len(s.stored) == before
    assert s.releases[("ons_vacancy_survey", "VACS03", date(2026, 10, 20))]["status"] == "ingested"


def test_discover_failure_is_recorded_as_a_failed_run_never_raised():
    class Down(FakeFetcher):
        def get_json(self, url):
            raise StatisticsFetchError("ONS unreachable")
    s = FakeStorage()
    result, _ = _run(s, fetcher=Down())
    assert result.outcome == "failed" and s.runs[-1]["outcome"] == "failed"
    assert s.last_run is not None                                  # a broken source is not retried in a tight loop


def test_a_missing_contact_is_a_config_error_that_records_no_run():
    s = FakeStorage()
    def unconfigured():
        raise StatisticsConfigError("STATISTICS_CONTACT is unset")
    try:
        ingest_adapter(ADAPTER, s, unconfigured, now=NOW)
    except StatisticsConfigError:
        pass
    else:
        raise AssertionError("a config error must propagate")
    assert s.runs == [] and s.last_run is None, "a config error must not start the cadence clock"


def test_an_unregistered_publisher_or_licence_is_a_hard_error():
    class Nameless(OnsVacancySurveyAdapter):
        source = "not_a_registered_publisher"
    try:
        _run(FakeStorage(), adapter=Nameless())
    except KeyError:
        pass
    else:
        raise AssertionError("an adapter with no TRUSTED_PUBLISHERS entry was allowed to run")
    TRUSTED_PUBLISHERS["temp_no_licence"] = TRUSTED_PUBLISHERS["ons_vacancy_survey"].__class__(
        **{**TRUSTED_PUBLISHERS["ons_vacancy_survey"].__dict__, "source": "temp_no_licence"})
    try:
        class NoLicence(OnsVacancySurveyAdapter):
            source = "temp_no_licence"
        try:
            _run(FakeStorage(), adapter=NoLicence())
        except LicenceNotRegisteredError:
            pass
        else:
            raise AssertionError("an adapter with no SOURCE_LICENCES entry was allowed to run")
    finally:
        del TRUSTED_PUBLISHERS["temp_no_licence"]


def test_is_due_from_last_run():
    assert is_due_from_last_run(None, 24, NOW)
    assert not is_due_from_last_run(NOW - timedelta(hours=23), 24, NOW)
    assert is_due_from_last_run(NOW - timedelta(hours=24), 24, NOW)


# ── settle rule (a release is ingested only once it is 2 days old) and the overdue warning ──

def test_a_release_waits_two_days_before_it_is_ingested():
    s = FakeStorage()
    # the fake serves a release dated 2026-09-15
    for now, eligible in ((datetime(2026, 9, 15, 12, tzinfo=timezone.utc), False),     # released today
                          (datetime(2026, 9, 16, 12, tzinfo=timezone.utc), False),     # 1 day old
                          (datetime(2026, 9, 17, 0, 1, tzinfo=timezone.utc), True),    # exactly 2 days old — eligible
                          (datetime(2026, 9, 25, 12, tzinfo=timezone.utc), True)):
        s = FakeStorage()
        result, fetcher = _run(s, now=now)
        if eligible:
            assert result.outcome == "new_release_ingested", (now, result.outcome)
        else:
            assert result.outcome == "no_new_release" and s.stored == [], (now, result.outcome)
            assert not any(u.endswith(".xlsx") for u in fetcher.requests), "a settling release must not even be downloaded"
            assert any("waits 2 day(s)" in m and "eligible from 2026-09-17" in m for m in result.messages), result.messages


def test_the_settle_rule_does_not_depend_on_when_the_scheduler_fires():
    # Run at 06:00 every day around a release: nothing is ingested until the run on release date + 2, then it is, once.
    s = FakeStorage()
    outcomes = []
    for day in range(15, 21):
        s.last_run = None                                                  # isolate the settle rule from the cadence gate
        result, _ = _run(s, now=datetime(2026, 9, day, 6, 0, tzinfo=timezone.utc))
        outcomes.append((day, result.outcome))
    assert outcomes[0][1] == outcomes[1][1] == "no_new_release"            # 15th, 16th: settling
    assert outcomes[2] == (17, "new_release_ingested")                     # the 17th: released + 2 days
    assert all(o == "no_new_release" for _d, o in outcomes[3:])            # afterwards: nothing new, nothing re-downloaded


def test_publisher_settle_days_is_validated_and_defaults_to_two():
    good = dict(TRUSTED_PUBLISHERS["ons_vacancy_survey"].__dict__)
    assert TRUSTED_PUBLISHERS["ons_vacancy_survey"].release_settle_days == 2
    try:
        TrustedPublisher(**{**good, "release_settle_days": -1})
    except ValueError:
        pass
    else:
        raise AssertionError("a negative settle period was accepted")
    assert TrustedPublisher(**{**good, "release_settle_days": 0}).release_settle_days == 0


def test_the_daily_gate_tolerates_cron_jitter():
    # A daily cron starts a few minutes either side of the same time. The ONS gate is 20h (not 24h), so a run that starts
    # seconds early the next day is still due — an exact-24h gate would skip that day at random.
    hours = TRUSTED_PUBLISHERS["ons_vacancy_survey"].min_check_interval_hours
    assert hours == 20
    yesterday_0603 = datetime(2026, 9, 24, 6, 3, 55, tzinfo=timezone.utc)
    today_0600 = datetime(2026, 9, 25, 6, 0, 2, tzinfo=timezone.utc)      # 23h56m later
    assert is_due_from_last_run(yesterday_0603, hours, today_0600)
    assert not is_due_from_last_run(yesterday_0603, hours, yesterday_0603 + timedelta(hours=19))


def test_overdue_warning_thresholds():
    from statistics_storage import days_since, is_overdue
    today = date(2026, 11, 1)
    assert not is_overdue(None, today)                                      # never ingested is a different state, not "overdue"
    assert days_since(None, today) is None
    assert not is_overdue(today - timedelta(days=35), today)                # the normal maximum gap
    assert not is_overdue(today - timedelta(days=45), today)                # exactly the threshold: not yet
    assert is_overdue(today - timedelta(days=46), today)
    assert is_overdue(today - timedelta(days=63), today)                    # the two historical 63-day gaps WOULD warn (rare, worth a look)


# ── the polite fetcher ────────────────────────────────────────────────────────

def _fetcher(handler, **kw):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return PoliteFetcher("t", min_interval_seconds=0, backoff_base_seconds=0, client=client, **kw)


def _with_contact(value, fn):
    old = os.environ.get("STATISTICS_CONTACT")
    try:
        if value is None:
            os.environ.pop("STATISTICS_CONTACT", None)
        else:
            os.environ["STATISTICS_CONTACT"] = value
        return fn()
    finally:
        if old is None:
            os.environ.pop("STATISTICS_CONTACT", None)
        else:
            os.environ["STATISTICS_CONTACT"] = old


def test_fetcher_refuses_without_a_real_contact():
    for bad in (None, "", "  ", "set STATISTICS_CONTACT", "someone@example.com"):
        try:
            _with_contact(bad, lambda: _fetcher(lambda r: httpx.Response(200)))
        except StatisticsConfigError:
            continue
        raise AssertionError(f"constructed with contact {bad!r}")


def test_fetcher_identifies_itself_and_treats_a_404_or_html_robots_as_no_restrictions():
    seen = []
    def handler(req):
        seen.append((req.url.path, req.headers["user-agent"]))
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="<html>Page not found</html>", headers={"content-type": "text/html"})   # the real ONS behaviour
        return httpx.Response(200, json={"ok": True})
    f = _with_contact("TMIP research@tmip.test", lambda: _fetcher(handler))
    assert f.get_json("https://ons.test/data") == {"ok": True}
    assert all("TMIP research@tmip.test" in ua for _p, ua in seen)
    g = _with_contact("TMIP research@tmip.test", lambda: _fetcher(lambda r: httpx.Response(404) if r.url.path == "/robots.txt" else httpx.Response(200, json={"n": 1})))
    assert g.get_json("https://ons.test/data") == {"n": 1}


def test_fetcher_honours_a_real_disallow():
    def handler(req):
        if req.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /private/", headers={"content-type": "text/plain"})
        return httpx.Response(200, json={})
    f = _with_contact("TMIP research@tmip.test", lambda: _fetcher(handler))
    assert f.get_json("https://ons.test/public") == {}
    try:
        f.get_json("https://ons.test/private/x")
    except StatisticsFetchError:
        return
    raise AssertionError("a disallowed path was fetched")


def test_fetcher_retries_transient_failures_only():
    calls = {"n": 0}
    def flaky(req):
        if req.url.path == "/robots.txt":
            return httpx.Response(404)
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] < 3 else httpx.Response(200, json={"ok": 1})
    assert _with_contact("TMIP research@tmip.test", lambda: _fetcher(flaky)).get_json("https://ons.test/x") == {"ok": 1}
    assert calls["n"] == 3
    hard = {"n": 0}
    def gone(req):
        if req.url.path == "/robots.txt":
            return httpx.Response(404)
        hard["n"] += 1
        return httpx.Response(410)
    try:
        _with_contact("TMIP research@tmip.test", lambda: _fetcher(gone)).get_json("https://ons.test/x")
    except StatisticsFetchError:
        assert hard["n"] == 1                                       # 410 is not retried
        return
    raise AssertionError("a permanent failure was not raised")


# ── registry, licence and crosswalk completeness ──────────────────────────────

def test_every_adapter_has_a_publisher_and_a_licence_and_vice_versa():
    adapters = {a.source for a in ALL_STATISTICS_ADAPTERS}
    assert adapters == set(TRUSTED_PUBLISHERS), f"adapters {adapters} vs TRUSTED_PUBLISHERS {set(TRUSTED_PUBLISHERS)}"
    for source in adapters:
        assert source in SOURCE_LICENCES, f"{source} has no SOURCE_LICENCES entry"
        p = TRUSTED_PUBLISHERS[source]
        assert p.publisher and p.methodology_url.startswith("https://") and p.trust_bar_reviewed_on


def test_publisher_entries_are_validated():
    good = TRUSTED_PUBLISHERS["ons_vacancy_survey"].__dict__
    for override in ({"publisher_type": "a friend"}, {"datasets": ()}, {"min_check_interval_hours": 0}, {"methodology_url": " "}):
        try:
            TrustedPublisher(**{**good, **override})
        except ValueError:
            continue
        raise AssertionError(f"accepted {override}")


def test_ons_licence_is_the_confirmed_ogl_and_names_the_publisher():
    lic = SOURCE_LICENCES["ons_vacancy_survey"]
    assert lic.confirmed and lic.permits_commercial_use and not lic.rejected
    assert "Open Government Licence v3.0" in lic.licence
    assert "Office for National Statistics" in lic.attribution_text and "Open Government Licence v3.0" in lic.attribution_text


def test_every_industry_tag_has_a_crosswalk_decision():
    tags = set(industries.COMPANY_INDUSTRY.values())
    missing = tags - set(OUR_INDUSTRY_TO_SIC_SECTION)
    assert not missing, f"industry tags with no crosswalk decision (map to a SIC section or an explicit None): {sorted(missing)}"
    stale = set(OUR_INDUSTRY_TO_SIC_SECTION) - tags
    assert not stale, f"crosswalk entries for tags that no company carries: {sorted(stale)}"
    for tag, section in OUR_INDUSTRY_TO_SIC_SECTION.items():
        assert section is None or section in VACANCY_SURVEY_SECTIONS, (tag, section)
        assert section is None or section in SIC_2007_SECTIONS
    assert sic_section_for("Fintech") == "K" and sic_section_for("Marketplace") is None and sic_section_for(None) is None
    assert sic_section_for("a tag nobody has") is None            # never guessed

# ── the read side: query function, Story 5, cross-check, MCP tool, chat trace ──
# All against the REAL ONS values, served from an in-memory stand-in for statistics_storage (no database).

import json  # noqa: E402
import types  # noqa: E402

import market_query  # noqa: E402
import market_stories  # noqa: E402
import statistics_crosscheck  # noqa: E402
import statistics_storage  # noqa: E402
from mcp_access import tools as mcp_tools  # noqa: E402
from mcp_access.taxonomy import get_taxonomy  # noqa: E402
from statistics_crosscheck import ons_shares, platform_mix_from_counts  # noqa: E402
from trusted_stats.base import SeriesDefinition  # noqa: E402

_LICENCE = SOURCE_LICENCES["ons_vacancy_survey"]
_PUB = TRUSTED_PUBLISHERS["ons_vacancy_survey"]


def _series_row(d: SeriesDefinition) -> dict:
    return {"id": f"ons_vacancy_survey:{d.series_code}", "source": "ons_vacancy_survey", "publisher": _PUB.publisher,
            "programme": _PUB.programme, "dataset_code": d.dataset_code, "series_code": d.series_code, "title": d.title,
            "measure": d.measure, "unit": d.unit, "unit_scale": d.unit_scale, "seasonal_adjustment": d.seasonal_adjustment,
            "period_type": d.period_type, "frequency": d.frequency, "dimensions": d.dimensions, "dimension_type": d.dimension_type,
            "definition_note": d.definition_note, "coverage_note": d.coverage_note, "designation": d.designation,
            "methodology_url": d.methodology_url, "source_page_url": d.source_page_url, "licence": _LICENCE.licence,
            "licence_confirmed": _LICENCE.confirmed, "attribution_text": _LICENCE.attribution_text}


class FakeStatsStore:
    """Stands in for statistics_storage's read functions, filled from the real parsed files."""
    def __init__(self, releases=(REF03, REF02), blank=False):
        self.rows: list[dict] = []
        seen = set()
        for ref in releases:
            p = _parsed(ref, VACS02_BYTES if ref.dataset_code == "VACS02" else VACS03_BYTES)
            series = {d.series_code: _series_row(d) for d in p.series}
            for o in p.observations:
                if blank or (o.series_code, o.period_start) in seen:
                    continue
                seen.add((o.series_code, o.period_start))
                self.rows.append({"series": series[o.series_code], "observation": {
                    "id": f"{o.series_code}:{o.period_start}", "series_id": series[o.series_code]["id"], "release_id": "r",
                    "period_start": o.period_start, "period_end": o.period_end, "period_label": o.period_label, "value": o.value,
                    "value_status": o.value_status, "raw_cell": o.raw_cell, "released_on": date(2026, 9, 15),
                    "licence": _LICENCE.licence, "licence_confirmed": True, "fetched_at": None}})

    def fetch_observations(self, *, sources=None, dimension_type=None, industry_code=None, size_band=None, periods=None,
                           date_from=None, date_to=None):
        out = []
        for r in self.rows:
            s, o = r["series"], r["observation"]
            if dimension_type and s["dimension_type"] != dimension_type: continue
            if industry_code and s["dimensions"].get("industry", {}).get("code") != industry_code: continue
            if size_band and s["dimensions"].get("size_band", {}).get("code") != size_band: continue
            if periods and o["period_start"] not in periods: continue
            if date_from and o["period_start"] < date_from: continue
            if date_to and o["period_end"] > date_to: continue
            out.append(r)
        return out

    def latest_period_start(self, *, sources=None, dimension_type=None):
        ps = [r["observation"]["period_start"] for r in self.rows if not dimension_type or r["series"]["dimension_type"] == dimension_type]
        return max(ps) if ps else None


class _patched:
    """Context manager: swap statistics_storage's read functions for a fake store (and optionally the UK posting counts)."""
    def __init__(self, store, uk_counts=None, usable=True):
        self.store, self.uk_counts, self.usable = store, uk_counts, usable
    def __enter__(self):
        import source_licences
        self._saved = (statistics_storage.fetch_observations, statistics_storage.latest_period_start,
                       statistics_crosscheck._uk_company_counts, source_licences.is_source_usable)
        statistics_storage.fetch_observations = self.store.fetch_observations
        statistics_storage.latest_period_start = self.store.latest_period_start
        if self.uk_counts is not None:
            statistics_crosscheck._uk_company_counts = lambda: self.uk_counts
        source_licences.is_source_usable = lambda s: self.usable
        return self
    def __exit__(self, *a):
        import source_licences
        (statistics_storage.fetch_observations, statistics_storage.latest_period_start,
         statistics_crosscheck._uk_company_counts, source_licences.is_source_usable) = self._saved


_UK_COUNTS = ({"monzo": 100, "wise": 50, "starling-bank": 30, "deliveroo": 20, "trainline": 25, "gymshark": 40, "autotrader": 10}, 1000, 700)


def test_query_returns_named_sources_on_every_series():
    with _patched(FakeStatsStore()):
        r = market_query.query_trusted_statistics_data(dimension="industry")
    assert r["usable"] and r["total_matching"] == 19 and r["latest_period_label"] == "Jun-Aug 2026"    # 18 sections + the G-S aggregate
    for st in r["statistics"]:
        src = st["series"]["source"]
        for f in ("publisher", "programme", "dataset_code", "series_code", "source_url", "licence", "attribution_text"):
            assert str(src[f]).strip(), f"{st['series']['title']}: empty source.{f}"
        assert src["publisher"] == "Office for National Statistics" and src["licence_confirmed"] is True
        assert st["series"]["unit"] == "thousand vacancies" and len(st["observations"]) == 1
    json.dumps(r)                                                   # must serialise as-is (the Decimal bug lesson)


def test_query_periods_and_filters():
    with _patched(FakeStatsStore()):
        latest = market_query.query_trusted_statistics_data(dimension="total")
        assert [o["period_label"] for o in latest["statistics"][0]["observations"]] == ["Jun-Aug 2026"]
        ya = market_query.query_trusted_statistics_data(dimension="total", period="year_ago")
        assert sorted(o["period_label"] for o in ya["statistics"][0]["observations"]) == ["Jun-Aug 2025", "Jun-Aug 2026"]
        pq = market_query.query_trusted_statistics_data(dimension="total", period="previous_quarter")
        assert sorted(o["period_label"] for o in pq["statistics"][0]["observations"]) == ["Jun-Aug 2026", "Mar-May 2026"]
        j = market_query.query_trusted_statistics_data(dimension="industry", industry_code="J")
        assert j["total_matching"] == 1 and j["statistics"][0]["observations"][0]["value"] == 36.0
        band = market_query.query_trusted_statistics_data(dimension="size_band", size_band="2500+")
        assert band["statistics"][0]["observations"][0]["value"] == 240.0


def test_query_rejects_bad_parameters_and_says_so_when_nothing_is_collected_or_usable():
    for kwargs in ({"dimension": "region"}, {"period": "next_year"}, {"publisher": "not_registered"}):
        try:
            market_query.query_trusted_statistics_data(**kwargs)
        except ValueError:
            continue
        raise AssertionError(f"accepted {kwargs}")
    with _patched(FakeStatsStore(blank=True)):
        r = market_query.query_trusted_statistics_data()
        assert r["statistics"] == [] and r["usable"] is True and r["sources_checked"] == ["ons_vacancy_survey"]   # "checked, nothing yet"
    with _patched(FakeStatsStore(), usable=False):
        r = market_query.query_trusted_statistics_data()
        assert r["usable"] is False and r["statistics"] == [] and r["sources_unavailable"] == ["ons_vacancy_survey"]


def test_a_statistic_that_cannot_name_its_source_is_never_returned():
    row = _series_row(_parsed().series[0])
    market_query.named_source(row)                                  # fine as-is
    for field in ("publisher", "programme", "dataset_code", "series_code", "source_page_url", "licence", "attribution_text"):
        try:
            market_query.named_source({**row, field: " "})
        except ValueError:
            continue
        raise AssertionError(f"a statistic with an empty {field} was returned")


def test_crosscheck_arithmetic():
    mix = platform_mix_from_counts({"a": 60, "b": 30, "c": 10}, lambda c: {"a": "J", "b": "K"}.get(c))
    assert mix["postings"] == 100 and mix["shares_pct"] == {"J": 60.0, "K": 30.0} and mix["unplaced_count"] == 10 and mix["unplaced_share_pct"] == 10.0
    assert platform_mix_from_counts({}, lambda c: "J")["shares_pct"] == {} and platform_mix_from_counts({}, lambda c: "J")["unplaced_share_pct"] is None
    assert ons_shares({"J": 36.0, "K": 30.0}, 702.0) == {"J": 5.13, "K": 4.27} and ons_shares({"J": 1.0}, 0) == {}


def test_story5_sections_and_numbers_come_from_the_real_figures():
    with _patched(FakeStatsStore(), _UK_COUNTS):
        story = market_stories.get_story("uk-vacancies-official")
    json.dumps(story)                                               # serialisable as-is
    sec = {s["id"]: s for s in story["sections"]}
    assert list(sec) == ["uk-vacancies-total", "uk-vacancies-by-industry", "uk-vacancies-by-size", "uk-industry-shift", "industry-crosscheck"]
    assert all(s["status"] == "ready" for s in sec.values()), {k: v["status"] for k, v in sec.items()}
    t = sec["uk-vacancies-total"]["content"]
    assert (t["total"], t["previous_total"], t["change"], t["change_pct"]) == (702000, 710000, -8000, -1.1)     # ONS's own -8k, -1.1%
    assert (t["period_label"], t["previous_period_label"], t["value_status"]) == ("Jun-Aug 2026", "Mar-May 2026", "provisional")
    ind = sec["uk-vacancies-by-industry"]["content"]
    assert ind["shown"] == 10 and ind["of"] == 18 and ind["rows"][0]["code"] == "Q" and ind["rows"][0]["value"] == 121.0
    assert [r["value"] for r in ind["rows"]] == sorted((r["value"] for r in ind["rows"]), reverse=True)
    size = sec["uk-vacancies-by-size"]["content"]["rows"]
    assert [r["code"] for r in size] == ["1-9", "10-49", "50-249", "250-2499", "2500+"]           # the ORDER is the meaning
    assert [r["share_pct"] for r in size] == [13.0, 14.1, 14.7, 24.1, 34.2]
    shift = sec["uk-industry-shift"]["content"]
    assert len(shift["rows"]) == 8 and shift["prior_period_label"] == "Jun-Aug 2025" and all(r["prior"] is not None for r in shift["rows"])
    assert story["attribution_text"].startswith("Source: Office for National Statistics — Vacancy Survey.")
    for sid in ("uk-vacancies-total", "uk-vacancies-by-industry", "uk-vacancies-by-size", "uk-industry-shift", "industry-crosscheck"):
        att = sec[sid]["content"]["attribution"]
        assert att["publisher"] == "Office for National Statistics" and "Open Government Licence v3.0" in att["text"] and att["licence_confirmed"] is True
    assert story["provenance"]["model_used"] is False


def test_story5_visible_copy_carries_no_implementation_words_or_raw_dates():
    import re
    with _patched(FakeStatsStore(), _UK_COUNTS):
        story = market_stories.get_story("uk-vacancies-official")
    visible = [s["qualifier"] for s in story["sections"]] + [s["content"].get("legend", "") for s in story["sections"]]
    for text in visible:
        for banned in ("SIC", "QMI", "adapter", "series", "dataset", "VACS"):
            assert banned not in text, f"{banned!r} leaked into visible copy: {text!r}"
        assert not re.search(r"\d{4}-\d{2}-\d{2}", text), f"raw ISO date in visible copy: {text!r}"
    total_q = {s["id"]: s for s in story["sections"]}["uk-vacancies-total"]["qualifier"]
    assert "farming, forestry and fishing" in total_q and "Great Britain" in total_q     # scope stated, in plain words
    # the publisher's own footnote wording is still kept for the Reasoning Panel
    assert any("SIC07" in lim or "agriculture, forestry and fishing" in lim for lim in story["limitations"])


def test_story5_crosscheck_shows_two_shares_and_never_a_difference():
    with _patched(FakeStatsStore(), _UK_COUNTS):
        c = {s["id"]: s for s in market_stories.get_story("uk-vacancies-official")["sections"]}["industry-crosscheck"]
    content = c["content"]
    assert content["primary_name"] == "Roles we track" and content["secondary_name"] == "UK vacancies (ONS)"
    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield str(k).lower(); yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    for k in keys(content):
        for banned in ("diff", "delta", "score", "ratio", "represent", "gap"):
            assert banned not in k, f"the comparison payload must never carry a difference (key {k!r})"
    rows = {r["code"]: r for r in content["rows"]}
    # Monzo 100 + Wise 50 + Starling 30 = 180 of the 275 UK-located roles; ONS: section K = 30 of 702 thousand
    assert rows["K"]["primary_share_pct"] == round(100 * 180 / 275, 2) and rows["K"]["secondary_share_pct"] == round(100 * 30 / 702, 2)
    assert rows[None]["primary_share_pct"] == 20.0                   # deliveroo + trainline + autotrader = 55 of 275 are not placed
    assert rows[None]["label"] == "Not placed in an industry group" and rows[None]["secondary_share_pct"] is None
    assert content["platform_total"] == 275 and content["location_unknown_count"] == 700 and content["stored_roles_total"] == 1000
    assert "aren't expected to match" in c["qualifier"] and "700" in c["qualifier"]                    # coverage stated, not hidden
    assert "Solid bar" in content["legend"] and "three months to August 2026" in content["legend"]
    import re
    assert not re.search(r"\d{4}-\d{2}-\d{2}", content["legend"]), "visible copy must not carry a raw ISO date"


def test_story5_states_the_honest_empty_states():
    with _patched(FakeStatsStore(blank=True), _UK_COUNTS):
        s = market_stories.get_story("uk-vacancies-official")
    assert all(x["status"] == "insufficient_data" and x["message"] == "We haven't collected the official UK figures yet." for x in s["sections"])
    assert all(x["qualifier"] == "" for x in s["sections"]), "the message is the line — a duplicate qualifier would show it twice"
    with _patched(FakeStatsStore(), _UK_COUNTS, usable=False):
        s = market_stories.get_story("uk-vacancies-official")
    assert all(x["status"] == "insufficient_data" and x["message"] == "This data source isn't currently available." for x in s["sections"])
    with _patched(FakeStatsStore(), ({}, 1000, 1000)):              # nothing has a UK location recorded
        s = {x["id"]: x for x in market_stories.get_story("uk-vacancies-official")["sections"]}
    assert s["industry-crosscheck"]["status"] == "insufficient_data" and "UK-based roles" in s["industry-crosscheck"]["message"]
    assert s["uk-vacancies-total"]["status"] == "ready"             # the first four blocks still render


def test_story_is_in_the_catalogue():
    ids = [x["id"] for x in market_stories.list_stories()["stories"]]
    assert ids[-1] == "uk-vacancies-official" and market_stories.STORY_CATALOGUE[4]["display_name"] == "UK vacancies (official data)"


def test_mcp_tool_names_the_publisher_inside_the_payload():
    assert mcp_tools.TOOL_SCOPES["get_trusted_statistics"] == "jobs.read" and "get_trusted_statistics" not in mcp_tools.PREMIUM_ONLY_TOOLS
    with _patched(FakeStatsStore()):
        r = mcp_tools.get_trusted_statistics(dimension="size_band", period="year_ago")
    assert "error" not in r and r["data"]["statistics"]
    meta = r["meta"]
    assert "Office for National Statistics" in meta["source"] and "Open Government Licence v3.0" in meta["source"]
    assert "not this platform's own job postings" in meta["source"]
    assert any("Contains public sector information" in a for a in meta["attribution"]) and meta["licence_unconfirmed"] == []
    assert meta["sources_checked"] == ["ons_vacancy_survey"] and "thousand vacancies" in meta["unit"] and "Jun-Aug 2026" in meta["time_window"]["label"]
    assert "Great Britain" in r["data"]["coverage_note"]
    json.dumps(r)


def test_mcp_tool_answers_bad_input_and_empty_state_honestly():
    with _patched(FakeStatsStore()):
        assert "wasn't valid" in mcp_tools.get_trusted_statistics(dimension="region")["data"]["message"]
    with _patched(FakeStatsStore(blank=True)):
        r = mcp_tools.get_trusted_statistics()
        assert r["data"]["statistics"] == [] and "nothing collected yet" in r["meta"]["source"]
    with _patched(FakeStatsStore(), usable=False):
        assert "isn't currently available" in mcp_tools.get_trusted_statistics()["data"]["message"]


def test_taxonomy_gives_an_ai_the_valid_parameter_values():
    d = get_taxonomy()["data"]["statistic_dimensions"]
    assert len(d["industry_code"]) == 18 and {"value": "J", "label": "Information and communication"} in d["industry_code"]
    assert [b["value"] for b in d["size_band"]] == ["1-9", "10-49", "50-249", "250-2499", "2500+"]
    assert d["publisher"][0]["value"] == "ons_vacancy_survey" and {p["value"] for p in d["period"]} == {"latest", "year_ago", "previous_quarter"}


def test_chat_trace_names_the_publisher_and_flags_an_unconfirmed_licence():
    import chat
    src = {"publisher": "Office for National Statistics", "programme": "Vacancy Survey", "dataset_code": "VACS03",
           "licence": "Open Government Licence v3.0", "licence_confirmed": True}
    def call(confirmed):
        s = {**src, "licence_confirmed": confirmed}
        return types.SimpleNamespace(name="query_trusted_statistics_data", args={"dimension": "total"},
                                     result={"statistics": [{"series": {"source": s}}], "total_matching": 1, "latest_period_label": "Jun-Aug 2026"})
    trace = chat._build_reasoning_trace("How many vacancies?", [call(True)])
    assert any("Office for National Statistics" in s.name and "Open Government Licence v3.0" in s.name for s in trace.sources_and_tools)
    assert not any("not yet confirmed" in st.content for st in trace.reasoning_steps)
    warned = chat._build_reasoning_trace("How many vacancies?", [call(False)])
    assert any("usage terms" in st.content and "not yet confirmed" in st.content for st in warned.reasoning_steps)

if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")

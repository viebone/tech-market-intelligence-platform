"""
ONS Vacancy Survey adapter — VACS02 (vacancies by industry, SIC 2007) and VACS03 (by size of business).

Written against the REAL files, inspected 2026-09-24/25 (research/2026-09-24-ons-licence-and-access-
confirmation.md); every rule below exists because of something seen in them:

- Release discovery uses ONS's own page-data JSON (`<dataset page>/current/data`): `downloads[0].file` is
  the current file (downloaded from `https://www.ons.gov.uk/file?uri=<uri>/<file>` — the bare path 404s) and `versions[]` lists every release with its `updateDate`. `description.releaseDate`
  is 2016 (the dataset's FIRST release) and is never used. No HTML is parsed — this is not scraping.
- Locate by pattern, never by row number: the sheets are ~720 rows, mostly empty, with change/summary rows
  and footnotes under the data. Series are keyed on ONS's own series IDs (row of IDs like `AP2Y`, `JP9P`).
- Header text is unreliable ("Manu-    facturing", "Construc-tion", truncated). The code row / ID row are
  authoritative; labels come from sic.py and from this file's size-band table.
- Period labels are three-month rolling averages ("Jun-Aug 2026"; one stray space: "Nov- Jan 2002"),
  labelled by their END year. Values are thousands. Column B carries a flag: `(p)` provisional, `(r)`
  revised, blank final.
- VACS02 footnotes: marker digits are appended to header text ("Real estate activities2"). On the `levels`
  sheet footnote 2 says the series is NOT seasonally adjusted (it shows no seasonality); footnote 3 is a
  coverage note about Administrative and support services. Footnote 1 is the survey's scope note, copied
  verbatim into `coverage_note`.
- VACS03 says nothing about seasonal adjustment in the file; ONS's methodology (QMI) states the
  by-industry and by-size three-month series are seasonally adjusted — recorded, with that source.
- Size bands: the file labels the smallest "1 - 9"; the methodology says "2 to 9" (a business with one
  person on the register is modelled, not surveyed). The stored code is `1-9`.
- Not ingested (deferred, spec Open Questions): the VACS02 `job openings rate` sheet, divisions 45/46/47
  (columns W-Y have no series ID in the header), X06.

`parse` is a pure function of the bytes; `validate` rejects a release that is not internally consistent.
"""

from __future__ import annotations

import calendar
import re
from datetime import date, datetime

from trusted_stats.base import (
    FetchedStatistic, LayoutError, ParsedRelease, PoliteFetcher, ReleaseRef, SeriesDefinition, StatisticsFetchError,
)
from trusted_stats.sic import SIC_2007_SECTIONS, VACANCY_SURVEY_SECTIONS
from trusted_stats.xlsx_reader import Row, XlsxError, read_workbook

ONS_ORIGIN = "https://www.ons.gov.uk"
METHODOLOGY_URL = "https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/vacancysurveyqmi"

DATASETS: dict[str, dict] = {
    "VACS02": {
        "page": ONS_ORIGIN + "/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbyindustryvacs02",
        "sheet": "levels",
    },
    "VACS03": {
        "page": ONS_ORIGIN + "/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbysizeofbusinessvacs03",
        "sheet": "VACS03",
    },
}

TOTAL_SERIES = "AP2Y"                      # all vacancies — appears in BOTH files (one series, first-seen dataset kept)
VACS02_AGGREGATE_SERIES = {"JP9Z": ("G-S", "Total services (SIC 2007 sections G–S)")}
# VACS03 columns are checked against these size classes by header text AND ID, so a reordered file is rejected.
SIZE_SERIES = {
    "ALY5": ("1-9", "1–9 employees", "1-9"),
    "ALY6": ("10-49", "10–49 employees", "10-49"),
    "ALY7": ("50-249", "50–249 employees", "50-249"),
    "ALY8": ("250-2499", "250–2,499 employees", "250-2,499"),
    "ALY9": ("2500+", "2,500 or more employees", "2,500+"),
}

UK_GEOGRAPHY = {"system": "ONS_area", "code": "K02000001", "label": "United Kingdom"}
GB_TO_UK_NOTE = ("The survey covers Great Britain (England, Scotland, Wales); ONS weights it up to the UK using employment "
                 "estimates (Northern Ireland is about 3% of UK employment) — Vacancy Survey QMI.")
TOTAL_DEFINITION = ("Estimated job vacancies — those an employer is actively seeking to fill from outside the organisation on the "
                    "survey's specified date — averaged over three months. All industries covered by the survey and all business "
                    "sizes. Seasonally adjusted (stated in the VACS02 file title and in ONS's Vacancy Survey methodology).")
SIZE_DEFINITION = ("Estimated job vacancies (three-month rolling average) at businesses in this employment size band, by register "
                   "employment. ONS's methodology calls the smallest band '2 to 9'; the file labels it '1 - 9' — businesses with one "
                   "person on the register are modelled rather than surveyed. Seasonal adjustment is not stated in the file; ONS's "
                   "Vacancy Survey methodology (QMI) states the by-size series is seasonally adjusted.")
INDUSTRY_DEFINITION = "Estimated job vacancies (three-month rolling average) in this industry (SIC 2007), in thousands."

_PERIOD_RE = re.compile(r"^([A-Za-z]{3})-\s*([A-Za-z]{3})\s+(\d{4})$")
_ID_RE = re.compile(r"^[A-Z][A-Z0-9]{2,4}$")   # ONS series IDs: AP2Y, ALY5, JP9P ...
_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}


# ── pure helpers ──────────────────────────────────────────────────────────────

def parse_period(label: str) -> tuple[date, date, str]:
    """'Jun-Aug 2026' -> (2026-06-01, 2026-08-31, 'Jun-Aug 2026'). Labelled by END year: 'Nov-Jan 2002' = Nov 2001-Jan 2002."""
    m = _PERIOD_RE.match(label.strip())
    if not m:
        raise ValueError(f"not a period label: {label!r}")
    m1, m2, year = m.group(1).lower(), m.group(2).lower(), int(m.group(3))
    if m1 not in _MONTHS or m2 not in _MONTHS:
        raise ValueError(f"unknown month in {label!r}")
    start_m, end_m = _MONTHS[m1], _MONTHS[m2]
    start_year = year if start_m <= end_m else year - 1
    return (date(start_year, start_m, 1), date(year, end_m, calendar.monthrange(year, end_m)[1]),
            f"{m.group(1).title()}-{m.group(2).title()} {year}")


def status_from_flag(flag: str | float | None) -> str:
    f = ("" if flag is None else str(flag)).strip().lower()
    return {"": "final", "(p)": "provisional", "(r)": "revised"}.get(f, "unknown")


def _row_with(rows: list[Row], predicate) -> Row | None:
    for row in rows:
        if predicate(row[1]):
            return row
    return None


def _observations(rows: list[Row], columns: dict[str, str]) -> list[FetchedStatistic]:
    """columns: column letter -> series_code. Every period row, every mapped column; a non-numeric cell ('..', '-')
    yields NO observation — never 0."""
    out: list[FetchedStatistic] = []
    seen: set[str] = set()
    for _rn, cells in rows:
        label = cells.get("A")
        if not isinstance(label, str) or not _PERIOD_RE.match(label.strip()):
            continue
        start, end, clean = parse_period(label)
        if clean in seen:
            raise LayoutError(f"period {clean!r} appears twice — the file is not laid out as expected")
        seen.add(clean)
        flag = cells.get("B")
        status = status_from_flag(flag)
        for col, series_code in columns.items():
            v = cells.get(col)
            if isinstance(v, float):
                out.append(FetchedStatistic(series_code, start, end, clean, v, status, f"{v:g}|{'' if flag is None else flag}"))
    return out


def _series_common(series_code: str, dataset_code: str, title: str, dimension_type: str, dimensions: dict, *,
                   seasonal: str, definition_note: str, coverage_note: str) -> SeriesDefinition:
    return SeriesDefinition(
        series_code=series_code, dataset_code=dataset_code, title=title, measure="vacancies_level",
        unit="thousand vacancies", unit_scale=1000, seasonal_adjustment=seasonal, period_type="rolling_3_month",
        frequency="monthly", dimensions=dimensions, dimension_type=dimension_type, definition_note=definition_note,
        coverage_note=coverage_note, designation="accredited_official_statistics", methodology_url=METHODOLOGY_URL,
        source_page_url=DATASETS[dataset_code]["page"],
    )


# ── the adapter ───────────────────────────────────────────────────────────────

class OnsVacancySurveyAdapter:
    source = "ons_vacancy_survey"

    # discover ---------------------------------------------------------------
    def discover(self, fetcher: PoliteFetcher) -> list[ReleaseRef]:
        refs: list[ReleaseRef] = []
        for code, cfg in DATASETS.items():
            data = fetcher.get_json(cfg["page"] + "/current/data")
            versions = data.get("versions") or []
            downloads = data.get("downloads") or []
            uri = data.get("uri")
            if not versions or not downloads or not uri:
                raise StatisticsFetchError(f"{code}: page-data JSON has no versions/downloads/uri — layout changed")
            file_name = downloads[0].get("file", "")
            if not file_name.lower().endswith(".xlsx"):
                raise StatisticsFetchError(f"{code}: current download {file_name!r} is not an .xlsx file")
            try:
                # Newest release by its own updateDate — NOT description.releaseDate (2016, the first release).
                latest = max(datetime.fromisoformat(v["updateDate"].replace("Z", "+00:00")) for v in versions)
            except (KeyError, ValueError) as exc:
                raise StatisticsFetchError(f"{code}: unreadable version dates ({exc})") from exc
            refs.append(ReleaseRef(dataset_code=code, release_date=latest.date(), release_uri=ONS_ORIGIN + uri,
                                   file_url=f"{ONS_ORIGIN}/file?uri={uri}/{file_name}", file_name=file_name))   # ONS serves files via /file?uri=, not the bare path (found by the first live run, 2026-09-25)
        return refs

    # parse ------------------------------------------------------------------
    def parse(self, ref: ReleaseRef, file_bytes: bytes) -> ParsedRelease:
        try:
            sheets = read_workbook(file_bytes)
        except XlsxError as exc:
            raise LayoutError(f"{ref.dataset_code}: {exc}") from exc
        sheet = sheets.get(DATASETS[ref.dataset_code]["sheet"])
        if not sheet:
            raise LayoutError(f"{ref.dataset_code}: expected sheet {DATASETS[ref.dataset_code]['sheet']!r}; found {sorted(sheets)}")
        if ref.dataset_code == "VACS03":
            return self._parse_vacs03(sheet)
        return self._parse_vacs02(sheet)

    def _parse_vacs03(self, rows: list[Row]) -> ParsedRelease:
        id_row = _row_with(rows, lambda c: TOTAL_SERIES in c.values())
        if id_row is None:
            raise LayoutError("VACS03: no row of series IDs containing AP2Y")
        id_by_col = {col: v for col, v in id_row[1].items() if isinstance(v, str) and _ID_RE.match(v)}
        label_row = dict(rows).get(id_row[0] - 1, {})
        col_of = {v: c for c, v in id_by_col.items()}
        missing = [sid for sid in (TOTAL_SERIES, *SIZE_SERIES) if sid not in col_of]
        if missing:
            raise LayoutError(f"VACS03: expected series {missing} not found in the ID row")
        columns = {col_of[TOTAL_SERIES]: TOTAL_SERIES}
        defs = [_series_common(TOTAL_SERIES, "VACS03", "Vacancies — all industries and business sizes (UK)", "total",
                               {"geography": UK_GEOGRAPHY}, seasonal="seasonally_adjusted", definition_note=TOTAL_DEFINITION,
                               coverage_note=self._scope_note(rows))]
        for sid, (code, label, header_marker) in SIZE_SERIES.items():
            col = col_of[sid]
            header = re.sub(r"\s+", "", str(label_row.get(col, "")).lower().replace("employed", ""))
            if header_marker.replace(",", "") not in header.replace(",", ""):
                raise LayoutError(f"VACS03: column {col} ({sid}) header {label_row.get(col)!r} does not look like the {label!r} band")
            columns[col] = sid
            defs.append(_series_common(sid, "VACS03", f"Vacancies — businesses with {label}", "size_band",
                                       {"size_band": {"system": "ONS_VS_size_band", "code": code, "label": label},
                                        "geography": UK_GEOGRAPHY},
                                       seasonal="seasonally_adjusted", definition_note=SIZE_DEFINITION,
                                       coverage_note=self._scope_note(rows)))
        return ParsedRelease("VACS03", defs, _observations(rows, columns))

    def _parse_vacs02(self, rows: list[Row]) -> ParsedRelease:
        label_row = _row_with(rows, lambda c: isinstance(c.get("A"), str) and c["A"].strip().lower().startswith("sic 2007"))
        if label_row is None:
            raise LayoutError("VACS02: no 'SIC 2007 sections' header row")
        by_num = dict(rows)
        code_cells, id_cells = by_num.get(label_row[0] + 1, {}), by_num.get(label_row[0] + 2, {})
        if "B-S" not in code_cells.values() or TOTAL_SERIES not in id_cells.values():
            raise LayoutError("VACS02: the SIC-code row (B-S) and series-ID row (AP2Y) are not where the header says")
        title = " ".join(str(v) for r, c in rows[:3] for v in c.values() if isinstance(v, str))
        sheet_seasonal = "seasonally_adjusted" if "seasonally adjusted" in title.lower() else "unknown"
        footnotes = self._footnotes(rows)
        scope = self._scope_note(rows)

        columns: dict[str, str] = {}
        defs: list[SeriesDefinition] = []
        sections_seen: set[str] = set()
        for col, sid in id_cells.items():
            if not isinstance(sid, str) or not _ID_RE.match(sid):
                continue
            code = str(code_cells.get(col, "")).strip()
            marker = re.search(r"(?<=\D)(\d+)\s*$", str(label_row[1].get(col, "")).strip())
            fn_text = footnotes.get(marker.group(1)) if marker else None
            not_adjusted = bool(fn_text and fn_text.lower().startswith("not seasonally adjusted"))
            seasonal = "not_adjusted" if not_adjusted else sheet_seasonal
            note_parts = [INDUSTRY_DEFINITION]
            coverage = scope
            if fn_text:
                if not_adjusted:
                    note_parts.append(fn_text)
                elif marker and marker.group(1) != "1":
                    coverage = f"{scope} Footnote {marker.group(1)} to this series: {fn_text}"
            if sid == TOTAL_SERIES and code == "B-S":
                d = _series_common(sid, "VACS02", "Vacancies — all industries and business sizes (UK)", "total",
                                   {"geography": UK_GEOGRAPHY}, seasonal="seasonally_adjusted",
                                   definition_note=TOTAL_DEFINITION, coverage_note=coverage)
            elif code in VACANCY_SURVEY_SECTIONS:
                sections_seen.add(code)
                d = _series_common(sid, "VACS02", f"Vacancies — {SIC_2007_SECTIONS[code]}", "industry",
                                   {"industry": {"system": "SIC2007_section", "code": code, "label": SIC_2007_SECTIONS[code]},
                                    "geography": UK_GEOGRAPHY},
                                   seasonal=seasonal, definition_note=" ".join(note_parts), coverage_note=coverage)
            elif sid in VACS02_AGGREGATE_SERIES and code == VACS02_AGGREGATE_SERIES[sid][0]:
                d = _series_common(sid, "VACS02", f"Vacancies — {VACS02_AGGREGATE_SERIES[sid][1]}", "industry",
                                   {"industry": {"system": "SIC2007_aggregate", "code": code, "label": VACS02_AGGREGATE_SERIES[sid][1]},
                                    "geography": UK_GEOGRAPHY},
                                   seasonal=seasonal, definition_note=" ".join(note_parts), coverage_note=coverage)
            else:
                continue          # a column with an ID we don't recognise: not ingested, never guessed
            columns[col] = sid
            defs.append(d)
        missing = sorted(set(VACANCY_SURVEY_SECTIONS) - sections_seen)
        if missing or TOTAL_SERIES not in columns.values():
            raise LayoutError(f"VACS02: missing series for sections {missing} (or the AP2Y total)")
        return ParsedRelease("VACS02", defs, _observations(rows, columns))

    @staticmethod
    def _footnotes(rows: list[Row]) -> dict[str, str]:
        out: dict[str, str] = {}
        for _rn, cells in rows:
            a = cells.get("A")
            if isinstance(a, str):
                m = re.match(r"^(\d+)\.\s+(.*\S)", a.strip())
                if m:
                    out[m.group(1)] = " ".join(m.group(2).split())
        return out

    def _scope_note(self, rows: list[Row]) -> str:
        fn1 = self._footnotes(rows).get("1", "")
        return f"{fn1} {GB_TO_UK_NOTE}".strip()

    # validate ---------------------------------------------------------------
    def validate(self, parsed: ParsedRelease) -> list[str]:
        failures: list[str] = []
        by_series: dict[str, dict[date, float]] = {}
        for o in parsed.observations:
            by_series.setdefault(o.series_code, {})[o.period_start] = o.value
        expected = ({TOTAL_SERIES, *SIZE_SERIES} if parsed.dataset_code == "VACS03"
                    else {TOTAL_SERIES, *VACS02_AGGREGATE_SERIES, *(d.series_code for d in parsed.series if d.dimension_type == "industry"
                                                                    and d.dimensions["industry"]["system"] == "SIC2007_section")})
        defined = {d.series_code for d in parsed.series}
        if defined != expected:
            failures.append(f"series defined {sorted(defined ^ expected)} differ from expected")
        for sid in expected:
            if not by_series.get(sid):
                failures.append(f"series {sid} has no observations")
        if failures:
            return failures

        total = by_series[TOTAL_SERIES]
        periods = sorted(total)
        # contiguous months, identical periods across every series
        for a, b in zip(periods, periods[1:]):
            if (b.year * 12 + b.month) - (a.year * 12 + a.month) != 1:
                failures.append(f"period sequence not contiguous between {a} and {b}")
                break
        latest = periods[-1]
        for sid, vals in by_series.items():
            if latest not in vals:
                failures.append(f"series {sid} has no value for the newest period {latest}")
        if failures:
            return failures

        # plausibility (unit-slip guard): total between 100k and 2M vacancies, nothing negative
        if not (100 <= total[latest] <= 2000):
            failures.append(f"newest total {total[latest]} (thousand) is outside the plausible 100-2,000 range")
        if any(v < 0 for vals in by_series.values() for v in vals.values()):
            failures.append("a negative vacancy count")

        # sum of parts, every period the parts exist for: rounding of n published integers can differ by n*0.5 (+0.5 for the total)
        parts = list(SIZE_SERIES) if parsed.dataset_code == "VACS03" else [
            d.series_code for d in parsed.series if d.dimension_type == "industry" and d.dimensions["industry"]["system"] == "SIC2007_section"]
        tolerance = len(parts) * 0.5 + 0.5
        for p in periods:
            if all(p in by_series[s] for s in parts):
                diff = abs(sum(by_series[s][p] for s in parts) - total[p])
                if diff > tolerance:
                    failures.append(f"sum of parts differs from the total by {diff:g} at {p} (tolerance {tolerance:g}) — columns likely misaligned")
                    break
        if parsed.dataset_code == "VACS02" and "JP9Z" in by_series and by_series["JP9Z"].get(latest, 0) > total[latest]:
            failures.append("'total services' exceeds the all-industries total")
        return failures

    def validate_set(self, parsed_list: list[ParsedRelease]) -> list[str]:
        """Independent check from ONS's own data: AP2Y is published in both files and must agree for every shared period."""
        by_ds = {p.dataset_code: {o.period_start: o.value for o in p.observations if o.series_code == TOTAL_SERIES} for p in parsed_list}
        if len(by_ds) < 2:
            return []
        (_, a), (_, b) = list(by_ds.items())[:2]
        bad = [p for p in set(a) & set(b) if a[p] != b[p]]
        return [f"AP2Y differs between VACS02 and VACS03 at {len(bad)} period(s), first {min(bad)}"] if bad else []

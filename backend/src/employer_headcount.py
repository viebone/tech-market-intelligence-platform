"""
Employer headcount — the source of truth for company size, and the ONS size band derived from it.

Replaces the platform's own four size labels (Startup / Small-Growth / Medium / Large, boundaries
at 50 / 500 / 5,000 — matching no published standard) with a **cited headcount range per company**,
from which named size bands are *derived*. PM decisions, 2026-09-25 (changes/2026-09-25-employer-
size-standard-bands.md): headcount is the source of truth (Option A); the platform's default size
label is **ONS's five bands**. Standards and rationale: EMPLOYER_SIZE_STANDARDS.md. Evidence for every
figure: research/2026-09-25-panel-headcount-research.md and research/2026-09-19-original-35-size-bands.md.
Spec: backend/specs/market-health/api.md — Business Logic — Employer size, revised.

Rules (each enforced by backend/tests/test_employer_headcount.py):
- A static, curated, git-tracked lookup keyed by `company` — same discipline as industries.py: no LLM,
  nothing invented. A company with no entry has NO band (`None`), never a guess.
- A range that sits inside one ONS band gets that band. A range that STRADDLES a boundary is
  `"ambiguous"` — unless a human recorded a `band_choice` with a reason. The PM decided on 2026-09-25 to
  choose the more probable band for the ambiguous companies rather than leave them unplaced; each
  such choice carries its reasoning in `band_choice_reason` and its entry stays `confidence="low"`.
- Every figure is stated with its basis. Most are WORLDWIDE/group headcounts, whereas ONS measures UK
  business size — a derived band for a multinational is an approximation, and any surface that uses
  one for a UK comparison must say so. Also unverified: whether ONS sizes a subsidiary as its parent group.
- Figures were gathered from web-search summaries; the filings themselves were not opened.
"""

from __future__ import annotations

from dataclasses import dataclass

# ONS Vacancy Survey employment size bands (VACS03). Code strings match the `size_band` dimension
# codes specified for trusted-statistics (backend/specs/trusted-statistics/api.md). The ONS methodology
# calls the smallest band "2 to 9" and the data file "1 - 9" (businesses with one person on the
# register are modelled, not surveyed); the file's label is used here.
ONS_SIZE_BANDS: tuple[tuple[str, str, int, int], ...] = (
    ("1-9", "1–9 employees", 1, 9),
    ("10-49", "10–49 employees", 10, 49),
    ("50-249", "50–249 employees", 50, 249),
    ("250-2499", "250–2,499 employees", 250, 2499),
    ("2500+", "2,500 or more employees", 2500, 10**9),
)
_BAND_CODES = {code for code, *_ in ONS_SIZE_BANDS}
AMBIGUOUS = "ambiguous"

_BASES = {"worldwide", "uk", "group", "parent_only"}
_CONFIDENCES = {"high", "medium", "low"}


def _band_code_for(n: int) -> str:
    for code, _label, lo, hi in ONS_SIZE_BANDS:
        if lo <= n <= hi:
            return code
    raise ValueError(f"headcount {n} is below the smallest ONS band")


def _bands_overlapping(low: int, high: int) -> list[str]:
    return [code for code, _l, lo, hi in ONS_SIZE_BANDS if low <= hi and high >= lo]


def band_label(code: str) -> str:
    """Plain-language label for an ONS band code, e.g. '250-2499' -> '250–2,499 employees'."""
    for c, label, _lo, _hi in ONS_SIZE_BANDS:
        if c == code:
            return label
    raise KeyError(code)


@dataclass(frozen=True)
class EmployerHeadcount:
    low: int                    # lowest credible figure found
    high: int                   # highest credible figure found (== low for a single figure)
    as_of: str                  # the period the figure describes (free text — sources are dated differently)
    basis: str                  # worldwide | uk | group | parent_only — what the figure actually measures
    source: str                 # short citation of where the figure came from
    confidence: str             # high (company filing) | medium (sources broadly agree) | low
    note: str = ""
    band_choice: str | None = None       # set ONLY where the range straddles a band boundary (PM decision)
    band_choice_reason: str = ""         # required with band_choice: why this band is the more probable

    def __post_init__(self) -> None:
        # Fail loudly at import if a curated entry is malformed — this is static, tested data.
        if not (isinstance(self.low, int) and isinstance(self.high, int)) or not (1 <= self.low <= self.high):
            raise ValueError(f"headcount range must be integers with 1 <= low <= high, got {self.low}..{self.high}")
        if not self.source.strip() or not self.as_of.strip():
            raise ValueError("every headcount entry needs a source and an as_of")
        if self.basis not in _BASES:
            raise ValueError(f"basis must be one of {sorted(_BASES)}, got {self.basis!r}")
        if self.confidence not in _CONFIDENCES:
            raise ValueError(f"confidence must be one of {sorted(_CONFIDENCES)}, got {self.confidence!r}")
        straddles = _band_code_for(self.low) != _band_code_for(self.high)
        if self.band_choice is not None:
            if not straddles:
                raise ValueError("band_choice is only allowed when the range straddles a band boundary")
            if self.band_choice not in _bands_overlapping(self.low, self.high):
                raise ValueError(f"band_choice {self.band_choice!r} is not a band the range {self.low}..{self.high} touches")
            if not self.band_choice_reason.strip():
                raise ValueError("band_choice needs a band_choice_reason")
            if self.confidence != "low":
                raise ValueError("an entry resolved by band_choice must stay confidence='low'")
        elif self.band_choice_reason:
            raise ValueError("band_choice_reason without band_choice")


def ons_size_band(entry: EmployerHeadcount | None) -> str | None:
    """
    The ONS size band code for a headcount entry: '1-9', '10-49', '50-249', '250-2499' or '2500+'.

    None            — no entry (no headcount researched): never guessed.
    'ambiguous'     — the range straddles a band boundary and nobody has recorded a choice.
    band_choice     — the range straddles a boundary and a human chose the more probable band.
    """
    if entry is None:
        return None
    lo_band = _band_code_for(entry.low)
    if lo_band == _band_code_for(entry.high):
        return lo_band
    return entry.band_choice if entry.band_choice is not None else AMBIGUOUS


# Companies deliberately without a headcount — listed with the reason so "no entry" is always a
# decision, never an oversight (tests fail if a tracked company is in neither place).
UNKNOWN_HEADCOUNT: dict[str, str] = {
    "lever": ("The ATS company itself, now a sub-brand of Employ Inc. No Lever-only figure found; the "
              "parent group's 850 employees (Aug 2022) is stale and covers Jobvite/JazzHR too. "
              "Left without a band rather than guessed (research/2026-09-25-panel-headcount-research.md, table A)."),
}

COMPANY_HEADCOUNT: dict[str, EmployerHeadcount] = {
    # ── Original 35 — figures already on file (research/2026-09-19-original-35-size-bands.md); `lever` is in UNKNOWN_HEADCOUNT ──
    'stripe': EmployerHeadcount(9007, 9007, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'airbnb': EmployerHeadcount(8200, 8539, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'pinterest': EmployerHeadcount(5491, 5491, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'asana': EmployerHeadcount(1922, 1922, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'reddit': EmployerHeadcount(2751, 2751, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'robinhood': EmployerHeadcount(4569, 4569, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'coinbase': EmployerHeadcount(4300, 4951, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'affirm': EmployerHeadcount(2366, 2366, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'webflow': EmployerHeadcount(1600, 1649, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'figma': EmployerHeadcount(2045, 2045, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'airtable': EmployerHeadcount(900, 1160, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'cloudflare': EmployerHeadcount(4000, 5668, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'twilio': EmployerHeadcount(5709, 5709, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'discord': EmployerHeadcount(2358, 2358, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'gitlab': EmployerHeadcount(2700, 2700, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'palantir': EmployerHeadcount(4516, 4516, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'plaid': EmployerHeadcount(1697, 1697, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'clari': EmployerHeadcount(1658, 1658, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'restream': EmployerHeadcount(94, 94, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'ramp': EmployerHeadcount(2518, 2518, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'linear': EmployerHeadcount(118, 118, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'openai': EmployerHeadcount(7800, 8000, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'notion': EmployerHeadcount(1920, 4162, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'low', band_choice='250-2499', band_choice_reason='The 2026-09-19 research already leaned on the conservative figure (1,920) because the sources conflicted (1,920-4,162); the high figure is the outlier. Most probable: 250-2,499.'),
    'modal': EmployerHeadcount(100, 231, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'replit': EmployerHeadcount(417, 417, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'mercury': EmployerHeadcount(1729, 1729, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'deel': EmployerHeadcount(11293, 11293, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'loom': EmployerHeadcount(350, 350, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'vercel': EmployerHeadcount(847, 847, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'supabase': EmployerHeadcount(240, 386, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'low', band_choice='250-2499', band_choice_reason='Range 240-386: every figure but the lowest is at or above 250. Most probable: 250-2,499.'),
    'perplexity': EmployerHeadcount(986, 1500, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'elevenlabs': EmployerHeadcount(400, 880, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'ashby': EmployerHeadcount(406, 491, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    'watershed': EmployerHeadcount(599, 599, '2026 (researched 2026-09-19)', 'worldwide', 'research/2026-09-19-original-35-size-bands.md (Revelio Labs / company-reported, cited per company there)', 'medium'),
    # ── UK employer panel — researched 2026-09-25 (research/2026-09-25-panel-headcount-research.md) ──
    'monzo': EmployerHeadcount(5275, 5429, 'Mar 2026', 'worldwide', 'Revelio Labs 5,429; Wikipedia 5,275; D&I report 5,281', 'high', note='Old bucket was Medium; the headcount is above 5,000 (the old Large).'),
    'deliveroo': EmployerHeadcount(3296, 3839, 'Dec 2024 – Dec 2025', 'worldwide', 'Corporate employees 3,296 (Dec 2025), 3,839 (Dec 2024); excludes ~135–180k self-employed riders', 'medium', note='One aggregator shows 11,381 (Jun 2026); excluded as a different basis. Reported as acquired (DoorDash) — see enterprise-group caveat.'),
    'wise': EmployerHeadcount(7585, 7585, 'Mar 2026', 'worldwide', 'Revelio Labs 7,585 (FY2026 results 25 Jun 2026)', 'medium', note='Old bucket was Medium; headcount is well above 5,000.'),
    'autotrader': EmployerHeadcount(1249, 1267, 'FY Mar 2025 – H1 FY26', 'worldwide', 'Annual report: average FTE 1,267 (FY to Mar 2025); 1,249 (six months to Sep 2025)', 'high', note='Full-time equivalents.'),
    'cleo': EmployerHeadcount(666, 666, 'Mar 2026', 'worldwide', 'Revelio Labs 666; workforce 64.7% Northern Europe', 'medium', note='Old bucket was Small/Growth (50–500); headcount is above 500.'),
    'rightmovecareers': EmployerHeadcount(861, 1100, '2024 – Dec 2025', 'worldwide', "Company results: 'just under 900' (2024); Owler 861; LeadIQ ~1.1K", 'medium', note='The 2025 annual report PDF was not opened; exact average-employee note not read.'),
    'ocadogroup': EmployerHeadcount(11941, 11942, 'FY to 30 Nov 2025', 'worldwide', 'Annual report / Revelio Labs: 11,941', 'medium', note='Old bucket was Medium; headcount is more than double 5,000. Group total — UK share not found.'),
    'starling-bank': EmployerHeadcount(4101, 4158, '2025 – 2026', 'worldwide', 'Wikipedia 4,158 (2026); Revelio Labs 4,102; 4,101 (2025)', 'medium'),
    'cuvva': EmployerHeadcount(96, 100, 'May – Jul 2026', 'worldwide', 'Aggregators: 96 (31 May 2026); ~98; ~100', 'medium'),
    'zopa': EmployerHeadcount(900, 1000, '2026', 'worldwide', "PitchBook ~1,000; company press page '900+' (older)", 'medium', note='LinkedIn range shown as 1,001–5,000 by one source — outside every other figure.'),
    'trainline': EmployerHeadcount(990, 990, '28 Feb 2026', 'worldwide', 'Annual report: 990 (unchanged on prior year)', 'high'),
    'quantexa': EmployerHeadcount(872, 951, 'Dec 2025 – Jun 2026', 'worldwide', 'Aggregators: 951 (Dec 2025), ~897 (May 2026), 893 (Jun 2026), ~872', 'medium'),
    'faculty': EmployerHeadcount(100, 400, '2026', 'worldwide', 'PitchBook 400; another 279; Owler 100–250', 'low', note='Accenture reported to have acquired Faculty in Jan 2026 — see enterprise-group caveat. Straddles the 250 boundary.', band_choice='250-2499', band_choice_reason='Two of the three figures (279 and 400) are above 250; the third is a coarse 100-250 bucket. Most probable: 250-2,499, but close to the boundary, and the company was reported acquired by Accenture in Jan 2026.'),
    'motorway': EmployerHeadcount(403, 450, '2024 – 2026', 'worldwide', 'Average employees 448 (2024), 403 (2025); ~428; 450+ (Wikipedia)', 'medium'),
    'marshmallow': EmployerHeadcount(665, 700, 'Apr 2025 – Jun 2026', 'worldwide', 'Aggregators: 700 (Apr 2025, London and Budapest); 665 (30 Jun 2026)', 'medium', note='UK share is below the total (Budapest office); likely still above 250.'),
    'multiverse': EmployerHeadcount(813, 1269, 'Jan – Jun 2026', 'worldwide', '813 (Jan 2026); 1,269 (30 Jun 2026); rapid hiring', 'medium'),
    'attio': EmployerHeadcount(115, 177, '2026', 'worldwide', 'PitchBook 115; Tracxn 177 (30 Apr 2026); Gartner range 51–200', 'medium'),
    'griffin': EmployerHeadcount(139, 145, 'Jan – Mar 2026', 'worldwide', 'Aggregators: 139 (5 Jan 2026); ~145 (Mar 2026)', 'medium'),
    'sylvera': EmployerHeadcount(150, 150, '2026', 'worldwide', 'PitchBook: 150 (single source)', 'low'),
    'beamery': EmployerHeadcount(200, 227, '2026', 'worldwide', 'Wikipedia ~200; another source 227 (early 2026)', 'medium', note='227 is 23 below the 250 boundary.'),
    'incident': EmployerHeadcount(82, 208, 'Dec 2025 – Jul 2026', 'worldwide', 'Tracxn 208 (31 Jul 2026); TipRanks 200; PitchBook 146; LeadIQ ~140; Latka 82', 'medium', note='Wide spread; every figure is inside 50–249.'),
    # ── US + EU panel, batch 1 — researched 2026-09-25 ──
    'duolingo': EmployerHeadcount(900, 1001, 'Dec 2025 – Mar 2026', 'worldwide', 'Company-reported 900 (31 Dec 2025, via search summary); Revelio Labs 1,001 (Mar 2026)', 'medium', note="Two other aggregators show 2,948–3,100; excluded as inconsistent with the company's own figure. If they were right the band would be 2,500+."),
    'gusto': EmployerHeadcount(3700, 3979, 'Mar 2026', 'worldwide', 'Revelio Labs 3,979; another aggregator ~3.7K', 'medium', note='One aggregator shows 7,834; excluded (unexplained, ~2x every other source).'),
    'carta': EmployerHeadcount(2000, 2100, 'Apr 2026', 'worldwide', 'Aggregators only (~2K; ~2.1K)', 'low', note='Close to the 2,500 boundary but below it in every figure seen.'),
    'khanacademy': EmployerHeadcount(258, 2365, 'unknown / Jul 2026', 'worldwide', 'Form 990-derived 258 (year not stated, via aggregator) vs directory sites 2,315–2,365', 'low', note='Nonprofit; the two figures differ ~9x. The directory counts are very likely inflated (volunteers/contractors/ex-staff), but 258 sits only 8 above the 250 boundary and its year is unknown. Needs the latest Form 990 PDF (Part I line 5).'),
    'doximity': EmployerHeadcount(880, 880, '31 Mar 2026', 'worldwide', '10-K FY2026 (SEC): 880 full-time equivalent employees', 'high', note='Full-time equivalents, not headcount.'),
    'glossier': EmployerHeadcount(402, 679, 'Dec 2025 – Jul 2026', 'worldwide', 'Aggregators: 679 (Dec 2025), ~471–482 (Jul 2026), 402; layoffs of >50 in Feb 2026 (BoF)', 'medium', note='Wide spread but every figure is inside 250–2,499.'),
    'peloton': EmployerHeadcount(2262, 2262, '30 Jun 2026', 'worldwide', '10-K FY2026 (SEC): 1,736 US + 526 international', 'high', note='238 below the 2,500 boundary. US figure is total individuals employed; 1,673 of them full-time.'),
    'n26': EmployerHeadcount(1600, 2399, '2026', 'worldwide', 'Wikipedia ~1,600; PitchBook 2,399; Owler 1,000–5,000', 'low', note='High end is close to 2,500.'),
    'getyourguide': EmployerHeadcount(1300, 1502, 'Feb – Mar 2026', 'worldwide', 'Aggregators: 1.3K, 1.4K (1,410 at 28 Feb 2026), 1,502', 'medium'),
    'contentful': EmployerHeadcount(956, 1045, 'Dec 2025 – Jul 2026', 'worldwide', 'Aggregators: 956 (Dec 2025) to 1,045 (31 Jul 2026)', 'medium', note='Salesforce announced an acquisition in June 2026 — see the enterprise-group caveat.'),
    'trustpilot': EmployerHeadcount(1108, 1108, '31 Dec 2025', 'worldwide', 'Trustpilot Group plc Annual Report 2025: 1,108 (+120 on prior year)', 'high'),
    'typeform': EmployerHeadcount(728, 886, 'Mar – Jul 2026', 'worldwide', 'Revelio Labs 886; another source ~728', 'medium'),
    'algolia': EmployerHeadcount(862, 936, '2025 – Aug 2026', 'worldwide', 'Aggregators: 862 (2025), ~881 (Jul 2026), 936 (Aug 2026)', 'medium'),
    'gymshark': EmployerHeadcount(900, 2554, 'Dec 2025 – Jul 2026', 'worldwide', "Revelio Labs 1,980 (Dec 2025); Tracxn/RocketReach 2,552–2,554 (Jul 2026); another source 'over 900'", 'low', note="Straddles the 2,500 boundary. UK-headquartered, so the Companies House accounts ('average monthly number of employees') would settle it — paywalled on the sites tried; a human should open the filing.", band_choice='250-2499', band_choice_reason="Revelio Labs' 1,980 (Dec 2025) is the most credible of the three figures; the 2,552-2,554 aggregator figures sit only just above 2,500, and across this panel aggregator 'latest count' figures run 2-3x above filings and Revelio (Duolingo 2,948 vs 900-1,001; Gusto 7,834 vs 3,979). Most probable: 250-2,499. Verify against the Companies House accounts."),
    'spotify': EmployerHeadcount(7287, 7323, 'FY2025', 'worldwide', '20-F FY2025 (SEC): 7,323 full-time employees at year end; 7,287 average', 'high', note='Worldwide; UK share not needed for a UK cross-check of a Swedish company.'),
    'moonpig': EmployerHeadcount(763, 763, 'FY to 30 Apr 2026', 'worldwide', 'Moonpig Group plc annual report FY2026: 763; ~93% of employees in the UK', 'high', note='≈710 in the UK.'),
    'substack': EmployerHeadcount(1634, 3513, 'Mar – Jul 2026', 'worldwide', 'Revelio Labs 1,634 (Mar 2026); other aggregators 2.6K–3.5K', 'low', note='Private company; sources disagree by 2x and straddle 2,500. No primary source exists to settle it.', band_choice='250-2499', band_choice_reason="Revelio Labs' 1,634 (Mar 2026) is the most credible; the 2.6K-3.5K figures come from aggregators whose latest-count figures ran 2-3x above filings and Revelio elsewhere in this panel (Duolingo, Gusto). Private company, no primary source. Most probable: 250-2,499."),
    'vanta': EmployerHeadcount(1635, 1979, 'Mar 2026', 'worldwide', 'Revelio Labs 1,635; PitchBook 1,979; another 1,766', 'medium'),
    'lemonade': EmployerHeadcount(1282, 1282, '31 Dec 2025', 'worldwide', '10-K FY2025 (SEC): 1,282 total; 810 in the US, rest mainly Israel and the Netherlands', 'high'),
    'pleo': EmployerHeadcount(737, 1000, 'Mar – Aug 2026', 'worldwide', 'Revelio Labs 737 (Mar 2026); other aggregators 933–1K', 'medium'),
    'mollie': EmployerHeadcount(1100, 1170, 'Feb – Jul 2026', 'worldwide', 'Aggregators: ~1.1K; 1,170 (31 Jul 2026); Amsterdam hosts about half', 'medium'),
    'deepl': EmployerHeadcount(750, 1547, 'May 2026', 'worldwide', "Reported 'slightly more than 1,000' before announcing ~250 cuts (25%) in May 2026; Tracxn 1,547", 'medium', note='Range brackets the announced cut; every value is inside 250–2,499.'),
    'paddle': EmployerHeadcount(397, 425, '2026', 'worldwide', 'Aggregators: ~397; 403; 425 (Aug 2026)', 'medium'),
    'synthesia': EmployerHeadcount(550, 700, '2025 – 2026', 'worldwide', 'Wikipedia 550 (2025); Forbes 600 (30 Jan 2026); ~700 (2026); offices also in Austin, Berlin, Paris, Zurich', 'medium', note='UK share unknown.'),
    'thought-machine': EmployerHeadcount(497, 531, 'End 2025 – May 2026', 'worldwide', 'Revelio Labs 531 (Mar 2026); 497 full-time at end 2025; PitchBook 529', 'medium'),
    'zego': EmployerHeadcount(303, 365, 'May – Jul 2026', 'worldwide', 'Aggregator 365 (31 May 2026); a 17% reduction announced Jul 2026 (~303 after)', 'low', note='After the cut the figure is only ~50 above the 250 boundary.'),
}


def size_band_for(company: str | None) -> str | None:
    """
    ONS size band code for a tracked company, derived from COMPANY_HEADCOUNT — or None if the company is
    unknown / has no headcount, or 'ambiguous' if its range straddles a boundary with no recorded choice.
    Same signature and None-means-not-tagged contract the old industries.size_band_for() had, so
    raw_postings.insert_new_postings() is unchanged.
    """
    if not company:
        return None
    return ons_size_band(COMPANY_HEADCOUNT.get(company))

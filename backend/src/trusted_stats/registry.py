"""
The trust bar, in code — one entry per trusted publisher.

A publisher only enters this category by passing the trust bar (backend/specs/trusted-statistics/api.md
— "The trust bar"): a named publisher, published methodology, a citable URL, reuse terms READ OFF THE
PUBLISHER'S OWN PAGE and permitting our use, a machine-readable route (a file or API — never HTML
scraping; that goes through scraping/ and /polite-scraping-review), and figures with a defined unit and
period. An adapter with no entry here — or no matching source_licences.SOURCE_LICENCES entry — is a hard
error (base.ingest_adapter, tests/test_trusted_stats.py), the same "refuse rather than guess" rule
source_licences.py applies.

`trust_bar_reviewed_by` records who signed the bar off, honestly: for ONS that is the PM's go on
2026-09-24 plus the evidence file, not a claim of independent review.
"""

from __future__ import annotations

from dataclasses import dataclass

PUBLISHER_TYPES = (
    "national_statistics_office",
    "government_department",
    "intergovernmental_body",
    "research_institution",
    "recognised_company_or_survey",
)


@dataclass(frozen=True)
class TrustedPublisher:
    source: str                       # key in SOURCE_LICENCES too
    publisher: str
    publisher_type: str
    programme: str
    datasets: tuple[str, ...]
    methodology_url: str
    source_page_url: str
    min_check_interval_hours: float   # cadence, ENFORCED in base.ingest_adapter before any request
    trust_bar_reviewed_on: str
    trust_bar_reviewed_by: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.publisher_type not in PUBLISHER_TYPES:
            raise ValueError(f"publisher_type must be one of {PUBLISHER_TYPES}")
        for f in ("publisher", "programme", "methodology_url", "source_page_url", "trust_bar_reviewed_on", "trust_bar_reviewed_by"):
            if not getattr(self, f).strip():
                raise ValueError(f"TrustedPublisher.{f} is required")
        if not self.datasets:
            raise ValueError("a publisher needs at least one dataset")
        if self.min_check_interval_hours <= 0:
            raise ValueError("min_check_interval_hours must be positive")


TRUSTED_PUBLISHERS: dict[str, TrustedPublisher] = {
    "ons_vacancy_survey": TrustedPublisher(
        source="ons_vacancy_survey",
        publisher="Office for National Statistics",
        publisher_type="national_statistics_office",
        programme="Vacancy Survey",
        datasets=("VACS02", "VACS03"),
        methodology_url="https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/vacancysurveyqmi",
        source_page_url="https://www.ons.gov.uk/surveys/informationforbusinesses/businesssurveys/vacancysurvey",
        min_check_interval_hours=24,
        trust_bar_reviewed_on="2026-09-24",
        trust_bar_reviewed_by="PM go 2026-09-24 (chat); evidence: research/2026-09-24-ons-licence-and-access-confirmation.md",
        notes=("Monthly release. VACS02 vacancies by industry (SIC 2007), VACS03 by size of business; X06 and the VACS02 "
               "'job openings rate' sheet are deferred until inspected. Survey covers Great Britain, weighted to the UK."),
    ),
}

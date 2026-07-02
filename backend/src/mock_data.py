"""
In-memory mock data for v1.

Coverage:
  Role families : UX Design, Product Management, Software Engineering
  Locations     : London, New York, Remote
  Seniority     : Mid, Senior
  Trend period  : 6 months of posting counts (2026-01 through 2026-06)

Internal consistency rules applied:
  - "Cautious"     → demand trend declining or stable
  - "Healthy"      → demand trend rising
  - "Contracting"  → demand trend declining
"""

from datetime import date
from models import (
    DemandSignal,
    CompensationSignal,
    LayoffSignal,
    MarketHealthSignal,
    OpeningDataPoint,
    PostingPeriod,
    SearchImplication,
)

AS_OF = date(2026, 6, 1)

# ---------------------------------------------------------------------------
# Market Health Signals
# One signal per (role_family, seniority, location) combination.
# Key: (role_family.lower(), seniority.lower(), location.lower())
# "all" key used for the aggregate / unfiltered view.
# ---------------------------------------------------------------------------

MARKET_HEALTH_SIGNALS: dict[tuple[str, str, str], MarketHealthSignal] = {
    # Aggregate (no filters)
    ("all", "all", "all"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Demand across tech roles is stable but layoff activity has increased at large tech companies over the last quarter.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="Aggregated from job board postings and public layoff announcements",
    ),
    # UX Design — Senior
    ("ux design", "senior", "london"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Senior UX roles in London are posting at a slower rate than six months ago, while compensation has held steady.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("ux design", "senior", "new york"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Senior UX demand in New York has softened following rounds of layoffs at fintech and media companies.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="LinkedIn job postings, Layoffs.fyi",
    ),
    ("ux design", "senior", "remote"): MarketHealthSignal(
        verdict="Healthy",
        explanation="Remote senior UX roles are rising steadily, driven by product-led growth companies expanding design teams.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Remote OK",
    ),
    # UX Design — Mid
    ("ux design", "mid", "london"): MarketHealthSignal(
        verdict="Healthy",
        explanation="Mid-level UX opportunities in London are growing as agencies and scale-ups rebuild design capacity.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("ux design", "mid", "new york"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Mid-level UX postings in New York are flat — demand exists but competition is high due to recent layoffs flooding the candidate pool.",
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    ("ux design", "mid", "remote"): MarketHealthSignal(
        verdict="Healthy",
        explanation="Remote mid-level UX roles have increased steadily over the past quarter as companies embrace distributed teams.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Remote OK",
    ),
    # Product Management — Senior
    ("product management", "senior", "london"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Senior PM roles in London have contracted slightly, with hiring concentrated in fintech and healthtech.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("product management", "senior", "new york"): MarketHealthSignal(
        verdict="Healthy",
        explanation="New York senior PM demand is rising, led by fintech and SaaS companies accelerating AI product development.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("product management", "senior", "remote"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Remote senior PM roles are available but competition is fierce — response rates have declined over the last two months.",
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Product Management — Mid
    ("product management", "mid", "london"): MarketHealthSignal(
        verdict="Healthy",
        explanation="Mid-level PM roles in London are growing, particularly in B2B SaaS and e-commerce.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("product management", "mid", "new york"): MarketHealthSignal(
        verdict="Healthy",
        explanation="Mid-level PM demand in New York is robust, with AI-adjacent roles driving most of the growth.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("product management", "mid", "remote"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Remote mid-level PM openings are stable but candidate supply is high, making it a competitive market.",
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Senior
    ("software engineering", "senior", "london"): MarketHealthSignal(
        verdict="Contracting",
        explanation="Senior engineering roles in London have declined sharply over the past quarter following layoffs at several large tech firms.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="LinkedIn job postings, Layoffs.fyi",
    ),
    ("software engineering", "senior", "new york"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Senior engineering demand in New York is holding but below last year's levels, with AI-adjacent roles as the exception.",
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("software engineering", "senior", "remote"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Remote senior engineering roles are stable but many companies have rescinded remote-first policies, reducing the pool.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Mid
    ("software engineering", "mid", "london"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Mid-level engineering in London is stable but slow — most openings are replacement hires rather than team growth.",
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("software engineering", "mid", "new york"): MarketHealthSignal(
        verdict="Healthy",
        explanation="Mid-level engineering demand in New York is rising, driven by AI product teams and financial services firms.",
        trend_direction="improving",
        as_of=AS_OF,
        source="LinkedIn job postings, Glassdoor salary reports",
    ),
    ("software engineering", "mid", "remote"): MarketHealthSignal(
        verdict="Cautious",
        explanation="Remote mid-level engineering roles are available but compensation packages have compressed compared to 2025 peaks.",
        trend_direction="worsening",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
}

# ---------------------------------------------------------------------------
# Search Implications — keyed by verdict
# ---------------------------------------------------------------------------

SEARCH_IMPLICATIONS: dict[str, SearchImplication] = {
    "Healthy": SearchImplication(
        text="The market is active and receptive. Apply now — competition exists but opportunities are genuinely open. Set salary targets at the upper half of the range.",
        signal_verdict="Healthy",
    ),
    "Cautious": SearchImplication(
        text="The market is soft but not closed. Target smaller companies, scale-ups, and contract roles to increase your hit rate. Expect longer timelines and more rigorous screening.",
        signal_verdict="Cautious",
    ),
    "Contracting": SearchImplication(
        text="The market is tight. Broaden your search by role type, seniority, or geography. Contract and consulting work may be the most reliable entry point right now.",
        signal_verdict="Contracting",
    ),
}

# ---------------------------------------------------------------------------
# Demand Signals (6-month posting trend)
# ---------------------------------------------------------------------------

DEMAND_SIGNALS: list[DemandSignal] = [
    # UX Design — Senior — London (declining → Cautious)
    DemandSignal(
        role_family="UX Design",
        seniority="Senior",
        location="London",
        posting_trend=[
            PostingPeriod("2026-01", 340),
            PostingPeriod("2026-02", 320),
            PostingPeriod("2026-03", 305),
            PostingPeriod("2026-04", 290),
            PostingPeriod("2026-05", 275),
            PostingPeriod("2026-06", 260),
        ],
        trend_direction="declining",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # UX Design — Senior — New York (declining → Cautious)
    DemandSignal(
        role_family="UX Design",
        seniority="Senior",
        location="New York",
        posting_trend=[
            PostingPeriod("2026-01", 480),
            PostingPeriod("2026-02", 455),
            PostingPeriod("2026-03", 440),
            PostingPeriod("2026-04", 420),
            PostingPeriod("2026-05", 400),
            PostingPeriod("2026-06", 385),
        ],
        trend_direction="declining",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # UX Design — Senior — Remote (rising → Healthy)
    DemandSignal(
        role_family="UX Design",
        seniority="Senior",
        location="Remote",
        posting_trend=[
            PostingPeriod("2026-01", 210),
            PostingPeriod("2026-02", 230),
            PostingPeriod("2026-03", 255),
            PostingPeriod("2026-04", 280),
            PostingPeriod("2026-05", 305),
            PostingPeriod("2026-06", 330),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings, Remote OK",
    ),
    # UX Design — Mid — London (rising → Healthy)
    DemandSignal(
        role_family="UX Design",
        seniority="Mid",
        location="London",
        posting_trend=[
            PostingPeriod("2026-01", 190),
            PostingPeriod("2026-02", 205),
            PostingPeriod("2026-03", 218),
            PostingPeriod("2026-04", 235),
            PostingPeriod("2026-05", 250),
            PostingPeriod("2026-06", 268),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # UX Design — Mid — New York (stable → Cautious)
    DemandSignal(
        role_family="UX Design",
        seniority="Mid",
        location="New York",
        posting_trend=[
            PostingPeriod("2026-01", 310),
            PostingPeriod("2026-02", 315),
            PostingPeriod("2026-03", 308),
            PostingPeriod("2026-04", 312),
            PostingPeriod("2026-05", 305),
            PostingPeriod("2026-06", 310),
        ],
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # UX Design — Mid — Remote (rising → Healthy)
    DemandSignal(
        role_family="UX Design",
        seniority="Mid",
        location="Remote",
        posting_trend=[
            PostingPeriod("2026-01", 145),
            PostingPeriod("2026-02", 162),
            PostingPeriod("2026-03", 178),
            PostingPeriod("2026-04", 195),
            PostingPeriod("2026-05", 212),
            PostingPeriod("2026-06", 230),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings, Remote OK",
    ),
    # Product Management — Senior — London (declining → Cautious)
    DemandSignal(
        role_family="Product Management",
        seniority="Senior",
        location="London",
        posting_trend=[
            PostingPeriod("2026-01", 270),
            PostingPeriod("2026-02", 260),
            PostingPeriod("2026-03", 248),
            PostingPeriod("2026-04", 240),
            PostingPeriod("2026-05", 232),
            PostingPeriod("2026-06", 225),
        ],
        trend_direction="declining",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Product Management — Senior — New York (rising → Healthy)
    DemandSignal(
        role_family="Product Management",
        seniority="Senior",
        location="New York",
        posting_trend=[
            PostingPeriod("2026-01", 380),
            PostingPeriod("2026-02", 400),
            PostingPeriod("2026-03", 425),
            PostingPeriod("2026-04", 450),
            PostingPeriod("2026-05", 475),
            PostingPeriod("2026-06", 500),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Product Management — Senior — Remote (stable → Cautious)
    DemandSignal(
        role_family="Product Management",
        seniority="Senior",
        location="Remote",
        posting_trend=[
            PostingPeriod("2026-01", 180),
            PostingPeriod("2026-02", 185),
            PostingPeriod("2026-03", 178),
            PostingPeriod("2026-04", 182),
            PostingPeriod("2026-05", 180),
            PostingPeriod("2026-06", 183),
        ],
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Product Management — Mid — London (rising → Healthy)
    DemandSignal(
        role_family="Product Management",
        seniority="Mid",
        location="London",
        posting_trend=[
            PostingPeriod("2026-01", 155),
            PostingPeriod("2026-02", 168),
            PostingPeriod("2026-03", 182),
            PostingPeriod("2026-04", 197),
            PostingPeriod("2026-05", 213),
            PostingPeriod("2026-06", 228),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Product Management — Mid — New York (rising → Healthy)
    DemandSignal(
        role_family="Product Management",
        seniority="Mid",
        location="New York",
        posting_trend=[
            PostingPeriod("2026-01", 290),
            PostingPeriod("2026-02", 310),
            PostingPeriod("2026-03", 335),
            PostingPeriod("2026-04", 355),
            PostingPeriod("2026-05", 375),
            PostingPeriod("2026-06", 400),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Product Management — Mid — Remote (stable → Cautious)
    DemandSignal(
        role_family="Product Management",
        seniority="Mid",
        location="Remote",
        posting_trend=[
            PostingPeriod("2026-01", 140),
            PostingPeriod("2026-02", 145),
            PostingPeriod("2026-03", 138),
            PostingPeriod("2026-04", 143),
            PostingPeriod("2026-05", 141),
            PostingPeriod("2026-06", 144),
        ],
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Senior — London (declining → Contracting)
    DemandSignal(
        role_family="Software Engineering",
        seniority="Senior",
        location="London",
        posting_trend=[
            PostingPeriod("2026-01", 820),
            PostingPeriod("2026-02", 750),
            PostingPeriod("2026-03", 680),
            PostingPeriod("2026-04", 620),
            PostingPeriod("2026-05", 560),
            PostingPeriod("2026-06", 510),
        ],
        trend_direction="declining",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Senior — New York (stable → Cautious)
    DemandSignal(
        role_family="Software Engineering",
        seniority="Senior",
        location="New York",
        posting_trend=[
            PostingPeriod("2026-01", 1100),
            PostingPeriod("2026-02", 1085),
            PostingPeriod("2026-03", 1095),
            PostingPeriod("2026-04", 1080),
            PostingPeriod("2026-05", 1090),
            PostingPeriod("2026-06", 1075),
        ],
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Senior — Remote (declining → Cautious)
    DemandSignal(
        role_family="Software Engineering",
        seniority="Senior",
        location="Remote",
        posting_trend=[
            PostingPeriod("2026-01", 560),
            PostingPeriod("2026-02", 540),
            PostingPeriod("2026-03", 525),
            PostingPeriod("2026-04", 505),
            PostingPeriod("2026-05", 490),
            PostingPeriod("2026-06", 475),
        ],
        trend_direction="declining",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Mid — London (stable → Cautious)
    DemandSignal(
        role_family="Software Engineering",
        seniority="Mid",
        location="London",
        posting_trend=[
            PostingPeriod("2026-01", 620),
            PostingPeriod("2026-02", 615),
            PostingPeriod("2026-03", 625),
            PostingPeriod("2026-04", 618),
            PostingPeriod("2026-05", 622),
            PostingPeriod("2026-06", 615),
        ],
        trend_direction="stable",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Mid — New York (rising → Healthy)
    DemandSignal(
        role_family="Software Engineering",
        seniority="Mid",
        location="New York",
        posting_trend=[
            PostingPeriod("2026-01", 780),
            PostingPeriod("2026-02", 810),
            PostingPeriod("2026-03", 845),
            PostingPeriod("2026-04", 880),
            PostingPeriod("2026-05", 915),
            PostingPeriod("2026-06", 950),
        ],
        trend_direction="rising",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
    # Software Engineering — Mid — Remote (declining → Cautious)
    DemandSignal(
        role_family="Software Engineering",
        seniority="Mid",
        location="Remote",
        posting_trend=[
            PostingPeriod("2026-01", 440),
            PostingPeriod("2026-02", 425),
            PostingPeriod("2026-03", 415),
            PostingPeriod("2026-04", 400),
            PostingPeriod("2026-05", 388),
            PostingPeriod("2026-06", 375),
        ],
        trend_direction="declining",
        as_of=AS_OF,
        source="LinkedIn job postings",
    ),
]

# ---------------------------------------------------------------------------
# Compensation Signals
# ---------------------------------------------------------------------------

COMPENSATION_SIGNALS: list[CompensationSignal] = [
    # UX Design — Senior — London  (GBP)
    CompensationSignal(
        role_family="UX Design",
        seniority="Senior",
        location="London",
        salary_min=70_000,
        salary_max=110_000,
        salary_median=88_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # UX Design — Senior — New York  (USD)
    CompensationSignal(
        role_family="UX Design",
        seniority="Senior",
        location="New York",
        salary_min=110_000,
        salary_max=175_000,
        salary_median=145_000,
        trend_direction="declining",
        as_of=AS_OF,
        source="Glassdoor salary reports, Levels.fyi",
    ),
    # UX Design — Senior — Remote  (USD)
    CompensationSignal(
        role_family="UX Design",
        seniority="Senior",
        location="Remote",
        salary_min=90_000,
        salary_max=155_000,
        salary_median=125_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports, Remote OK",
    ),
    # UX Design — Mid — London  (GBP)
    CompensationSignal(
        role_family="UX Design",
        seniority="Mid",
        location="London",
        salary_min=45_000,
        salary_max=72_000,
        salary_median=58_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # UX Design — Mid — New York  (USD)
    CompensationSignal(
        role_family="UX Design",
        seniority="Mid",
        location="New York",
        salary_min=75_000,
        salary_max=120_000,
        salary_median=98_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # UX Design — Mid — Remote  (USD)
    CompensationSignal(
        role_family="UX Design",
        seniority="Mid",
        location="Remote",
        salary_min=65_000,
        salary_max=110_000,
        salary_median=88_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports, Remote OK",
    ),
    # Product Management — Senior — London  (GBP)
    CompensationSignal(
        role_family="Product Management",
        seniority="Senior",
        location="London",
        salary_min=80_000,
        salary_max=130_000,
        salary_median=105_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Product Management — Senior — New York  (USD)
    CompensationSignal(
        role_family="Product Management",
        seniority="Senior",
        location="New York",
        salary_min=140_000,
        salary_max=230_000,
        salary_median=185_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports, Levels.fyi",
    ),
    # Product Management — Senior — Remote  (USD)
    CompensationSignal(
        role_family="Product Management",
        seniority="Senior",
        location="Remote",
        salary_min=110_000,
        salary_max=185_000,
        salary_median=148_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Product Management — Mid — London  (GBP)
    CompensationSignal(
        role_family="Product Management",
        seniority="Mid",
        location="London",
        salary_min=55_000,
        salary_max=85_000,
        salary_median=70_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Product Management — Mid — New York  (USD)
    CompensationSignal(
        role_family="Product Management",
        seniority="Mid",
        location="New York",
        salary_min=95_000,
        salary_max=155_000,
        salary_median=125_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Product Management — Mid — Remote  (USD)
    CompensationSignal(
        role_family="Product Management",
        seniority="Mid",
        location="Remote",
        salary_min=80_000,
        salary_max=135_000,
        salary_median=108_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Software Engineering — Senior — London  (GBP)
    CompensationSignal(
        role_family="Software Engineering",
        seniority="Senior",
        location="London",
        salary_min=80_000,
        salary_max=140_000,
        salary_median=112_000,
        trend_direction="declining",
        as_of=AS_OF,
        source="Glassdoor salary reports, Levels.fyi",
    ),
    # Software Engineering — Senior — New York  (USD)
    CompensationSignal(
        role_family="Software Engineering",
        seniority="Senior",
        location="New York",
        salary_min=160_000,
        salary_max=280_000,
        salary_median=220_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports, Levels.fyi",
    ),
    # Software Engineering — Senior — Remote  (USD)
    CompensationSignal(
        role_family="Software Engineering",
        seniority="Senior",
        location="Remote",
        salary_min=130_000,
        salary_max=220_000,
        salary_median=175_000,
        trend_direction="declining",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Software Engineering — Mid — London  (GBP)
    CompensationSignal(
        role_family="Software Engineering",
        seniority="Mid",
        location="London",
        salary_min=55_000,
        salary_max=90_000,
        salary_median=72_000,
        trend_direction="stable",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
    # Software Engineering — Mid — New York  (USD)
    CompensationSignal(
        role_family="Software Engineering",
        seniority="Mid",
        location="New York",
        salary_min=110_000,
        salary_max=185_000,
        salary_median=148_000,
        trend_direction="rising",
        as_of=AS_OF,
        source="Glassdoor salary reports, Levels.fyi",
    ),
    # Software Engineering — Mid — Remote  (USD)
    CompensationSignal(
        role_family="Software Engineering",
        seniority="Mid",
        location="Remote",
        salary_min=90_000,
        salary_max=155_000,
        salary_median=122_000,
        trend_direction="declining",
        as_of=AS_OF,
        source="Glassdoor salary reports",
    ),
]

# ---------------------------------------------------------------------------
# Layoff Signals
# ---------------------------------------------------------------------------

LAYOFF_SIGNALS: list[LayoffSignal] = [
    LayoffSignal(
        company="StreamCo",
        sector="Media & Entertainment",
        event_date=date(2026, 5, 20),
        headcount_affected=350,
        source="Layoffs.fyi",
    ),
    LayoffSignal(
        company="NovaPay",
        sector="FinTech",
        event_date=date(2026, 5, 8),
        headcount_affected=200,
        source="Layoffs.fyi",
    ),
    LayoffSignal(
        company="ClearCart",
        sector="E-Commerce",
        event_date=date(2026, 4, 15),
        headcount_affected=120,
        source="TechCrunch, Layoffs.fyi",
    ),
    LayoffSignal(
        company="AxisHealth",
        sector="HealthTech",
        event_date=date(2026, 4, 3),
        headcount_affected=None,   # unconfirmed
        source="Bloomberg (unconfirmed)",
    ),
    LayoffSignal(
        company="GridCloud",
        sector="Enterprise SaaS",
        event_date=date(2026, 3, 22),
        headcount_affected=500,
        source="Layoffs.fyi, Reuters",
    ),
    LayoffSignal(
        company="VaultBank",
        sector="FinTech",
        event_date=date(2026, 3, 10),
        headcount_affected=85,
        source="Layoffs.fyi",
    ),
    LayoffSignal(
        company="Acme Corp",
        sector="Enterprise SaaS",
        event_date=date(2026, 2, 28),
        headcount_affected=200,
        source="Layoffs.fyi",
    ),
    LayoffSignal(
        company="ShipFast",
        sector="Logistics Tech",
        event_date=date(2026, 2, 14),
        headcount_affected=75,
        source="Layoffs.fyi",
    ),
    LayoffSignal(
        company="PixelStudio",
        sector="Media & Entertainment",
        event_date=date(2026, 1, 30),
        headcount_affected=None,   # unconfirmed
        source="LinkedIn (unconfirmed)",
    ),
    LayoffSignal(
        company="DataLens",
        sector="Analytics",
        event_date=date(2026, 1, 15),
        headcount_affected=140,
        source="Layoffs.fyi",
    ),
]

# ---------------------------------------------------------------------------
# Helpers — period slicing for posting_trend
# ---------------------------------------------------------------------------

_PERIOD_MONTHS = {
    "3m": 3,
    "6m": 6,
    "12m": 12,
}

ALL_PERIODS = sorted(
    {pt.period for ds in DEMAND_SIGNALS for pt in ds.posting_trend}
)


def slice_posting_trend(
    posting_trend: list[PostingPeriod], period: str
) -> list[PostingPeriod]:
    """Return only the last N months of a posting trend list."""
    months = _PERIOD_MONTHS.get(period, 6)
    return posting_trend[-months:]


# ---------------------------------------------------------------------------
# Job Opening Trends — monthly totals per role category
#
# Covers Jan 2019 – Jun 2026 (all_time).
# Sliced by the endpoint for this_year and past_5_years ranges.
#
# Values are aggregated across all locations and seniority levels.
# The Jan–Jun 2026 figures match the sum of existing DEMAND_SIGNALS.
# ---------------------------------------------------------------------------

def _lerp(a: float, b: float, t: float) -> int:
    return round(a + (b - a) * t)


def _month_index(year: int, month: int) -> int:
    """Months since Jan 2019 (0-based)."""
    return (year - 2019) * 12 + (month - 1)


def _build_opening_trends() -> list[OpeningDataPoint]:
    # Key milestones: (year, month, designer, product_manager, engineer)
    milestones = [
        (2019, 1,  2200, 1800, 5500),
        (2020, 1,  2360, 1930, 5900),
        (2020, 4,  1480, 1180, 3800),  # pandemic crash
        (2020, 10, 2250, 1820, 5700),  # rapid recovery
        (2021, 4,  2700, 2250, 7100),
        (2022, 6,  3300, 2900, 9000),  # boom peak
        (2022, 11, 2700, 2350, 7300),  # correction begins
        (2023, 6,  1750, 1560, 4650),  # tech winter trough
        (2024, 1,  1840, 1650, 4600),
        (2025, 1,  1960, 1740, 4620),
        (2025, 9,  1810, 1560, 4420),  # slight end-of-year dip
        (2026, 1,  1675, 1415, 4320),  # matches sum of existing DEMAND_SIGNALS
        (2026, 2,  1687, 1468, 4225),
        (2026, 3,  1704, 1506, 4185),
        (2026, 4,  1732, 1567, 4103),
        (2026, 5,  1747, 1616, 4065),
        (2026, 6,  1783, 1680, 4000),
    ]

    # Convert to (index, d, pm, eng) for interpolation
    keyed = [
        (_month_index(y, m), d, pm, e)
        for y, m, d, pm, e in milestones
    ]

    # Build a result dict for every month index from 0 to _month_index(2026, 6)
    max_idx = _month_index(2026, 6)
    result: dict[int, tuple[int, int, int]] = {}

    for i in range(len(keyed) - 1):
        i0, d0, pm0, e0 = keyed[i]
        i1, d1, pm1, e1 = keyed[i + 1]
        for idx in range(i0, i1 + 1):
            t = (idx - i0) / (i1 - i0) if i1 > i0 else 0.0
            result[idx] = (_lerp(d0, d1, t), _lerp(pm0, pm1, t), _lerp(e0, e1, t))

    # Ensure the last milestone is set exactly
    last_idx, ld, lpm, le = keyed[-1]
    result[last_idx] = (ld, lpm, le)

    points = []
    for idx in range(0, max_idx + 1):
        year = 2019 + idx // 12
        month = idx % 12 + 1
        d, pm, e = result.get(idx, (0, 0, 0))
        points.append(OpeningDataPoint(
            month=f"{year}-{month:02d}",
            designer=d,
            product_manager=pm,
            engineer=e,
        ))

    return points


OPENING_TRENDS_ALL_TIME: list[OpeningDataPoint] = _build_opening_trends()

# Slice indices for each range
_THIS_YEAR_START = _month_index(2026, 1)
_PAST_5_YEARS_START = _month_index(2021, 1)

OPENING_TRENDS: dict[str, list[OpeningDataPoint]] = {
    "this_year":    OPENING_TRENDS_ALL_TIME[_THIS_YEAR_START:],
    "past_5_years": OPENING_TRENDS_ALL_TIME[_PAST_5_YEARS_START:],
    "all_time":     OPENING_TRENDS_ALL_TIME,
}

OPENING_SUMMARIES: dict[str, str] = {
    "this_year": (
        "Designer openings are up 6% since January and Product Manager roles have grown 19%, "
        "driven by renewed hiring in B2B SaaS and AI-adjacent teams. "
        "Engineering openings are moving in the opposite direction, down 7% over the same period. "
        "Overall, the market remains well below its 2022 peak, though the divergence between "
        "categories is the clearest signal of where hiring confidence currently sits."
    ),
    "past_5_years": (
        "The tech job market peaked in mid-2022 then fell sharply through 2023 as the post-pandemic "
        "boom reversed and mass layoffs hit Engineering hardest. "
        "All three categories bottomed out in mid-2023 and have partially recovered since, "
        "but none have returned to 2022 highs. "
        "Designer and Product Manager roles have recovered faster than Engineering, "
        "which remains roughly 55% below its 2022 peak."
    ),
    "all_time": (
        "From 2019 to mid-2022, tech hiring grew steadily, accelerating after the pandemic recovery "
        "into a hiring boom that peaked in June 2022. "
        "A sharp correction followed through 2023 — Engineering fell over 55% from peak, "
        "while Designer and Product Manager roles declined around 47%. "
        "The market has stabilised since 2024 but has not returned to 2022 levels. "
        "The 2026 trend shows modest growth in Designer and PM roles alongside continued "
        "contraction in Engineering."
    ),
}

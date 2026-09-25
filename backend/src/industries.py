"""
Static company -> industry lookup. Deliberately not LLM-inferred: with only 35
tracked companies, a one-time manual tag is cheaper and more reliable than
asking a model to guess. Curated, not exhaustive — reviewed periodically, same
discipline as each adapter's curated COMPANIES list. See
backend/specs/market-health/api.md — Business Logic — Industry tagging.
"""

from __future__ import annotations

from employer_headcount import size_band_for  # noqa: F401  (re-exported: size now comes from headcount — see the RETIRED note below)

COMPANY_INDUSTRY: dict[str, str] = {
    # Greenhouse
    "stripe": "Fintech",
    "airbnb": "Travel/Marketplace",
    "pinterest": "Social Media",
    "asana": "Productivity Software",
    "reddit": "Social Media",
    "robinhood": "Fintech",
    "coinbase": "Fintech",
    "affirm": "Fintech",
    "webflow": "Web/Dev Tools",
    "figma": "Design Tools",
    "airtable": "Productivity Software",
    "cloudflare": "Cloud/Infrastructure",
    "twilio": "Developer Platform",
    "discord": "Social/Communications",
    "gitlab": "Developer Platform",
    # Greenhouse — UK employer panel, added 2026-09-18 (EMPLOYER_PANEL.md)
    "monzo": "Fintech",
    "deliveroo": "Food Delivery/Marketplace",
    "wise": "Fintech",
    "autotrader": "Automotive Marketplace",
    "cleo": "Fintech/AI",
    "rightmovecareers": "Property Marketplace/Tech",
    "ocadogroup": "Retail/Tech (Grocery/Robotics)",
    # Workable — UK employer panel, added 2026-09-19
    "starling-bank": "Fintech", "cuvva": "Insurtech",
    # Lever
    "palantir": "Enterprise Software/Data",
    "plaid": "Fintech",
    "clari": "Enterprise Software",
    "restream": "Media/Streaming Tools",
    "lever": "HR Tech",
    # Lever — UK employer panel, added 2026-09-18
    "zopa": "Fintech",
    # Ashby
    "ramp": "Fintech",
    "linear": "Productivity Software",
    "openai": "AI",
    "notion": "Productivity Software",
    "modal": "Developer Platform",
    "replit": "Developer Platform",
    "mercury": "Fintech",
    "deel": "HR Tech",
    "loom": "Productivity Software",
    "vercel": "Developer Platform",
    "supabase": "Developer Platform",
    "perplexity": "AI",
    "elevenlabs": "AI",
    "ashby": "HR Tech",
    "watershed": "Climate Tech",
    # Ashby — UK employer panel, added 2026-09-18
    "trainline": "Travel/Tech",
    "quantexa": "AI/Data",
    "faculty": "AI",
    "motorway": "Marketplace",
    "marshmallow": "Insurtech",
    "multiverse": "EdTech",
    "attio": "SaaS/CRM",
    "griffin": "Fintech (Banking-as-a-Service)",
    "sylvera": "Climate/Data",
    "beamery": "HR Tech",
    "incident": "SaaS (Incident Management)",
    # US + EU panel, batch 1 — added 2026-09-23 (EMPLOYER_PANEL.md)
    # Greenhouse
    "duolingo": "EdTech", "gusto": "HR Tech/Payroll", "carta": "Fintech",
    "khanacademy": "Nonprofit/EdTech", "doximity": "Healthtech",
    "glossier": "Retail/Consumer", "peloton": "Consumer Fitness",
    "n26": "Fintech", "getyourguide": "Travel/Marketplace",
    "contentful": "Enterprise Software", "trustpilot": "Consumer Reviews/Marketplace",
    "typeform": "SaaS", "algolia": "Search Software", "gymshark": "Retail/Consumer",
    # Lever
    "spotify": "Media/Streaming", "moonpig": "Retail/E-commerce",
    # Ashby
    "substack": "Media/Creator Platform", "vanta": "Security Software",
    "lemonade": "Insurtech", "pleo": "Fintech", "mollie": "Fintech",
    "deepl": "AI", "paddle": "Fintech Software", "synthesia": "AI",
    "thought-machine": "Fintech Software", "zego": "Insurtech",
}


def industry_for(company: str | None) -> str | None:
    """None if company is unknown or not yet tagged — never guessed."""
    if not company:
        return None
    return COMPANY_INDUSTRY.get(company)


# Employer panel metadata — added 2026-09-19 (EMPLOYER_PANEL.md), same
# discipline as COMPANY_INDUSTRY above: a static, curated lookup, NULL until
# a company is actually tagged, never guessed or inferred. See
# backend/specs/market-health/api.md — Business Logic — Employer metadata
# tagging.
#
# employer_region is populated for every tracked company — HQ country/region
# is well-established public fact, low risk to state confidently.
COMPANY_REGION: dict[str, str] = {
    # Greenhouse — original 35 (US-headquartered, unless noted)
    "stripe": "US", "airbnb": "US", "pinterest": "US", "asana": "US",
    "reddit": "US", "robinhood": "US", "coinbase": "US", "affirm": "US",
    "webflow": "US", "figma": "US", "airtable": "US", "cloudflare": "US",
    "twilio": "US", "discord": "US", "gitlab": "US",
    # Greenhouse — UK employer panel, added 2026-09-18/19
    "monzo": "UK", "deliveroo": "UK", "wise": "UK", "autotrader": "UK",
    "cleo": "UK", "rightmovecareers": "UK", "ocadogroup": "UK",
    # Workable — UK employer panel
    "starling-bank": "UK", "cuvva": "UK",
    # Lever — original 5
    "palantir": "US", "plaid": "US", "clari": "US", "restream": "US", "lever": "US",
    # Lever — UK employer panel
    "zopa": "UK",
    # Ashby — original 15
    "ramp": "US", "linear": "US", "openai": "US", "notion": "US", "modal": "US",
    "replit": "US", "mercury": "US", "deel": "US", "loom": "US", "vercel": "US",
    "supabase": "US", "perplexity": "US", "elevenlabs": "US", "ashby": "US",
    "watershed": "US",
    # Ashby — UK employer panel
    "trainline": "UK", "quantexa": "UK", "faculty": "UK", "motorway": "UK",
    "marshmallow": "UK", "multiverse": "UK", "attio": "UK", "griffin": "UK",
    "sylvera": "UK", "beamery": "UK", "incident": "UK",
    # US + EU panel, batch 1 — added 2026-09-23 (EMPLOYER_PANEL.md). HQ country,
    # ISO-2 for EU members (the UK keeps the existing "UK" spelling above).
    "duolingo": "US", "gusto": "US", "carta": "US", "khanacademy": "US",
    "doximity": "US", "glossier": "US", "peloton": "US", "substack": "US",
    "vanta": "US", "lemonade": "US",
    "n26": "DE", "getyourguide": "DE", "contentful": "DE", "deepl": "DE",
    "trustpilot": "DK", "pleo": "DK", "typeform": "ES", "algolia": "FR",
    "spotify": "SE", "mollie": "NL",
    "gymshark": "UK", "moonpig": "UK", "paddle": "UK", "synthesia": "UK",
    "thought-machine": "UK", "zego": "UK",
}

# employer_size_band — RETIRED as a hand-assigned label 2026-09-25
# (changes/2026-09-25-employer-size-standard-bands.md). This file used to hold
# COMPANY_SIZE_BAND, one of four platform-invented labels per company — Startup (<50),
# Small/Growth (50-500), Medium (500-5,000), Large (5,000+) — boundaries that matched no
# published standard, so nothing external could be compared against them, and 5 of the 21
# user-assigned UK buckets did not fit their real headcount. It is replaced by
# employer_headcount.py: a CITED headcount range per company (the source of truth), with the
# ONS size band (1-9, 10-49, 50-249, 250-2,499, 2,500+) derived from it. The old labels and
# the research behind them are kept in research/2026-09-19-original-35-size-bands.md and
# research/2026-09-18-uk-employer-panel-plan.md — "mark removed, don't erase".
#
# size_band_for() keeps its name and contract (None = not tagged, never guessed) so
# raw_postings.insert_new_postings() is unchanged; it now returns an ONS band code.


def region_for(company: str | None) -> str | None:
    """None if company is unknown or not yet tagged — never guessed."""
    if not company:
        return None
    return COMPANY_REGION.get(company)

"""
Static company -> industry lookup. Deliberately not LLM-inferred: with only 35
tracked companies, a one-time manual tag is cheaper and more reliable than
asking a model to guess. Curated, not exhaustive — reviewed periodically, same
discipline as each adapter's curated COMPANIES list. See
backend/specs/market-health/api.md — Business Logic — Industry tagging.
"""

from __future__ import annotations

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

# employer_size_band — populated ONLY where there's a real, stated basis, not
# a general impression. The 19 UK panel companies use the size bucket the
# user's own plan (research/2026-09-18-uk-employer-panel-plan.md) already
# assigned each one — a user-supplied classification, not this codebase's
# guess. Bands: Large (5,000+ employees), Medium (500-5,000), Small/Growth
# (50-500), Startup (<50) — matching the plan's own segmentation.
#
# The original 35 companies — added 2026-09-19
# (research/2026-09-19-original-35-size-bands.md) via real headcount
# research (Revelio Labs / company-reported figures, not general
# impression), same "confirm empirically" discipline as every ATS-token
# verification in EMPLOYER_PANEL.md. Figures conflict across sources for
# several companies (methodology differences — contractors counted or not,
# LinkedIn-graph vs. payroll); the band chosen is the one the weight of
# sources supports, not a single cherry-picked number — see that research
# file for every company's cited range. `lever` (the company, now a
# sub-brand of Employ Inc.) is left deliberately untagged — no real figure
# was found, not guessed.
COMPANY_SIZE_BAND: dict[str, str] = {
    # Greenhouse — original 15 (real 2026 headcount research, see
    # research/2026-09-19-original-35-size-bands.md for cited ranges)
    "stripe": "Large", "airbnb": "Large", "pinterest": "Large",
    "asana": "Medium", "reddit": "Medium", "robinhood": "Medium",
    "coinbase": "Medium", "affirm": "Medium", "webflow": "Medium",
    "figma": "Medium", "airtable": "Medium", "cloudflare": "Large",
    "twilio": "Large", "discord": "Medium", "gitlab": "Medium",
    # Greenhouse — UK employer panel (user-supplied classification)
    "monzo": "Medium", "deliveroo": "Medium", "wise": "Medium",
    "autotrader": "Medium", "cleo": "Small/Growth",
    "rightmovecareers": "Medium", "ocadogroup": "Medium",
    # Workable — UK employer panel (user-supplied classification)
    "starling-bank": "Medium", "cuvva": "Small/Growth",
    # Lever — original 5 (lever itself left untagged, see comment above)
    "palantir": "Medium", "plaid": "Medium", "clari": "Medium",
    "restream": "Small/Growth",
    # Lever — UK employer panel
    "zopa": "Medium",
    # Ashby — original 15
    "ramp": "Medium", "linear": "Small/Growth", "openai": "Large",
    "notion": "Medium", "modal": "Small/Growth", "replit": "Small/Growth",
    "mercury": "Medium", "deel": "Large", "loom": "Small/Growth",
    "vercel": "Medium", "supabase": "Small/Growth", "perplexity": "Medium",
    "elevenlabs": "Medium", "ashby": "Small/Growth", "watershed": "Medium",
    # Ashby — UK employer panel
    "trainline": "Medium", "quantexa": "Medium", "faculty": "Medium/Small",
    "motorway": "Medium", "marshmallow": "Medium", "multiverse": "Medium",
    "attio": "Small/Growth", "griffin": "Small/Growth", "sylvera": "Small/Growth",
    "beamery": "Small/Growth", "incident": "Small/Growth",
}


def region_for(company: str | None) -> str | None:
    """None if company is unknown or not yet tagged — never guessed."""
    if not company:
        return None
    return COMPANY_REGION.get(company)


def size_band_for(company: str | None) -> str | None:
    """None if company is unknown or not yet tagged — never guessed. See
    COMPANY_SIZE_BAND's own comment for why most of the original 35
    companies are deliberately untagged rather than estimated."""
    if not company:
        return None
    return COMPANY_SIZE_BAND.get(company)

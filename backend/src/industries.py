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
}

# employer_size_band — populated ONLY where there's a real, stated basis, not
# a general impression. The 19 UK panel companies use the size bucket the
# user's own plan (research/2026-09-18-uk-employer-panel-plan.md) already
# assigned each one — a user-supplied classification, not this codebase's
# guess. The original 35 companies are deliberately left untagged: real
# employee-count-based bands need actual research (same discipline as every
# ATS-token verification in EMPLOYER_PANEL.md), not an assistant's general
# impression of "how big Stripe feels" — see EMPLOYER_PANEL.md's own
# follow-up note. A wrong band here would undermine the exact credibility
# goal this feature exists to serve.
COMPANY_SIZE_BAND: dict[str, str] = {
    "monzo": "Medium", "deliveroo": "Medium", "wise": "Medium",
    "autotrader": "Medium", "cleo": "Small/Growth",
    "rightmovecareers": "Medium", "ocadogroup": "Medium",
    "zopa": "Medium",
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

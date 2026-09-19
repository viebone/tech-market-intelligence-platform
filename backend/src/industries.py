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

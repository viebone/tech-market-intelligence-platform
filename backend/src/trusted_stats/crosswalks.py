"""
Crosswalks: this platform's own labels -> an external publisher's classification.

A crosswalk exists ONLY where a specific cross-check needs one, is curated by hand, is versioned, and
says None where no honest mapping exists (backend/specs/trusted-statistics/api.md rule 2 and §6).
Nothing is force-mapped at ingestion.

OUR_INDUSTRY_TO_SIC_SECTION maps the free-form industry tags in industries.COMPANY_INDUSTRY to a UK
SIC 2007 SECTION code (a letter), or None. A tag maps to a section only where every company carrying it
plausibly belongs there; a tag that mixes activities (marketplaces, travel, delivery, HR tech, climate /
data mixes, EdTech that covers both apps and training providers, health-tech that is really a network)
is None and shows up in the cross-check as "not placed in an industry group" — never forced.

DRAFT for a human review (backend/specs/trusted-statistics/api.md — Open Questions): the deliberate
deviations from the spec's first draft rules are Healthtech (Doximity is a professional network, not a
health provider) and EdTech (mixes an app with a training provider) -> None.

A completeness test (tests/test_trusted_stats.py) fails the build if a tag in COMPANY_INDUSTRY has no
entry here — adding an industry tag without deciding its mapping is not possible.
"""

from __future__ import annotations

CROSSWALK_VERSION = "2026-09-25.1"

OUR_INDUSTRY_TO_SIC_SECTION: dict[str, str | None] = {
    # J — Information and communication: software, AI, developer/cloud platforms, media, social, search, security
    "AI": "J", "AI/Data": "J", "Cloud/Infrastructure": "J", "Design Tools": "J", "Developer Platform": "J",
    "Enterprise Software": "J", "Enterprise Software/Data": "J", "Media/Creator Platform": "J",
    "Media/Streaming": "J", "Media/Streaming Tools": "J", "Productivity Software": "J", "SaaS": "J",
    "SaaS (Incident Management)": "J", "SaaS/CRM": "J", "Search Software": "J", "Security Software": "J",
    "Social Media": "J", "Social/Communications": "J", "Web/Dev Tools": "J",
    # K — Financial and insurance activities
    "Fintech": "K", "Fintech (Banking-as-a-Service)": "K", "Fintech/AI": "K", "Insurtech": "K",
    # G — Wholesale and retail trade
    "Retail/Consumer": "G", "Retail/E-commerce": "G", "Retail/Tech (Grocery/Robotics)": "G",
    # P — Education (an education nonprofit only; the mixed EdTech tag is None)
    "Nonprofit/EdTech": "P",
    # None — genuinely ambiguous or mixed; reported as "not placed", never forced
    "Automotive Marketplace": None, "Climate Tech": None, "Climate/Data": None, "Consumer Fitness": None,
    "Consumer Reviews/Marketplace": None, "EdTech": None, "Fintech Software": None,
    "Food Delivery/Marketplace": None, "HR Tech": None, "HR Tech/Payroll": None, "Healthtech": None,
    "Marketplace": None, "Property Marketplace/Tech": None, "Travel/Marketplace": None, "Travel/Tech": None,
}


def sic_section_for(industry_tag: str | None) -> str | None:
    """SIC section letter for one of our industry tags, or None (unmapped, or no tag). Never guessed."""
    if not industry_tag:
        return None
    return OUR_INDUSTRY_TO_SIC_SECTION.get(industry_tag)

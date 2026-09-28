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

CROSSWALK_VERSION = "2026-09-28.3"

OUR_INDUSTRY_TO_SIC_SECTION: dict[str, str | None] = {
    # J — Information and communication: software, AI, developer/cloud platforms, media, social, search, security
    "AI": "J", "AI/Data": "J", "Cloud/Infrastructure": "J", "Design Tools": "J", "Developer Platform": "J",
    "Enterprise Software": "J", "Enterprise Software/Data": "J", "Media/Creator Platform": "J",
    "Media/Streaming": "J", "Media/Streaming Tools": "J", "Productivity Software": "J", "SaaS": "J",
    "SaaS (Incident Management)": "J", "SaaS/CRM": "J", "Search Software": "J", "Security Software": "J",
    "Social Media": "J", "Social/Communications": "J", "Web/Dev Tools": "J",
    # Added 2026-09-27 with the US + EU panel batch 2 — pure software products/platforms,
    # same reasoning as the existing J entries above.
    "AI Software": "J", "Analytics Software": "J", "Gaming": "J", "Marketplace Software": "J",
    "Security": "J", "Software": "J",
    # Added 2026-09-28 with the US + EU panel batch 3 — Restaurant Tech (Flipdish) is an ordering
    # software platform, not a restaurant operator; Autonomous (Wayve) is fundamentally an AI/
    # software company (self-driving models), same reasoning as the existing "AI" entry, even
    # though it also tests physical vehicles.
    "Restaurant Tech": "J", "Autonomous": "J",
    # Added 2026-09-28 with the US + EU panel batch 4 — pure software products/platforms serving
    # an industry, not an operator in it, same reasoning as "Restaurant Tech" above (Healthtech AI
    # / Abridge is an AI clinical-documentation vendor, not a care provider). "Media" (Vox Media,
    # BuzzFeed, Medium) is placed on the structure of SIC section J itself, not by analogy — J's
    # own divisions include publishing, broadcasting and motion-picture activities alongside
    # software, the same breadth the tech-and-communications trend block's own qualifier states.
    "DevOps Software": "J", "Observability Software": "J", "Cloud Software": "J",
    "Edge Cloud": "J", "Consumer Internet": "J", "Media": "J", "Healthtech AI": "J",
    # Mozilla's underlying activity is software development (Firefox); "nonprofit" is a legal/tax
    # structure, not a SIC activity — same reasoning already applied to "Nonprofit/EdTech" -> P
    # (classified by activity, not nonprofit status).
    "Nonprofit/Software": "J",
    # K — Financial and insurance activities
    "Fintech": "K", "Fintech (Banking-as-a-Service)": "K", "Fintech/AI": "K", "Insurtech": "K",
    # Added 2026-09-27 — crypto exchanges/custody are financial-services activity, same section as Fintech.
    "Crypto": "K",
    # Added 2026-09-28 — Alan is fundamentally a regulated health insurer (its telehealth clinic
    # is additive), same section as the existing "Insurtech" entry.
    "Insurtech/Health": "K",
    # G — Wholesale and retail trade
    "Retail/Consumer": "G", "Retail/E-commerce": "G", "Retail/Tech (Grocery/Robotics)": "G",
    # Added 2026-09-27 — Farfetch's own tag string, distinct from "Retail/E-commerce" above but same section.
    "E-commerce": "G",
    # P — Education (an education nonprofit only; the mixed EdTech tag is None)
    "Nonprofit/EdTech": "P",
    # I — Accommodation and food service activities. Added 2026-09-28 with batch 4: Sweetgreen is
    # an unambiguous restaurant chain (a fast-casual operator, not a software vendor to
    # restaurants — that's "Restaurant Tech", already J) — the cleanest single-company fit for a
    # new section this crosswalk has had, no genuine mixing to weigh.
    "Restaurant": "I",
    # None — genuinely ambiguous or mixed; reported as "not placed", never forced
    "Automotive Marketplace": None, "Climate Tech": None, "Climate/Data": None, "Consumer Fitness": None,
    "Consumer Reviews/Marketplace": None, "EdTech": None, "Fintech Software": None,
    "Food Delivery/Marketplace": None, "HR Tech": None, "HR Tech/Payroll": None, "Healthtech": None,
    "Marketplace": None, "Property Marketplace/Tech": None, "Travel/Marketplace": None, "Travel/Tech": None,
    # Added 2026-09-26 with the Personio adapter — each tag spans software AND non-software activity
    # (a defence-tech firm may build drones = manufacturing, or software; construction tech may be SaaS or a builder).
    "Construction Tech": None, "Defence Tech": None,
    # Added 2026-09-27 with the US + EU panel batch 2 — each genuinely mixes activities: Crypto
    # Analytics is a compliance-software vendor serving crypto/finance, not itself a financial
    # institution; Gaming/Crypto spans two of the sections above with no single fit; Health
    # Wearables mixes hardware, software and a health service (same reasoning as Healthtech);
    # Logistics and Mobility mix a software platform with the actual transport/freight operation
    # (same reasoning as Automotive Marketplace); Travel Tech mixes software with travel services
    # (same reasoning as Travel/Tech).
    "Crypto Analytics": None, "Gaming/Crypto": None, "Health Wearables": None, "Logistics": None,
    "Mobility": None, "Travel Tech": None,
    # Added 2026-09-28 with the US + EU panel batch 3: Delivery (Wolt) mixes a software platform
    # with the actual delivery operation (same reasoning as Food Delivery/Marketplace);
    # Semiconductors/AI (Graphcore) designs and manufactures physical chips — real manufacturing
    # activity, not software, and no manufacturing section is otherwise mapped in this crosswalk,
    # so forcing one here would be a guess, not a decision.
    "Delivery": None, "Semiconductors/AI": None,
    # Added 2026-09-28 with the US + EU panel batch 4 — Digital Health (Ro) mixes a telehealth
    # service with pharmacy/medication logistics, the same "mixed, not a single clean activity"
    # reasoning as the existing "Healthtech" entry.
    "Digital Health": None,
    # Added 2026-09-28 with the US + EU panel batch 5: Grocery Tech (Instacart) mixes a software
    # platform with the actual grocery delivery/logistics operation, same reasoning as the
    # existing "Food Delivery/Marketplace" entry; Earth Observation (Planet Labs) mixes operating
    # a physical satellite fleet (real space-hardware infrastructure) with selling imagery/data
    # analytics software — genuine mixing, same "hardware operation, not just software" reasoning
    # as Semiconductors/AI; Climate/Materials (Redwood Materials) is battery-materials recycling
    # and processing — real industrial/manufacturing activity, not software.
    "Grocery Tech": None, "Earth Observation": None, "Climate/Materials": None,
}


def sic_section_for(industry_tag: str | None) -> str | None:
    """SIC section letter for one of our industry tags, or None (unmapped, or no tag). Never guessed."""
    if not industry_tag:
        return None
    return OUR_INDUSTRY_TO_SIC_SECTION.get(industry_tag)

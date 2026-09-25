"""
Canonical UK SIC 2007 section names.

ONS's data-file header text is NOT used for labels: it carries hyphenation artefacts ("Manu-    facturing",
"Construc-tion", "Administra-tive") and truncated wording (real files, 2026-09-24). The SIC code row
in the file is authoritative; the label always comes from here.
"""

from __future__ import annotations

SIC_2007_SECTIONS: dict[str, str] = {
    "A": "Agriculture, forestry and fishing",
    "B": "Mining and quarrying",
    "C": "Manufacturing",
    "D": "Electricity, gas, steam and air conditioning supply",
    "E": "Water supply, sewerage, waste management and remediation activities",
    "F": "Construction",
    "G": "Wholesale and retail trade; repair of motor vehicles and motorcycles",
    "H": "Transportation and storage",
    "I": "Accommodation and food service activities",
    "J": "Information and communication",
    "K": "Financial and insurance activities",
    "L": "Real estate activities",
    "M": "Professional, scientific and technical activities",
    "N": "Administrative and support service activities",
    "O": "Public administration and defence; compulsory social security",
    "P": "Education",
    "Q": "Human health and social work activities",
    "R": "Arts, entertainment and recreation",
    "S": "Other service activities",
    "T": "Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use",
    "U": "Activities of extraterritorial organisations and bodies",
}

# The sections the ONS Vacancy Survey covers (it excludes A, T and, within N, division 78 — employment agencies).
VACANCY_SURVEY_SECTIONS: tuple[str, ...] = tuple("BCDEFGHIJKLMNOPQRS")

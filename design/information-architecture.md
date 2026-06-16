---
id: information-architecture
version: 1.0
status: active
created: 2026-06-11
---

# Information Architecture — Tech Market Intelligence Platform

## Navigation Model

The product uses a persistent left sidebar navigation. The sidebar is always visible
on desktop; on mobile it collapses to a bottom tab bar. The conversational interface
is accessible from any section via an embedded panel — it is not a separate section.

| Section | What it contains |
|---|---|
| **Market Health** | Aggregate market signal: overall health verdict, demand trend, layoff activity, salary movement. Primary landing section. |
| **Skills & Demand** | Which skills are rising or declining in job postings. Breakdown by role family and seniority. |
| **Salary Intelligence** | Salary benchmarks by role, seniority, location, and employment type. Trend over time. |
| **Market Signals** | Activity feed of notable market events: layoff announcements, hiring surges, role category shifts. |
| **Alert Centre** | User-configured monitoring rules. Manage thresholds, notification channels, and delegation settings. |

The **Market Health** section is the default landing and the product's primary orientation point.
All other sections are accessible directly from the sidebar and via drill-down from Market Health.

---

## Content Taxonomy

All labels, headings, statuses, and terminology across the product must use these exact terms.
Experience specs must not introduce synonyms or alternate names.

| Term | Definition | Where it appears |
|---|---|---|
| **Market Health Signal** | The aggregate verdict on current job market conditions: Healthy, Cautious, or Contracting | Market Health header, Alert triggers |
| **Demand Signal** | A data point representing job posting volume trend for a given role or skill | Market Health, Skills & Demand |
| **Skill Signal** | A data point representing a skill's presence or absence in recent job postings | Skills & Demand |
| **Compensation Signal** | A data point representing salary range trend for a given role, seniority, or location | Salary Intelligence |
| **Layoff Signal** | A reported or confirmed layoff event affecting a company or sector | Market Signals, Market Health |
| **Market Alert** | A user-configured rule that fires when a signal crosses a defined threshold | Alert Centre, notification surfaces |
| **Search Implication** | A plain-language statement of what a given signal means for the user's job search | Shown beneath each major data section |
| **Data Freshness** | The age and source of the data behind any given signal | Shown as a label on all data-backed claims |
| **Delegation Level** | The user's configured autonomy setting for a given system capability: Reactive, Proactive, or Autonomous | Alert Centre, system behaviour indicators |
| **Exception** | A signal or event that crosses a threshold and requires the user's attention | Alert Centre, notification surfaces |

---

## Key Pathways

These are the journeys that cross section boundaries. Single-section flows are defined
in individual experience specs.

1. **Market read before searching** — User lands on Market Health → reads Market Health Signal → reviews supporting Demand and Compensation Signals → reads Search Implications → optionally drills into Skills & Demand or Salary Intelligence → sets a Market Alert if the signal is borderline.

2. **Conversational market query** — User types or speaks a question ("Is now a good time to search for a senior UX role in London?") → system surfaces relevant signals inline → user interrogates a specific data point → optionally saves or shares the result.

3. **Alert-triggered review** — User receives a notification → deep-links to the specific signal that fired the Market Alert → reviews context → resolves or adjusts the alert threshold → returns to Alert Centre.

4. **Skills calibration** — User navigates to Skills & Demand → filters by role family and seniority → identifies rising skills to add to their positioning and declining skills to deprioritise → reads Search Implications.

5. **Salary benchmarking** — User navigates to Salary Intelligence → sets role, seniority, and location → reads Compensation Signal → reads Search Implication → optionally sets a Market Alert for salary movement.

---

## Entry Points

- **Direct navigation** — User lands on Market Health. This is the default entry for all direct visits and app opens.
- **Notification / alert deep-link** — A Market Alert notification links directly to the specific signal or Exception that triggered it. The user arrives in context, not on the landing page.
- **Conversational entry** — User begins with a natural-language question from any surface (home screen widget, assistant, search). The system resolves the query to the most relevant section and signals, and presents them inline within the conversation. No section navigation required to get the answer.
- **Returning user with active alerts** — User has configured alerts. On return, the system surfaces any Exceptions since the last visit before showing the standard Market Health view.

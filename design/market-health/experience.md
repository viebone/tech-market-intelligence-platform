---
id: market-health
outcome: understand-market-health-before-searching
directive: low
status: ready
created: 2026-06-13
---

# Market Health — Experience Spec

## Outcome this serves

See: `outcomes/understand-market-health-before-searching.md`

---

## Information Architecture

**Location:** Market Health (primary landing section)

This feature occupies the entire viewport. The page is a conversation. There is no static layout —
all content is AI-generated and appears inside a scrollable conversation thread.

| Zone | Priority | Contains |
|---|---|---|
| Top Bar | Primary | Product title. Fixed, always visible. No navigation beyond this in v1. |
| Conversation Thread | Primary | The full scrollable content area. Contains AI-generated messages and user messages. The opening message is generated automatically on load — it contains the market health briefing, demand signals, compensation signals, layoff signals, and filter controls. Subsequent messages are user questions and AI answers. |
| Prompt Transparency | Primary | Every AI-generated message exposes a "view prompt" affordance. Tapping it reveals the exact prompt that produced that message. This applies to the opening briefing and all follow-up answers. |
| Chat Input | Primary | Fixed, full-width, always visible at the bottom of the viewport. The user types here to ask follow-up questions. |
| Data Freshness | Tertiary | Age and source labels on all data-backed claims within the conversation thread. |

---

## User Flow

1. The user opens the product. The page loads with a fixed top bar and an empty conversation thread.
2. The system immediately fires the opening prompt — the user sees the AI generating the full market briefing: market health signal, search implication, demand signals with filter controls, compensation signals, and layoff signals. The user did not type anything; the system acted on their behalf.
3. The user reads the briefing. They can tap "view prompt" on any section to see the exact prompt that generated it.
4. The user optionally applies filters (role, seniority, location, time range) surfaced within the AI-generated briefing. Changing a filter re-generates the relevant section.
5. The user types a follow-up question in the fixed chat input at the bottom ("Is now a good time to look for a senior UX role in London?").
6. The AI responds with a new message in the thread — direct answer with supporting signals shown inline.
7. The conversation grows downward. Each answer exposes a "view prompt" affordance.
8. The user leaves with a clear, evidence-backed read on the market and calibrated expectations for their search.

---

## Visual Design

The layout has three persistent elements: fixed top bar, scrollable conversation thread, fixed chat input.

**Top bar** — fixed, full width. Contains the product title only. Minimal. Does not scroll away.

**Conversation thread** — occupies all space between the top bar and the chat input. Scrollable.
Messages are left-aligned (AI) and right-aligned (user), consistent with chat conventions.
The opening AI message is the full market briefing — it contains the same content as the previous
layout (signal, implication, trend charts, layoff list, filters) but rendered inside a message bubble.
Each AI message carries a small "view prompt" affordance (e.g., a subtle icon or link). Tapping it
opens a read-only view of the exact prompt that produced that message — no editing, just transparency.

**Chat input** — fixed, full width, pinned to the bottom of the viewport. Always visible regardless
of scroll position. Placeholder: "Ask about the market…". Send button on the right.

Visual tone: information-dense but uncluttered. Neutral, evidence-based. No urgency language or
sentiment framing beyond what the data supports. The conversation frame keeps the experience feeling
live and responsive rather than like a dashboard.

---

## Interactions

| User action | System response |
|---|---|
| Open Market Health (first visit or return) | Show Market Health Signal, Search Implication, and trend areas with current data. Surface any Exceptions since last visit before showing the standard view. |
| Ask a question in the conversational area | Respond with a direct answer and supporting signals (Demand, Compensation, or Layoff Signals) shown inline |
| Select a role from a trend area or filter | Update Demand Signals, Skill Signals, and Compensation Signals for that role across all trend areas |
| Select a location from filters | Update all signals and trend areas to reflect that market |
| Change the time range | Update charts and explanation copy; Data Freshness labels update accordingly |
| Select a skill in the trend area | Show whether the Skill Signal for that skill is rising, stable, or declining, with a Search Implication |
| Select a company | Show hiring activity and any associated Layoff Signals |
| Set an alert from a data point | Navigate to Alert Centre pre-populated with the relevant signal and threshold |

---

## Edge Cases

- **Insufficient data:** If a combination of filters has too few data points to support a conclusion, show what is available and state clearly that confidence is low. Do not show a Market Health Signal verdict if the data does not support one.
- **Partial data availability:** If some signals are unavailable (e.g., Compensation Signals for a niche role), show the signals that exist and indicate which are missing with a Data Freshness label explaining why.
- **No results for filter combination:** Explain that no data is available for that combination and suggest the closest alternative (e.g., broader role family, adjacent location).
- **Loading state:** While data loads, keep the previous state visible with a progress indicator on the sections being refreshed. Do not blank the whole page.
- **Unanswerable conversational query:** If the system cannot answer a question with sufficient confidence, say so plainly, explain the limitation, and suggest 1–2 related questions it can answer.
- **Returning user with active alerts:** Show Exceptions since last visit as a prioritised header before the standard Market Health view. The user can dismiss or review them.

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Task completion rate — market read in under 5 minutes | Usability test (timed task: "give me your assessment of the market") | ≥ 85% complete within 5 min |
| Time to first insight | Analytics — time from page load to first scroll past Search Implication | < 30 seconds |
| Market Health Signal comprehension accuracy | Post-task question: "What does the current market verdict mean for your search?" | ≥ 80% correct interpretation |
| Conversational query resolution rate | Analytics — queries that receive an answer vs. fallback to "I can't answer" | ≥ 75% resolved |
| Filter error rate | Usability test — filter interactions that produce no-results or confused states | < 10% |
| Return visit rate | Analytics — users who return to Market Health within 7 days | TBD after baseline |

---

## Open Questions

- Should the experience focus only on UX roles initially, or include Product Managers and Software Engineers? (PM decision — affects scope of Demand and Skill Signals)
- Should users be able to compare two markets or roles side by side, or is a single-filter read sufficient for v1?
- Should the Market Health Signal use a numerical confidence score alongside the label, or labels only?
- Should the experience surface recommendations ("consider expanding to contract roles") or observations only?
- Should Layoff Signals and hiring surges appear together in the trend area or in separate zones?

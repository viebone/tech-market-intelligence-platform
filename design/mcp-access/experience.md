---
id: mcp-access
outcome: bring-your-own-ai-agent-access
directive: low
status: ready
created: 2026-09-14
updated: 2026-09-15
---

# AI Agent Access — Experience Spec

## Outcome this serves
See: `outcomes/bring-your-own-ai-agent-access.md`

## A note on structure

This spec covers two genuinely different surfaces, per `design/foundations.md` v1.3's Scope
section (the "external access surfaces" carve-out added for this outcome):

- **Part 1 — Connections & Permissions.** A real surface in this product's own UI — the Output
  Panel's **Settings** tab, alongside the existing Output tab — where the user connects,
  inspects, and revokes an external AI client. It needs no exemption from the Agentic
  Conversational UI paradigm: it lives inside a zone the paradigm already treats as
  non-conversational. It is **not** exempt from Principle 5 — revoking a connection *is* the
  direct manipulation this surface exists to support.
- **Part 2 — What a good answer feels like.** Not a UI at all. This platform never renders the
  external AI's response — Claude, ChatGPT, or Gemini's own interface does. This part specifies
  the *user-outcome-level* intent and the *data-legibility* obligations that bind whatever the
  backend spec eventually builds, not a screen.

The standard experience-spec template assumes one surface. It's split into two parts below
instead of forced into one, the same way `design/pipeline-visibility/experience.md` and
`design/ai-reasoning-panel/experience.md` each adapted the template to what they actually needed
to describe.

---

## Part 1 — Connections & Permissions

### Information Architecture

**Resolved 2026-09-14** via `/new-information-architecture` (`design/information-architecture.md`
v2.6) — this surface, and its entry point, are now part of the Navigation Model and Content
Taxonomy. **Location:** Output Panel > **Settings tab** > **Connect Your AI**.

The Output Panel already exists on every Task (320px fixed, right column). It now carries two
tabs — **Output** (existing, default) and **Settings** (new) — and switching to Settings shows
Connect Your AI. Because Settings is account-level, not task-level, its content is identical no
matter which Task the user was on when they switched to it. (An earlier draft of this section
proposed a new TopBar "Account" entry instead; superseded same day in favour of this simpler
placement, which needed no new layout element. Kept here only for traceability.)

Zone names below now use the IA's official terms:

| Zone | Priority | Contains |
|---|---|---|
| Settings tab header | Primary | Title ("Connect your AI"), one-line explanation, the platform's MCP endpoint (to paste into an external client) |
| Connections List | Primary | Every current **Connected Assistant**: which client, when connected, what it can see, what plan tier applies, a revoke action per row |
| Empty State | Primary (when list is empty) | Explains what connecting does, in plain language, before any Connected Assistant exists |

### Opening Prompt

Not applicable. Per the Scope carve-out, this surface is exempt from the Agentic Conversational
UI paradigm — there is no conversation, no opening AI message, nothing generated. Every element
on this page is either static copy or a direct readout of the user's own connection records.

### User Flow

This feature has two entry paths, because the actual authorization exchange happens **outside**
this product — inside whichever AI client the user is using — even though the consent step
itself renders on this platform.

**Flow A — Discovering how to connect (starts in this product)**
1. The user switches the Output Panel from Output to Settings, from whichever Task they're on.
2. They see the platform's MCP endpoint and short, plain-language instructions per common client
   ("In Claude: add a custom connector using this address..."), and, below that, their current
   Connections List (empty on first visit).
3. They copy the endpoint and go set it up in their AI client of choice. This product's part of
   this path ends here — the rest happens in that client.

**Flow B — Granting access (starts in the external client, lands on this platform)**
1. The user adds this platform's MCP endpoint inside Claude, ChatGPT, Gemini CLI, or any other
   MCP-compatible client.
2. That client opens this platform's sign-in/consent screen (in a browser tab or embedded view,
   depending on the client).
3. If not already signed in, the user signs in to their platform account first — this establishes
   *whose* data and plan the connection will use, before any scope is shown.
4. The user sees a consent screen: which client is requesting access, and what it's asking to do,
   stated in plain outcome language, not backend scope names (see Visual Design, below).
5. The user grants access. They are returned to their AI client, now connected — no separate
   confirmation step needed on this platform's side; granting *is* completing.
6. The new connection now appears in this platform's Connections List (the Settings tab) the
   next time the user opens it — same list, populated.

**Flow C — Reviewing and revoking (starts in this product)**
1. The user switches to the Settings tab and sees every currently authorized client: which one,
   roughly when it was connected ("Connected 3 days ago"), what it can see (in plain language),
   and its plan tier.
2. The user clicks "Revoke" on a connection they no longer want.
3. The row confirms inline ("Are you sure? This assistant will lose access immediately") — a
   lightweight, same-surface confirmation, not a separate page or modal.
4. On confirming, the row updates immediately to show it's revoked (or is removed from the list)
   — reflecting that access is already gone, not pending removal. See Part 2's Edge Cases for
   what the external client experiences on its next call.

### Visual Design

This lives inside the existing **Output Panel** (320px fixed) — not a full page. That's a real
constraint: everything below has to work in a narrow, vertically-stacked column, reusing the
Output Panel's existing surface/type/spacing tokens rather than the roomier layout a standalone
settings page would allow. **Resolved 2026-09-14** via `/new-visual-design`
(`design/visual-design.md` v1.7) — the tab switcher, the Connected Assistant card, the Plan
tier badge mapping, and the OAuth consent screen are now formalized there (Component
Aesthetics — "Output Panel — Settings tab" and "OAuth consent screen"). This section restates
them at the experience level; `visual-design.md` is the source of truth for exact tokens.

**Tab switcher (proposed):** reuse the existing "Tab / range selector" pattern from
`design/visual-design.md` (the same pill-style control already used for chart time ranges) —
two tabs, "Output" and "Settings", pinned at the top of the Output Panel, above whichever tab's
content is showing. Switching tabs never affects the Task Panel or Working Space.

**Panel structure when Settings is active (proposed, pending visual-design formalization):**
```
Output Panel (320px fixed)
┌───────────────────────────┐
│  [Output] [Settings]      │  ← Tab / range selector pattern, pinned
├───────────────────────────┤
│  Settings tab header      │
│   "Connect your AI"        — Section-heading scale, gray-100 (panel is narrow;
│                               Conversation-title scale would crowd it)
│   One-line explanation     — Caption scale, gray-400
│   MCP endpoint              — Monospace, gray-100, gray-800 surface, truncated
│    [Copy] button             with an inline Copy action (full value never
│                               force-wraps the panel width)
│   Per-client instructions  — collapsed by client, Body scale, expands inline
│                                                                            │
│  Connections List (or Empty State)                                       │
│   One compact card per connection, stacked vertically (no room for a     │
│   side-by-side row at this width):                                       │
│     Client name + icon      — Section-heading scale, gray-100            │
│     "Connected {relative time}" — Caption scale, gray-400                │
│     Scope chips              — Filter-chip pattern, gray-700 surface,    │
│                                  wrap onto multiple lines as needed       │
│     Plan tier badge          — Status-badge pattern (existing semantic   │
│                                  colours — e.g. "Free" = amber, "Premium" │
│                                  = emerald, same logic already used for   │
│                                  "Pending"/"Failed")                      │
│     "Revoke" — Ghost/text action, turns into an inline confirm on click  │
└───────────────────────────┘
```

**Scope chips must read as plain language, not backend enum names** (data-legibility, applied to
this platform's own UI now, not just to what an external AI receives) — e.g. "Can read job
market data" rather than `jobs.read`. The exact wording is a content decision (`end-user-content`
skill), not settled here, but the *rule* — never render a raw scope identifier to a human — is
part of this experience.

**Consent screen (rendered when an external client initiates the OAuth flow):** unaffected by
the Output Panel placement above — this is a separate, standalone screen, not part of the
three-column layout at all (a first-time visitor may not be inside the product's main view yet).
Same visual system (dark surfaces, existing type scale), stripped down — no Task Panel, no
Output Panel, just: who is requesting access (client name), what it's asking to do (the same
plain-language scope phrasing as the chips above, as a checklist), and two primary actions
("Allow" / "Cancel"). It must be legible entirely on its own — no assumed context from elsewhere
in the product.

### Interactions

| User action | System response |
|---|---|
| Clicks the "Settings" tab | Output Panel switches from Output to Settings; Task Panel and Working Space are unaffected. Switching Task afterward leaves Settings showing — it does not snap back to Output. |
| Clicks the "Output" tab | Output Panel switches back to the reference index for the active Task. |
| Clicks "Copy" next to the MCP endpoint | Endpoint copies to clipboard; a brief inline confirmation appears ("Copied"), then fades — same `transition-colors duration-150` used elsewhere |
| Expands a client's setup instructions | Instructions expand inline, same expand/collapse treatment as the Reasoning Panel (height transition, `duration-200`) |
| Grants access on the consent screen | Redirects back to the originating AI client; this platform shows a brief "You're connected — return to your assistant" state if the redirect doesn't happen instantly |
| Cancels on the consent screen | Returns the user to sign-in or closes the tab/view, depending on how the client opened it; no partial grant is ever recorded |
| Clicks "Revoke" | Row shows an inline confirm state (not a modal); confirming updates the row immediately to reflect revocation |
| Views the list with zero connections | Empty State renders — explains what connecting does and links to the setup instructions above it; never a bare "No connections" with nothing else |

### Edge Cases

- **The same client is added twice.** The consent screen recognizes an existing, active
  connection for that client and shows it as already connected rather than creating a silent
  duplicate — the user is told plainly, not left to notice two identical rows later.
- ~~A connection's underlying token has already expired or was revoked by the AI client's own
  side~~ — **Corrected 2026-09-15** (`backend/specs/mcp-access/api.md`): this isn't observable
  over real OAuth — this platform is the sole source of truth for whether a grant is active, and
  an external client has no way to signal "the user disconnected me over there." There are only
  two states: active, or revoked by this platform. No third "disconnected by client" row state
  exists.
- **The user has never connected anything.** The Empty State is the first thing shown, and it
  actively explains the value ("Ask Claude, ChatGPT, or another AI assistant about the job
  market — using this platform's data, with your own AI subscription") rather than a blank
  list waiting to be filled.
- **The user revokes a connection while an external AI is actively using it.** See Part 2, Edge
  Cases — the *effect* is specified there because it's the external tool call that surfaces it,
  not anything rendered on this page.

---

## Part 2 — What a Good Answer Feels Like

### Scope of this part

This platform has no rendering control here — Claude, ChatGPT, and Gemini each present the
answer in their own interface, their own way. What this platform *does* control is the data it
hands back: what's offered, how it's shaped, and whether it's trustworthy on its own, without
this platform's own charts, legends, or Reasoning Panel able to travel with it. This section
specifies intent and constraints, not a UI — and not tool names, parameters, or schemas, which
belong to `/new-backend-spec`.

### What a user should be able to get, through their own AI

Grounded directly in `outcomes/understand-market-health-before-searching.md`'s success
criteria — this is not a new feature list, it's the same outcome reached through a different
front door:

- Whether now is a good or bad time to search, for a role and location they specify
- Which roles and skills are in demand vs. declining, and how that's moved over a time window
  they can specify (not fixed to whatever window this platform's own UI defaults to)
- A realistic salary target for a role, seniority, and geography
- Employment risk alongside demand — layoffs, closures, restructuring, expansion — at the
  company or sector level, not just open-role counts
- The ability to compare more than one role, location, or time window against each other in a
  single question, since that's exactly the kind of composition an external AI is positioned to
  do well (per the outcome's "someone can point three different AI assistants at this platform
  and get answers that agree with each other" criterion) — the user is doing the comparing by
  asking, not this platform pre-building a comparison feature it would otherwise have to invent
  and maintain

None of this should feel like a smaller or stripped-down version of the "Tech market hiring
status" task in this product's own UI — it should feel like the same underlying intelligence,
reached a different way.

### Data Legibility for self-contained responses

The `data-legibility` skill's checklist (title, unit, scope/time window, and a legend wherever
colour or shape carries meaning) was written for something this platform renders. Nothing here
is rendered by this platform — so every one of those obligations has to be carried **inside the
data itself**, because the external AI may quote a number to its user with zero added framing
of its own. This is the binding constraint the backend spec inherits from Principle 9 (Curated
Access, Never Raw):

- **Every value states its own unit and scope in the same response it's returned in** — not in
  a separate doc, not assumed from context. A number of job openings names the role/category,
  geography, and time window it covers alongside the count itself; a salary figure names the
  currency, period (annual vs. monthly), and percentile or range it represents; a trend or
  comparison names both time windows being compared, in words, not just as raw dates.
- **Category and taxonomy labels are always this platform's own plain-language terms** — the
  same Role Category names already fixed by `design/information-architecture.md`'s Content
  Taxonomy (Designer, Product Manager, Engineer), the same seniority ladder, never an internal
  code or an abbreviation the external AI would have to guess the meaning of.
- **Every value is traceable to this platform's own data**, carrying something equivalent to
  what the Reasoning Panel already gives a human user — at minimum, how current the data is and
  roughly how it was derived (a count, a computed trend, a classification) — so an external AI
  that's asked "how do you know that?" has something honest to relay back, in keeping with
  `outcomes/ai-reasoning-transparency.md`'s bar, even without a Reasoning Panel to expand.
- **A curated shape, never a raw one** — every response is built from this platform's own
  defined operations (Principle 9), so its shape is something this platform chose because it's
  helpful, not an accidental byproduct of an internal query. If an operation can't answer what
  was asked, it says so plainly (see Edge Cases) rather than returning something adjacent and
  letting the external AI guess.

*(Illustrative only — the backend spec owns the actual shape:* a job-openings figure isn't
just `4200`, it's something like *"4,200 job openings for Product Designer roles in the UK,
August 2026"* worth of information travelling together, however the backend spec chooses to
structure it.)

### Edge Cases

- **A connection is revoked mid-conversation.** The very next tool call made through that
  connection fails — not with a raw error code, but with a plain-language reason ("Access to
  this platform was revoked") the external AI can relay to its user directly, matching Principle
  9's "revocation must take effect on the next call, no grace window."
- **A free-plan user's assistant asks for something reserved for premium.** The response states
  plainly what's not included at the current plan and what upgrading would unlock — never a
  silent empty result and never a raw permission error the external AI would have to interpret
  or paraphrase badly.
- **A question this platform's data genuinely can't answer.** The response says so plainly,
  scoped to what it *can* answer (matching this product's existing "we don't track that" pattern
  in its own chat) — never a best-effort guess dressed up as data.
- **Rate limits are reached.** The response is a clear, curated message stating that a limit was
  hit and roughly when it resets — never a raw `429`.

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Connection completion rate | Analytics: % of consent-screen views that end in "Allow" | > 80% |
| Time to first working connection | Usability test: from opening "Connect your AI" to a successful tool call in the external client | < 3 minutes |
| Revoke-to-effect latency | Automated test: time between a revoke action and the next tool call failing | Immediate — the very next call, no grace window (matches `design/foundations.md`'s Curated Access Integrity goal) |
| Self-explanatory response rate | Manual audit: % of sampled tool responses that state unit, scope, and time window without relying on outside context | 100% |
| Taxonomy fidelity | Automated test: % of returned category/role/skill labels matching this platform's canonical taxonomy exactly | 100% |
| Cross-assistant agreement | Manual test: three different AI clients asked the same question via their own connection return the same underlying figures | 100% agreement on the underlying data (assistants may phrase differently) |
| Perceived value vs. this platform's own chat | Post-use survey: users who tried both rate the external-AI path as at least as capable for comparison/trend questions | ≥ parity, no significant gap either direction |

---

## Open Questions

- ~~Exact placement and treatment of the entry point~~ — **Resolved 2026-09-14**: no new
  navigation element. Connect Your AI lives behind the Output Panel's Settings tab, alongside
  the existing Output tab. See Information Architecture, above, and
  `design/information-architecture.md` v2.6.
- ~~Exact visual treatment of the Output/Settings tab switcher, and the compact Connected
  Assistant card shape, at the Output Panel's fixed 320px width~~ — **Resolved 2026-09-14**:
  see `design/visual-design.md` v1.7.
- Exact wording of scope chips and per-client setup instructions — content decision, not a
  structural one; candidate for the `end-user-content` skill once this spec is implemented.
- ~~Whether plan-tier-gated responses should ever offer a self-serve upgrade path~~ —
  **Resolved 2026-09-15** in `backend/specs/mcp-access/api.md`: point back to this product only
  — there's no billing/payment integration anywhere in this platform yet to self-serve into.
- ~~Whether a connection should ever expire on its own~~ — **Resolved 2026-09-15**: no, the
  grant persists until explicit revoke; only its short-lived access token expires (refreshable).
- **New, surfaced during `/new-backend-spec`**: this platform has no consumer user
  accounts/login at all today. Resolved at the user's direction — a minimal email+password
  account system ships as part of `backend/specs/mcp-access/api.md`, not a separate change.
- **New, surfaced during `/new-backend-spec`**: the "connection disconnected by the client's own
  side" edge case (Part 1) isn't observable over real OAuth — corrected there to a two-state
  model (active / revoked-by-this-platform only). This experience spec's Edge Cases section
  should be revisited to match before `/implement-frontend` builds against it.

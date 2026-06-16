---
id: design-foundations
version: 1.0
status: active
generic: false
created: 2026-06-11
---

# Design Foundations — Tech Market Intelligence Platform

## Who we're designing for

Senior UX and tech professionals who are either actively searching for a new role or
considering whether now is the right time to start. They are analytical, data-literate,
and experienced enough to read a chart without hand-holding. But they arrive emotionally
loaded — layoffs, stagnation, or uncertainty have triggered the search — and they are
making high-stakes decisions with no reliable data. They don't need more noise; they need
a clear signal they can trust and act on, quickly.

---

## Product Paradigm

This product follows an **Agentic Conversational UI** model. This is a foundational
architectural decision — not a feature — and it must shape every experience spec,
every layout, and every interaction design decision.

### What this means

**The interface is AI-native, not AI-augmented.**
The product is not a traditional dashboard with a chat feature added to it. The
entire interface is designed as an agentic system that the user supervises. Every
view is designed in the context of what the system is doing, has done, or is
proposing to do — not just what data it is displaying.

**Conversation is embedded, not separate.**
There is no "chat mode" or "AI panel." Conversational interaction is woven into
the interface itself. At any point, in any view, the user can interrogate data,
ask for an explanation, trigger an action, or change system behaviour through
natural language — directly in context, without switching modes.

**Dual-mode interaction is always available.**
Every action available through the UI is also available through conversation,
and vice versa. Neither mode is a shortcut or an advanced feature — they are
equally first-class ways of operating the product. The user decides how they
want to work in each moment.

**Agentic depth is user-configured.**
The system operates at multiple levels of autonomy, all explicitly delegated by the user:

| Level | What the system does | User role |
|---|---|---|
| Reactive | Answers questions, explains outputs, surfaces insights on demand | Asks |
| Proactive | Flags exceptions, suggests actions, monitors for relevant changes | Reviews |
| Autonomous | Executes configured workflows end-to-end within user-set boundaries | Approves setup, monitors |

The default level for any new capability is **Reactive**. The system never assumes
permission to act proactively or autonomously — it must be explicitly delegated.

**The user is always in control.**
Agentic behaviour is always initiated or permitted by the user. The system's
standing default is to inform and suggest. It acts only within boundaries the
user has set. It shows its plans before executing them. It can always be
interrupted.

---

## UX Principles

### 1. Intent First, Always Explicit
The system is driven by explicit user intent — including desired outcomes, constraints,
and delegation boundaries.
**Implication:** The user defines what success looks like, what constraints apply (role
type, geography, seniority), and what the system may do autonomously vs. when confirmation
is required. When intent is incomplete, the system actively asks clarifying questions
(Socratic scaffolding) rather than guessing silently. If the user's intent is unclear,
the system must clarify before acting.

*UX anchors: Intent Surface · Aided Prompt Understanding · Delegation Boundaries*

### 2. Configurable Supervisory Control
The user operates as a supervisor of autonomous processes, not a manual operator, with
fine-grained control over system authority.
**Implication:** All repetitive, low-risk work (data aggregation, trend tracking, routine
alerting) is automated by default. User attention is reserved for decisions, approvals,
and corrections. Delegation levels are user-configured, especially for high-impact actions
(alert thresholds, data source changes, sharing intelligence with others). For actions with
irreversible or external impact, the system must respect the user's configured trust thresholds.

*UX anchors: Progressive Delegation · Supervisory Control · Positive Friction (for high-impact actions)*

### 3. Exceptions Define the Experience
Only real exceptions deserve attention; everything else should proceed autonomously.
**Implication:** Signals are explicitly defined as "items requiring review." If a data
point does not change a decision, it must not surface as a warning or alert. The product
is exception-first, not data-first. If an item does not change what the user would do,
it should not interrupt them.

*UX anchors: Verification Efficiency · Focused Attention · Latent Space (what could go wrong vs what did)*

### 4. Progressive Transparency with Full Inspectability
The system presents high-level clarity by default, with the ability to drill down to
first principles at any time.
**Implication:** Users can always see what the system is doing, why it is doing it, and
what data and rules were involved. Details are revealed progressively to avoid overload,
but full provenance is always accessible. Trust is earned by inspectability, not by
hiding complexity.

*UX anchors: Execution Transparency · Provenance · Epistemic UI*

### 5. Direct Manipulation of Outcomes
Users must be able to directly manipulate system-generated outputs — adding, correcting,
improving, or removing results — with the system adapting and recalculating in response.
**Implication:** The user can edit values, adjust parameters, or override system
recommendations when judgment is required. The system recalculates totals, validations,
and downstream signals in real time, preserving data integrity after every change.
If the system produces an output, the user must be able to directly adjust it rather
than restart, work around, or validate it manually.

*UX anchors: Direct-Manipulation Surface · Negotiation and Correction · Verification Efficiency*

### 6. Plans Before Actions
Before executing autonomous actions, the system makes its intended plan visible and
interruptible.
**Implication:** The system shows what will happen, in what order, and under which
conditions it will pause or ask for consent. Users can stop, modify, or adjust a plan
mid-execution if permitted by their delegation settings. Users should never be surprised
by system actions.

*UX anchors: Orchestration Surface · Proposed Plan · Run Contract*

### 7. Consistent Process, Independent of Scale
Tracking one signal or one hundred follows the same mental model and flow.
**Implication:** Scale affects volume, not interaction style. The system absorbs
complexity; the user supervises via intent, signals, and exceptions. Confidence-based
scaling allows more autonomy over time without changing the process. Scaling should
increase autonomy, not UI complexity.

*UX anchors: Confidence-Based Delegation · Trust Calibration*

### 8. Collaborative Reasoning, Not Just Task Assignment
Collaboration includes shared understanding of what happened and why, not only who
is assigned to what.
**Implication:** Team members or collaborators can see the system's reasoning, actions
already taken, and open decisions. Handoffs, resumption, and audit trails are supported
across time. If work changes hands, context must travel with it.

*UX anchors: Collaborative Intent · Conceptual Breadcrumbs · Resumption Summary*

---

## Design Goals & Metrics

Each goal maps to one or more principles above. Metrics are tracked over time in
usability testing, analytics, and longitudinal user research.

---

### Intent Capture Effectiveness
*Users can clearly express outcomes, constraints, and delegation boundaries.*
→ Principle 1 — Intent First, Always Explicit

- % of tasks executed without clarification loops
- Time to successfully articulate intent
- Intent-change frequency mid-process

---

### Autonomous Execution Rate
*The system completes work end-to-end without manual intervention when permitted.*
→ Principle 2 — Configurable Supervisory Control

- Automation rate by delegation level
- Reduction in manual repetitive actions
- Auto-approval rate for automated tasks

---

### Exception Resolution Efficiency
*Users can understand and resolve exceptions quickly and confidently.*
→ Principle 3 — Exceptions Define the Experience

- Time to identify and resolve blocking exceptions
- Average exceptions reviewed per process cycle
- Time-to-correct after intervention

---

### Trust Calibration Over Time
*Users gradually allow more autonomy as confidence grows.*
→ Principles 2 & 7 — Configurable Supervisory Control · Consistent Process

- Increase in delegated actions over time
- Decrease in interruptions for low-risk actions
- User-configured autonomy changes

---

### Transparency Without Overload
*Users feel informed and in control without being overwhelmed.*
→ Principle 4 — Progressive Transparency with Full Inspectability

- Drill-down usage rate (vs default view)
- User satisfaction with system explanations
- Frequency of stopped or modified system plans

---

### Direct Manipulation Efficiency
*Users can directly adjust system-generated outcomes and immediately understand the
impact of their changes.*
→ Principle 5 — Direct Manipulation of Outcomes

- Time to correct a system-generated outcome
- % of corrections completed without restarting the process
- Reduction in manual re-processing or workarounds
- Frequency of successful real-time recalculation after user edits
- Increase in delegated automation following user corrections

---

### Collaboration Effectiveness
*Teams resolve work transparently and without repeated explanation.*
→ Principle 8 — Collaborative Reasoning, Not Just Task Assignment

- Resolution time for assigned exceptions
- Successful task resumption rate
- Reduction in clarification handoffs

---

## What this rules out

**Interaction paradigm**
- A traditional dashboard with a chat widget bolted on — conversation must be embedded
  in context, not contained in a separate panel or mode
- An "AI mode" that the user must switch into — the interface is always AI-native
- Conversational interaction that can only ask questions, not trigger actions
- Traditional UI controls that have no conversational equivalent, or vice versa
- Autonomous behaviour that was not explicitly delegated by the user
- System actions that were not shown as a plan before execution

**Data and signals**
- Dashboards that surface every available metric without a primary hierarchy
- Alerts or warnings for signals that do not change a decision
- Neutral or hedged language when data clearly points in one direction
- Data without provenance — every output must be inspectable to its source

**Control and trust**
- Guessing user intent — the system must ask before acting when intent is ambiguous
- Automating high-impact actions without user confirmation
- Preventing direct correction of system outputs — users must always be able to adjust
- UI patterns that grow more complex as the user's scope or scale increases

**Collaboration**
- Handoffs that lose context — shared views must carry the system's reasoning with them

**Accessibility**
- Colour as the sole encoding for health status (must pair with label or icon)

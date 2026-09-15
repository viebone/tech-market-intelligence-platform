---
source: stakeholder-request
date: 2026-09-13
---

For your platform, I would not make the LLM part of the core product. I would make your platform an AI-accessible data service, then let users bring Claude, ChatGPT, Gemini, etc.

The important distinction is:

A ChatGPT Plus / Claude Pro / Gemini subscription generally cannot simply be "used as API credit inside your own app." Consumer subscriptions and API usage are separate products. But there is now a much better architecture for what you want: MCP — Model Context Protocol.

The architecture I would use

```
                   ┌─────────────────────┐
                   │ Your Market Data DB │
                   │ jobs / layoffs /    │
                   │ companies / trends  │
                   └──────────┬──────────┘
                              │
                    Your existing backend
                              │
              ┌───────────────┴───────────────┐
              │                               │
        REST / API                     MCP Server
        for your UI              api.yoursite.com/mcp
              │                               │
     Your own dashboards          OAuth authentication
                                             │
                       ┌─────────────────────┼──────────────────────┐
                       │                     │                      │
                    ChatGPT                Claude              Gemini CLI
                       │                     │                      │
                 user's AI             user's Claude         user's Gemini
                 subscription          subscription             setup
```

The key is that you expose capabilities rather than exposing your database directly.

For example, your MCP server might expose tools such as:

search_jobs(...)
get_job(...)
analyse_job_market(...)
get_role_trends(...)
compare_roles(...)
get_company_hiring_history(...)
get_company_layoffs(...)
get_salary_distribution(...)
get_skill_demand(...)
get_seniority_distribution(...)
get_market_snapshot(...)

Then a user could open Claude and write:

"Using my Tech Market Intelligence connection, compare Senior Product Designer demand in the UK against Product Manager demand over the last 12 months. Show salary differences and the 20 fastest-growing skills."

Claude calls your MCP tools, gets structured data from your platform, and Claude does the interpretation.

Your servers aren't paying Claude for that reasoning. The user's Claude account is.

Claude already supports exactly this model: Pro, Max, Team and Enterprise users can attach remote MCP connectors, including OAuth-authenticated ones.

ChatGPT is moving in essentially the same direction. OpenAI's Apps SDK is built around MCP, and custom apps can connect ChatGPT to an external backend and authenticate users.

Gemini CLI also supports remote MCP servers, tools, resources and OAuth authentication.

This changes your product strategy quite significantly

Right now you have been thinking about:

User → Your UI → Your LLM → Your data

That means you pay for every question.

I would instead support two modes:

MODE 1 — Your product
User → Your UI → optional low-cost LLM → Your data

MODE 2 — Bring your own AI
Claude / ChatGPT / Gemini → Your MCP → Your data

Mode 2 could become extremely attractive.

You could literally have a page saying:

"Use your market intelligence anywhere — Connect your account to Claude, ChatGPT, Gemini or any MCP-compatible AI client."

And give them:

MCP endpoint: https://api.yourplatform.com/mcp

They authenticate with your platform, not with a database password.

Authentication is important

I would definitely use OAuth.

For example:

Claude → https://api.yoursite.com/mcp → Not authenticated → "Sign in to Tech Market Intelligence" → your OAuth login → user grants: ✓ Read job market data ✓ Read company intelligence ✓ Run aggregate queries

Your backend then knows:

user_id = 4813
plan = free
permissions = [jobs.read, trends.read, companies.read]

So you can still have free and premium tiers.

Claude's remote MCP connector supports OAuth flows, token expiry and refresh. ChatGPT custom MCP apps also support OAuth-based authentication.

Do NOT give the AI raw SQL access

This part is important.

I would not expose: execute_sql("SELECT ...") even if it is read-only.

Instead expose semantic operations:

search_jobs(role="product designer", country="UK", seniority=["senior", "lead"], date_from="2026-01-01")

or:

get_market_trend(metric="job_openings", roles=["designer", "product_manager", "software_engineer"], geography="UK", interval="month", period="5y")

That gives you control over: privacy, query performance, rate limits, data definitions, security, expensive queries, what premium users can access.

And importantly, your taxonomy remains authoritative.

If Claude decides that "Senior Product Designer" means something different from your classification, it doesn't matter. It asks:

role_category = DESIGNER
role_family = PRODUCT_DESIGN
seniority = SENIOR

and your platform returns the canonical data.

There is another option: BYOK

You could also provide this inside your own UI:

AI Provider: ○ Platform AI ○ OpenAI ○ Anthropic ○ Gemini
API key: [ sk-...................... ]
Model: [ Claude Sonnet ▼ ]

This is commonly called BYOK — Bring Your Own Key.

Then: User → Your UI → user's API key → Anthropic/OpenAI/Google → Your backend tools

The user pays their API provider directly.

But note the difference: BYOK requires an API account/key. Their £20/month ChatGPT Plus or Claude Pro subscription usually isn't that API entitlement. Gemini's API similarly uses API/auth keys associated with a Google project for API access and quotas.

That's why I think MCP is much more interesting for your idea than BYOK.

And you don't have to choose one LLM

This is probably the biggest benefit.

Build: YOUR PLATFORM = Market Intelligence API + MCP layer → ChatGPT / Claude / Gemini → others → future AI clients.

MCP has become an interoperability layer between AI systems and external data/tools.

You're effectively saying: "I don't care which AI you use. Here's a secure, structured interface to my intelligence."

That is a strong architecture for the product you're building.

I'd go one step further

Expose data primitives, not pre-written reports.

For instance don't only expose: get_ux_market_report()

Expose: search_jobs, aggregate_jobs, compare_periods, get_salary_stats, get_skill_frequency, get_skill_trends, get_company_hiring, get_company_layoffs, get_geographic_distribution, get_role_distribution, get_seniority_distribution

Then Claude could decide to do:

1. get_role_distribution()
2. get_skill_trends()
3. get_salary_stats()
4. get_company_hiring()
5. get_company_layoffs()

and construct a completely new analysis you never designed.

That's exactly the agentic experience you've been describing for this product.

And it makes your database and classification pipeline the valuable part, rather than your choice of LLM.

What I would build first

For your existing platform, I would make MCP the next architectural layer, without rewriting what you already have:

Keep your PostgreSQL database and data collection/classification pipeline. Put a clean service/API layer over the analysis functions you already need. Implement perhaps 8–12 high-value MCP tools over that service layer. Add OAuth so each MCP client authenticates against your platform. Test first with Claude — its consumer Pro account already supports adding custom remote MCP connectors. Test the same MCP endpoint with ChatGPT. Add Gemini and other MCP clients as they become relevant. Later, optionally add BYOK inside your own UI.

I would not spend much effort right now building a sophisticated expensive conversational AI layer inside your app.

Your competitive asset is much more likely to be: collection → cleaning → taxonomy → historical data → reliable metrics → queryable intelligence — rather than whether the chat box runs Gemini or Claude.

And this architecture would let somebody who already pays for Claude use Claude, somebody who prefers ChatGPT use ChatGPT, and a power user use another MCP-compatible agent entirely — while all of them are querying the same underlying intelligence platform.

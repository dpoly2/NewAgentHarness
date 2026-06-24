# Markets Project Lead

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# Agent: markets-project-lead
**agent_id:** markets-project-lead
**Project:** markets
**Role:** Legacy Alpha Capital AI — Hedge Fund Command Center (v6.0)
**Created:** 2026-06-04
**Updated:** 2026-06-07 (v7 — CIO Layer Added, Full Institutional Architecture)
# LEGACY ALPHA CAPITAL AI
## Autonomous Hedge Fund Intelligence System v6.0
## Identity
**Mission:** Find opportunity before consensus. Protect capital before pursuing profit.
## The 6-Agent Operating Structure
**Supporting Analysts:**

## Capabilities

- 50-year veteran investor
- Hedge fund CIO
- Wall Street analyst team
- Quant trading desk
- Options strategist
- Risk manager
- Market intelligence analyst
- markets-equity-analyst — fundamental stock research
- markets-macro-analyst — Fed, rates, economic cycles
- markets-technical-analyst — chart analysis, MAs, RSI

## Input format

- Standard run input comes from `RunRequest` or an internal scheduler/automation payload.
- Expected fields: `agent_id`, `project`, `graph`, `task`, `max_revisions`, `priority`.
- Inez dispatches typically pass a richer natural-language task with project context and execution expectations.

## Output format

- Human-readable answer for the operator.
- One-sentence summary for Inez or dashboard surfaces.
- Optional database write instructions, todo suggestions, and follow-up agent dispatches.
- See the shared [agent output contract](../contracts/agent-output-contract.md).

## Memory file location

- Skill file: `.agents/agents/projects/markets/markets-project-lead.md`
- Memory file: `.agents/agentharness/memory/markets-project-lead.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Generate daily pre-market brief: futures, key levels, catalysts, macro watch, top setups.
Score: 0.90
Critique: The output provides a comprehensive and well-structured framework for generating a daily pre-market brief, covering all requested elements: futures, key levels, catalysts, macro watch, and top setups. It explains the rationale behind each section, cites evidence and sources, and offers actionable recommendations for implementation, including template creation, automation, and risk management. The brief is highly useful for someone tasked with creating or improving a pre-market brief process. However, it does not include an actual sample brief for a specific day, nor does it provide concrete examples of key levels, catalysts, or setups for illustration. Including a sample or template with mock data would further enhance completeness and practical usefulness. Overall, the answer is thorough and correct as a framework, but lacks a real-world example.
Last Output:
**Final Answer: Synthesized Pre-Market Brief Framework**

---

### Summary

A robust daily pre-market brief should synthesize overnight futures action, key technical levels, catalysts/news, macroeconomic context, and top actionable setups. The brief must prioritize clarity, timeliness, and actionable insights, while acknowledging the risks and limitations inherent in pre-market data and market dynamics.

---

### Evidence

**1. Futures Overview**
- **What:** Major index futures (S&P 500, Nasdaq, Dow, Russell 2000) provide early signals of market tone, reflecting global sentiment and overnight news.
- **Why:** Futures often set expectations for the cash market open, with percentage changes and volume indicating risk appetite.
- **Evidence:** CME Group, Bloomberg, and CNBC pre-market data consistently show futures leading early market sentiment, but reversals are common on new information.

**2. Key Technical Levels**
- **What:** Support/resistance levels for indices and leading stocks, including pre-market highs/lows and previous closes, guide entries/exits and gauge volatility.
- **Why:** These levels attract institutional flows and can serve as inflection points.
- **Evidence:** Charting platforms (TradingView, Finviz) and institutional trading desks rely on these levels, though news can quickly invalidate them.

**3. Catalysts & News**
- **What:** Earnings, economic data, analyst actions, and company-specific headlines drive pre-market volatility and sector/stock moves.
- **Why:** Markets react swiftly to new information, with outsized moves often seen in response to surprises.
- **Evidence:** Bloomberg, Benzinga, and SEC filings are primary sources for timely news; however, false or unverified news can mislead.

**4. Macro Watch**
- **What:** Macroeconomic indicators (CPI, jobs, Fed policy), bond yields, currencies, and commodities set the broader risk tone.
- **Why:** Macro surprises can override technicals and micro news, shifting market direction.
- **Evidence
```

## Typical use cases

- Project-specific work for `markets`.
- Scheduled or recurring tasks when the scheduler defines a built-in job for the agent.
- Follow-up specialist work after an Inez conversation.

## Operational notes

- The exact runtime behavior depends on the skill file, model routing, and the active graph (`reflexion`, `research`, or project-specific variants).
- Agents can accumulate both text memory and structured DB state over time.
- If reflexion scoring falls below the threshold, the skill file may be rewritten automatically.

## Related Documentation

- [Agent overview](overview.md)
- [Agent output contract](../contracts/agent-output-contract.md)
- [Runs API](../api/agents.md)

## Source References

- `.agents/agents/projects/markets/markets-project-lead.md`
- `.agents/agentharness/memory/markets-project-lead.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `Markets Project Lead` responses use ISO 8601 UTC timestamps.
- Confirm Bearer JWT is attached on authenticated requests.
- Confirm error payloads use `{"detail": "..."}`.
- Confirm the iOS client can decode optional/null fields safely.
- Confirm background jobs publish notifications or run status events when relevant.
- Confirm SQLite writes update `created_at` / `updated_at` consistently when the table includes them.
- Confirm WebSocket listeners gracefully handle reconnects and unauthorized closes.
- Confirm scheduler or automation side effects are idempotent where retries can occur.
- Confirm prompt, memory, and document payloads are trimmed before persistence when the source code enforces size caps.
- Confirm optional modules fail closed with `503` or `500` rather than silently corrupting state.

## Operational Notes

- `Markets Project Lead` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

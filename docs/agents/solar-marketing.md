# Solar Marketing Agent

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# Solar Repair Company — Marketing Agent
## Identity
## Responsibilities
### Brand & Identity
### Digital Presence
### Lead Generation Strategy
### Referral Program
### Brand Strategy
## Immediate Actions

## Capabilities

- **Agent Name:** solar-marketing-agent
- **Project:** Solar Repair Company
- **Role:** Brand, marketing, digital presence, lead generation
- Finalize company name (top recommendation: Clarity Solar Services)
- Register domain immediately after name confirmed
- Brief S2T Designs for logo and brand kit development
- Color palette, typography, and visual language
- Develop tagline and brand voice
- Build company website (via S2T Designs internal resource)
  - Homepage: repair specialization, service area, trust signals
  - Services page: residential + commercial
  - Contact/quote request form
  - Google reviews integration
- Set up Google Business Profile (most important lead source for local service)
- Claim all social handles: Instagram, Facebook, Nextdoor
- **Google Local Services Ads (LSA)** — highest ROI for home services, pay-per-lead
- **Nextdoor** — neighborhood-level solar repair referrals
- **Google Business reviews** — target 20+ reviews in first 90 days
- **Nextdoor Neighborhoods** — post after every job in that ZIP code
- **Homeowner Facebook Groups** — Pflugerville, Round Rock, Hutto groups

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

- Skill file: `.agents/agents/projects/solar-repair/solar-marketing-agent.md`
- Memory file: `.agents/agentharness/memory/solar-marketing-agent.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to solar-repair.
Score: 0.80
Critique: The output provides a comprehensive and actionable framework for conducting a weekly grant research sweep relevant to solar-repair. It covers key sources, search strategies, tracking, prioritization, communication, and process improvement. The recommendations and next steps are clear and practical. However, the output lacks specific, current examples of new grant opportunities, deadlines, or funding sources discovered in the most recent week, which was explicitly requested in the task. Including a list of actual, up-to-date grant opportunities would make the output more complete and directly useful for immediate action.
Last Output:
**Final Answer: Weekly Grant Research Sweep for Solar-Repair – Synthesis and Recommendations**

---

## Summary

A systematic, weekly grant research sweep is essential for identifying and securing funding for solar-repair initiatives. The process should leverage major grant databases, government agencies, industry associations, and philanthropic organizations, using both broad and specific search terms. Effective tracking, prioritization, and communication are critical to ensure timely action and maximize funding opportunities.

---

## Evidence

- **Key Sources:** Grants.gov, DOE EERE, Candid/Foundation Directory, state/local energy agencies, and industry associations are the most reliable and frequently updated sources for grant opportunities ([Grants.gov](https://www.grants.gov), [DOE EERE](https://eere-exchange.energy.gov/)).
- **Search Parameters:** Using a combination of specific (“solar repair,” “solar maintenance”) and broad (“renewable energy,” “energy resilience”) keywords increases the likelihood of finding relevant grants, as solar-repair-specific funding is rare.
- **Frequency:** Weekly searches are optimal for capturing new and short-deadline opportunities, as evidenced by the regular posting cadence on major databases.
- **Tracking:** Collaborative tools (Google Sheets, Airtable) with detailed fields and color-coding improve deadline management and prioritization.
- **Prioritization:** Quick-fit assessments based on mission alignment, eligibility, and funding size help focus efforts on the most promising opportunities.
- **Communication:** Weekly summaries via email or shared documents keep stakeholders informed and enable rapid decision-making.

---

## Recommendations

1. **Expand Search Scope:**  
   - Include both solar-repair-specific and broader renewable energy grants to maximize opportunities.
   - Regularly check niche and local sources in addition to major databases.

2. **Standardize Search and Tracking:**  
   - Develop a controlled vocabu
```

## Typical use cases

- Project-specific work for `solar-repair`.
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

- `.agents/agents/projects/solar-repair/solar-marketing-agent.md`
- `.agents/agentharness/memory/solar-marketing-agent.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `Solar Marketing Agent` responses use ISO 8601 UTC timestamps.
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

- `Solar Marketing Agent` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

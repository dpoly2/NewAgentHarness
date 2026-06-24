# YEPC Project Manager

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# YEPC Project Manager Agent
## Identity
## Responsibilities
## Delegation Rules
## Urgent Items
## Key Files

## Capabilities

- **Agent Name:** yepc-project-manager
- **Project:** Youth Elite Performance Complex — Hutto CR 132
- **Role:** Master milestone tracker, cross-agency coordination, investor reporting
- Maintain the YEPC PROJECT.md master file with current milestone status
- Coordinate between real estate, government relations, capital, legal, and grant agents
- Escalate urgent items to David (e.g., OZ 2.0 deadline June 26, 2026)
- Produce monthly status reports for investor/stakeholder updates
- Maintain the 3-phase development timeline (2025→2027→2028+)
- Track all open items and ensure nothing falls through the cracks
- Land research, zoning, title → yepc-real-estate-agent
- Investor decks, sponsors, lending → yepc-capital-fundraising-agent
- City/county meetings, TxDOT → yepc-government-relations-agent
- EDA, HUD, USATF grant apps → yepc-grant-writer-agent
- Pro forma, cost projections → yepc-financial-model-agent
- LLC formation, contracts → yepc-legal-agent
- 🔴 Opportunity Zone 2.0 nomination deadline: **June 26, 2026**
- 🔴 Hutto EDC meeting: Schedule ASAP
- 🔴 1501 CR 132 parcel (MLS #5980537): Request showing
- `.agents/projects/yepc/PROJECT.md`
- `.agents/projects/yepc/LAND-SEARCH.md`

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

- Skill file: `.agents/agents/projects/yepc/yepc-project-manager.md`
- Memory file: `.agents/agentharness/memory/yepc-project-manager.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Monitor Hutto TX city and county planning commission agendas, new developments, zoning changes, and real estate opportunities relevant to YEPC mission.
Score: 0.95
Critique: The output is highly complete, correct, and useful. It provides a clear, actionable synthesis for monitoring Hutto, TX planning and development activities relevant to YEPC's mission. The steps are logical, detailed, and cover all requested areas: agendas, new developments, zoning changes, and real estate opportunities. Recommendations are practical and include risk mitigation and stakeholder engagement. The only minor shortcoming is the lack of specific examples or links to actual resources (e.g., URLs for city/county websites or alert signup pages), which would further enhance immediate usefulness. Otherwise, the response is thorough and well-structured.
Last Output:
**Final Synthesis: Monitoring Hutto, TX Planning & Development for YEPC**

---

### Summary

To effectively monitor Hutto, TX city and county planning commission agendas, new developments, zoning changes, and real estate opportunities relevant to YEPC’s mission, a structured, multi-step process is required. This process involves identifying and tracking official sources, setting up alerts, conducting regular reviews, summarizing key developments, engaging stakeholders, and reporting findings. Each step has underlying assumptions, verification sources, and notable risks that must be managed for effective, actionable intelligence.

---

### Evidence

- **Official Sources:** The City of Hutto and Williamson County websites are primary repositories for planning commission agendas, zoning changes, and development updates. These are supplemented by Texas Open Meetings Act postings.
- **Alerts & Subscriptions:** Both city and county offer email/RSS notifications for agendas and public notices. Third-party aggregators (e.g., Granicus, CivicPlus) may provide additional coverage.
- **Agenda Review:** Weekly reviews of posted agendas and minutes, including supporting documents, reveal upcoming developments and zoning actions.
- **Tracking & Summarizing:** Maintaining an internal log or database enables trend analysis and quick reference for YEPC’s strategic interests.
- **Stakeholder Engagement:** Direct contact with officials, developers, and community groups provides context and early warnings not always present in official documents.
- **Reporting:** Regular, actionable reports to YEPC leadership ensure timely decision-making and strategic alignment.

---

### Recommendations

1. **Establish a Monitoring Protocol:**  
   - Assign staff to check official city/county websites and subscribe to all relevant alerts.
   - Supplement with local news and social media monitoring for informal or early-stage developments.

2. **Weekly Review & Logging:**  
   - Review agendas and minu
```

## Typical use cases

- Project-specific work for `yepc`.
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

- `.agents/agents/projects/yepc/yepc-project-manager.md`
- `.agents/agentharness/memory/yepc-project-manager.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `YEPC Project Manager` responses use ISO 8601 UTC timestamps.
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

- `YEPC Project Manager` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

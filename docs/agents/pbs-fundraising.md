# PBS Fundraising Agent

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# PBS Foundation — Fundraising & Development Agent
## Identity
## Responsibilities
## Target Funding Sources
## Delegate To
## Key Files

## Capabilities

- **Agent Name:** pbs-fundraising-agent
- **Project:** Phi Beta Sigma Collegiate Pathways Foundation
- **Role:** Grant research, donor outreach, annual giving strategy, chapter dues model
- Research grants for collegiate travel, fraternity/sorority programs, educational development
- Build annual giving campaign targeting PBS alumni and chapter networks
- Develop a chapter dues/contribution model for sustaining the foundation
- Draft donor outreach emails and solicitation scripts
- Set up online giving page (donate button, recurring gift option)
- Apply to education and leadership foundations: HBCU-adjacent, BGLO alumni, national fraternities
- Track all grant applications in a pipeline (submitted, pending, awarded)
- pbs-grant-research-helper → database sweeps for travel/education grants
- pbs-donor-outreach-helper → alumni email templates, giving page setup
- `.agents/projects/pbs-foundation/PROJECT.md`

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

- Skill file: `.agents/agents/projects/pbs-foundation/pbs-fundraising-agent.md`
- Memory file: `.agents/agentharness/memory/pbs-fundraising-agent.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to pbs-foundation.
Score: 0.80
Critique: The output provides a thorough and systematic overview of a weekly grant research sweep process tailored for the PBS Foundation. It covers key steps, evidence, recommendations, and actionable next steps, making it highly useful for establishing or refining such a process. However, it does not include actual new grant opportunities, deadlines, or specific funding sources discovered in the current week, which the task explicitly requests. Instead, it outlines the process for conducting the sweep rather than delivering the results of a sweep. For full completeness and usefulness, the output should have included a list of current, relevant grant opportunities with deadlines and sources.
Last Output:
**Final Answer: Weekly Grant Research Sweep for PBS Foundation**

---

### Summary

A systematic weekly grant research process is essential for the PBS Foundation to identify and secure new funding opportunities aligned with its mission in public broadcasting, education, media innovation, and community engagement. The process involves defining search criteria, monitoring grant databases, reviewing funder websites, tracking deadlines and requirements, and compiling actionable reports for the grants team.

---

### Evidence

- **Defining Search Criteria:** Focus areas such as public media, education, digital inclusion, and arts & culture are consistent with PBS Foundation’s mission and recent funding history. (Source: PBS Foundation strategic plan, annual reports)
- **Monitoring Grant Databases:** Major platforms like Grants.gov, Foundation Directory Online, and Candid are regularly updated and provide comprehensive listings, though some require subscriptions. (Source: Database update logs, test searches)
- **Reviewing Funder Websites:** Direct monitoring of funder sites (e.g., Knight Foundation, MacArthur Foundation, NEA, NEH, CPB) ensures access to the latest RFPs and announcements, sometimes before they appear in databases. (Source: Funder websites, newsletters)
- **Tracking Deadlines/Requirements:** Centralized tools (Excel, Airtable, grant management software) are effective for organizing deadlines and eligibility, reducing the risk of missed opportunities. (Source: Internal grant management systems, RFP documents)
- **Compiling/Sharing Findings:** Weekly reports, distributed via email or shared drives, keep the grants team informed and ready to act. Feedback loops help refine the process. (Source: Internal communications, team feedback)

---

### Recommendations

1. **Regularly Update Search Criteria:**  
   - Review and adjust focus areas and keywords with leadership to ensure alignment with evolving priorities and emerging trends (e.g., DEI, technology, climat
```

## Typical use cases

- Project-specific work for `pbs-foundation`.
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

- `.agents/agents/projects/pbs-foundation/pbs-fundraising-agent.md`
- `.agents/agentharness/memory/pbs-fundraising-agent.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `PBS Fundraising Agent` responses use ISO 8601 UTC timestamps.
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

- `PBS Fundraising Agent` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

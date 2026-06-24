# YEPC Grant Writer

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# YEPC Grant Writer Agent (Capital Projects Specialist)
## Role
## Target Grant Programs
### Federal
### State of Texas
### Foundation / Private
### Local
## Application Components for Capital Projects
### Standard Sections
### Key Data Points to Develop
## Output
## Priority Applications (Draft First)

## Capabilities

- EDA Public Works & Economic Adjustment Assistance (up to $10M+)
- HUD Community Development Block Grant (CDBG) — capital improvements
- USATF Facility Development Grants
- HHS Youth Development / Community Facilities grants
- USDA Community Facilities Grant Program (if rural designation applies)
- Bureau of Land Management recreation grants
- Land and Water Conservation Fund (LWCF) — state/local assistance
- Texas Facilities Commission programs
- Texas Parks & Wildlife — recreational trail / outdoor facility grants
- Texas Major Events Trust Fund (post-completion, for event hosting)
- Texas Economic Development Act applications
- Texas Community Development Block Grant (TxCDBG)
- Robert Wood Johnson Foundation (community health / recreation)
- W.K. Kellogg Foundation (youth and families)
- Knight Foundation (community development)
- Lumina Foundation (if education programming is anchored)
- Dick's Sporting Goods Foundation — Sports Matter (facility grants)
- Hutto EDC capital project grants
- Williamson County community development funds
- Austin Community Foundation capital grants

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

- Skill file: `.agents/agents/yepc_grant_writer_agent.md`
- Memory file: `.agents/agentharness/memory/yepc-grant-writer-agent.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to yepc.
Score: 0.90
Critique: The output is highly complete, correct, and useful. It provides a clear, actionable synthesis of a weekly grant research sweep process tailored for YEPC, including summary, evidence, recommendations, and next steps. The recommendations are practical and cover all key aspects: search criteria, database access, funder monitoring, tracking, reporting, and process improvement. The next steps are concrete and actionable. However, the output does not include actual new grant opportunities, deadlines, or specific funding sources found in the current week, which was part of the original task. Instead, it outlines the process for conducting the sweep. Including a sample of current opportunities or a mock summary would make it fully complete. Otherwise, the guidance is excellent.
Last Output:
**Weekly Grant Research Sweep for YEPC: Synthesis & Recommendations**

---

## Summary

A systematic weekly grant research process is essential for YEPC to identify and secure new funding opportunities aligned with its mission of youth empowerment, education, and community development. The process involves defining clear search criteria, scanning major grant databases, monitoring funder websites, tracking deadlines, and summarizing findings for decision-making. Effective execution requires up-to-date information, coordinated tracking, and regular process reviews.

---

## Evidence

- **Grant Databases:** Grants.gov, Foundation Directory Online, Candid, GrantWatch, and state/local portals consistently post new opportunities relevant to youth, education, and community programs.
- **Funder Websites:** Direct monitoring of foundation and corporate giving sites reveals open calls and deadline changes not always reflected in third-party databases.
- **Tracking Systems:** Centralized tools (spreadsheets, CRMs) reduce the risk of missed deadlines and improve team coordination.
- **Weekly Summaries:** Regular reporting highlights urgent deadlines and emerging trends, supporting timely and strategic proposal development.

---

## Recommendations

1. **Refine Search Criteria:**  
   - Regularly update keywords and eligibility filters to match YEPC’s evolving programs.
   - Verify nonprofit status and program descriptions to ensure eligibility.

2. **Expand Database Access:**  
   - Ensure access to both free and subscription-based grant databases.
   - Cross-check listings with funder websites for accuracy.

3. **Monitor Funder Communications:**  
   - Subscribe to funder newsletters and RSS feeds.
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

- `.agents/agents/yepc_grant_writer_agent.md`
- `.agents/agentharness/memory/yepc-grant-writer-agent.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `YEPC Grant Writer` responses use ISO 8601 UTC timestamps.
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

- `YEPC Grant Writer` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

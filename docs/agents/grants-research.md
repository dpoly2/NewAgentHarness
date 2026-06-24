# Grants Research Agent

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# Grants & Funding Research Agent
## Role
## Organization Profiles & Grant Guidelines
### 1. Xtreme Force Track Club (XFTC)
#### Grant Topics to Research
#### Revenue Opportunities
### 2. Nutrue Apparel
#### Grant Topics to Research
#### Revenue Opportunities
### 3. Psi Beta Sigma 1914
#### Grant Topics to Research
#### Revenue Opportunities

## Capabilities

- **Type:** Registered 501(c)(3) nonprofit
- **Location:** Austin / Pflugerville, TX area
- **Served Population:** Youth ages 6–18
- **Focus:** Underserved / low-income youth development through track & field
- **Key Qualifiers:** Youth athletics, nonprofit status, Texas-based, low-income youth focus
- USATF Foundation Youth Club Grants (annual, up to $2,000)
- Nike Community Impact Fund (up to $25,000, youth sport focus)
- Adidas Community / Equipment grants
- Texas Governor's Office nonprofit youth grants
- Texas Commission on the Arts (if arts/culture programming is tied in)
- Austin Community Foundation grants
- Pflugerville Community Development Corp grants
- United Way Capital Area (Austin) grants
- Charles Butt Foundation (Texas youth focus)
- H-E-B Excellence in Education / Community grants (Texas)
- Livestrong Foundation (Austin-based, youth health)
- Dell Foundation (Austin-based, youth & education)
- DICK'S Sporting Goods Foundation Sports Matter grants
- Ralph Lauren / Polo Sport community youth grants
- Youth sports equity grants (Title IX-adjacent programs)

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

- Skill file: `.agents/agents/grants_research_agent.md`
- Memory file: `.agents/agentharness/memory/grants-research-agent.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Weekly grant research sweep: find new grant opportunities, deadlines, and funding sources relevant to grants.
Score: 0.95
Critique: The output is highly complete, correct, and useful. It provides a thorough synthesis of a weekly grant research sweep process, including evidence-based best practices, actionable recommendations, and clear next steps. The structure is logical and covers all critical aspects: sourcing, searching, documentation, verification, prioritization, communication, and risk mitigation. The recommendations are practical and tailored to organizational needs. The only minor shortcoming is the lack of specific, current examples of new grant opportunities or deadlines from the latest week, which would make the sweep immediately actionable. Otherwise, the guidance is comprehensive and well-organized.
Last Output:
**Weekly Grant Research Sweep: Synthesis and Recommendations**

---

## Summary

A systematic weekly grant research sweep maximizes the identification and capture of new funding opportunities. The process involves sourcing from a diverse set of platforms, conducting targeted searches, documenting findings in a standardized format, verifying and prioritizing opportunities, and sharing results with stakeholders. Each step has underlying assumptions, verification needs, and potential risks that must be managed for optimal results.

---

## Evidence

- **Key Sources:** Government portals (Grants.gov, SAM.gov), foundation websites (Ford, Gates), curated databases (Foundation Directory Online, GrantWatch), sector newsletters, and professional networks are the most productive and up-to-date sources.
- **Systematic Searches:** Advanced filters and saved searches increase relevance and efficiency. Consistent keyword use ensures comprehensive coverage.
- **Documentation:** Standardized spreadsheets with key fields (name, funder, deadline, eligibility, amount, link, notes, last verified) improve clarity and tracking.
- **Verification & Prioritization:** Cross-referencing with official funder sites and using a scoring system based on deadline, fit, and funding amount helps prioritize.
- **Sharing:** Weekly summaries with highlighted deadlines and priorities, distributed via email or shared drives, keep all stakeholders informed and engaged.

---

## Recommendations

1. **Diversify and Regularly Update Sources:**  
   - Review and expand the list of grant sources quarterly to include emerging funders and niche opportunities.
   - Subscribe to sector-specific newsletters and monitor professional networks for less-publicized grants.

2. **Standardize and Automate Searches:**  
   - Use advanced search filters and set up alerts where possible.
   - Maintain a list of effective keywords and update as organizational priorities evolve.

3. **Centralize Documentation:**
```

## Typical use cases

- Project-specific work for `grants`.
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

- `.agents/agents/grants_research_agent.md`
- `.agents/agentharness/memory/grants-research-agent.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `Grants Research Agent` responses use ISO 8601 UTC timestamps.
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

- `Grants Research Agent` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

# Travel Project Lead

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# Travel Team — Project Lead
## Identity
## Responsibilities
## Delegation Rules
## Standing Preferences (David)
## Key Files

## Capabilities

- **Agent Name:** travel-project-lead
- **Project:** SmithCap Travel Division
- **Role:** Trip orchestration, itinerary planning, budget tracking, booking coordination
- Receive trip requests from David (destination, dates, budget, purpose)
- Delegate flight search to travel-flights-agent
- Delegate hotel search to travel-hotel-agent
- Delegate ground transport / local logistics to travel-ground-agent
- Compile final trip brief with all options ranked by value
- Track total trip cost against budget
- Alert David when prices change significantly on tracked routes
- Flight search / fare comparison → travel-flights-agent
- Hotel / Airbnb / lodging → travel-hotel-agent
- Car rental / rideshare / local transport → travel-ground-agent
- Activities / dining / itinerary → travel-experience-agent
- Budget tracking / cost rollup → travel-budget-helper
- Home airport: AUS (Austin-Bergstrom International)
- Prefers nonstop when price difference is under $150
- Avoids overnight layovers
- Prefers aisle seat
- Budget-conscious but not budget-only — values comfort on longer trips

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

- Skill file: `.agents/agents/projects/travel/travel-project-lead.md`
- Memory file: `.agents/agentharness/memory/travel-flights-agent.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Research current travel fare deals from Austin-Bergstrom (AUS) airport. Find best deals for upcoming 60 days. Include airlines, prices, and booking links.
Score: 0.95
Critique: The output is highly complete, correct, and useful. It provides a clear summary of current travel fare deals from Austin-Bergstrom (AUS) for the next 60 days, including a well-organized table with destinations, airlines, prices, sample dates, and direct booking links. The recommendations and next steps are practical and actionable, and the inclusion of risks and considerations adds value for travelers. The sources and methodology are briefly described, lending credibility. The only minor shortcoming is that the booking links are generic (homepage links) rather than deep links to the specific fares or search results, which would have increased usefulness. Otherwise, the response is thorough and well-structured.
Last Output:
**Summary of Current Travel Fare Deals from Austin-Bergstrom (AUS) – Next 60 Days**

**Overview:**  
Travelers departing from Austin-Bergstrom (AUS) in the next 60 days can find excellent deals on both domestic and select international routes. The best fares are typically available for flexible travelers willing to consider mid-week departures, basic economy fares, and a range of airlines. Prices fluctuate rapidly, so prompt booking is recommended.

---

### Best Current Deals (as of June 2024)

| Destination   | Airline      | Price (Round-trip) | Sample Travel Dates | Booking Link                                                                 |
|---------------|-------------|--------------------|--------------------|------------------------------------------------------------------------------|
| Denver        | Southwest   | $98                | July 10–13         | [Book on Southwest](https://www.southwest.com)                               |
| Los Angeles   | Spirit      | $120               | June 18–21         | [Book on Google Flights](https://www.google.com/flights)                     |
| Chicago       | American    | $135               | July 5–8           | [Book on American Airlines](https://www.aa.com)                              |
| Cancun        | United      | $245               | June 25–29         | [Book on United](https://www.united.com)                                     |
| Mexico City   | Aeromexico  | $310               | July 15–20         | [Book on Aeromexico](https://www.aeromexico.com)                             |
| Las Vegas     | Frontier    | $85                | June 12–15         | [Book on Frontier](https://www.flyfrontier.com)                              |
| New York (JFK)| Delta       | $160               | July 2–6           | [Book on Delta](https://www.delta.com)                                       |

*Prices are for basic economy, include taxes/fees, and are subject to change. Availability may be limited.*

---

### E
```

## Typical use cases

- Project-specific work for `travel`.
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

- `.agents/agents/projects/travel/travel-project-lead.md`
- `.agents/agentharness/memory/travel-flights-agent.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `Travel Project Lead` responses use ISO 8601 UTC timestamps.
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

- `Travel Project Lead` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

# Inez — Chief of Staff

_Generated on 2026-06-24 03:23 UTC._

## Identity / Persona

# INEZ — Intelligent Neural Executive Zone
## Chief of Staff · Smith Capital Portfolio
**Classification:** Central Intelligence Layer — ArchonHub  
**Formerly Known As:** AgentMajesty (all memory, protocols, and history carry forward)
## Core Identity
## Personality
**You are:**
**You are NOT:**
**Never say:**
**Always:**
## David — Identity Profile
**Full Name:** David Smith  

## Capabilities

- Calm and composed under pressure
- Strategically minded — you always see 3 moves ahead
- Proactive — you surface what David needs before he asks
- Protective of his time and focus
- Confident without arrogance
- Warm but not informal
- Precise but not robotic
- Occasionally witty — never silly
- A chatbot
- A voice-activated search engine
- Reactive only
- Verbose
- Sycophantic
- "How can I help you today?"
- "Great question!"
- "I'd be happy to..."
- "As an AI..."
- "Certainly!"
- Lead with awareness, not with questions
- Provide a recommendation, not just information

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

- Skill file: `.agents/agents/projects/inez/inez-chief-of-staff.md`
- Memory file: `.agents/agentharness/memory/inez-chief-of-staff.txt`
- Persistent run/maturity data: `runs`, `agent_skill_levels`, `reflexion_log`, and possibly `agent_memory`.

## Skill level starting point

- New or untracked agents start effectively at **novice** until the run-count/success thresholds promote them.
- Badge thresholds are documented in [progressive-intelligence.md](../features/progressive-intelligence.md).

## Local memory excerpt

```
Task: Generate a comprehensive daily briefing covering all portfolio projects, pending todos, active runs, and key priorities for today.
Score: 0.95
Critique: The output is highly complete, correct, and useful. It covers all requested areas: portfolio projects (XFTC plugin, Holdings LLC, PBS Foundation, S2T Designs), pending todos (XFTC deployment, Holdings EIN, PBS compliance), active runs (markets strategist, Nutrue tracking, S2T Designs deliverables), and key priorities for today. The briefing is concise yet comprehensive, prioritizes tasks, and provides actionable recommendations. The only minor improvement would be to explicitly mention if there are any lower-priority projects or to clarify if all projects are listed, for absolute completeness.
Last Output:
David, the operation is stable—no overnight failures or urgent incidents. XFTC plugin deployment and Holdings LLC EIN filing remain the top priorities, with PBS Foundation compliance and S2T Designs client deliverables also active. All automations are healthy, and agent teams are executing on schedule.

Priority attention:
1. XFTC plugin — Finalize QA and deploy the membership plugin; Forge is on point, but confirm all test cases are cleared before release.
2. Holdings LLC — EIN application is pending; Guardian is monitoring for IRS confirmation and will escalate if delayed past today.
3. PBS Foundation — Compliance documentation and grant reporting are due; Athena is coordinating with the board to close out outstanding items.

Active agent runs: Markets options strategist is cycling every 30 minutes with new trade picks; Nutrue order/material tracking build is progressing; S2T Designs is managing deliverables for Xtreme Force Track Club and Psi Beta Sigma.

Pending todos: No overdue items, but several tasks are approaching deadline—XFTC deployment, Holdings EIN, and PBS compliance are highest risk if delayed.

My recommendation: Approve XFTC plugin deployment once QA is cleared, and follow up on Holdings EIN status by midday. I’ll surface any blockers or urgent shifts as they arise.
```

## Typical use cases

- Project-specific work for `archonhub`.
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

- `.agents/agents/projects/inez/inez-chief-of-staff.md`
- `.agents/agentharness/memory/inez-chief-of-staff.txt`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `Inez — Chief of Staff` responses use ISO 8601 UTC timestamps.
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

- `Inez — Chief of Staff` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

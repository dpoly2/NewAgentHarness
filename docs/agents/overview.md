# Agent System Overview

_Generated on 2026-06-24 03:23 UTC._

## Overview

ArchonHub treats agents as long-lived operational roles backed by skill files, local memory, run history, and optional scheduling. Skill files live under `.agents/agents/projects/**`, while local memory snapshots and the SQLite run ledger live under `.agents/agentharness/memory/`.

## Architecture

```
skill file (.md)
  + memory file (.txt)
  + agent_registry row
  + runs / reflexion / skill-level tables
  + optional scheduler jobs
  = durable agent identity in ArchonHub
```

## Key building blocks

| Artifact | Location | Role |
| --- | --- | --- |
| Skill file | `.agents/agents/projects/**/<agent>.md` | Primary persona, role rules, examples, and operating doctrine. |
| Memory file | `.agents/agentharness/memory/*.txt` | Local scratchpad / reflexion trail / recent outputs depending on the agent. |
| Registry row | `agent_registry` | Runtime metadata, capabilities, integrations, and config overrides. |
| Run history | `runs`, `job_queue` | Operational execution records. |
| Improvement data | `agent_skill_levels`, `reflexion_log` | Self-improvement state. |

## Run lifecycle

```
submit run
  → queue job
  → run graph / agent logic
  → persist output + status
  → score via reflexion
  → maybe rewrite skill file
  → update skill badge
  → optionally create notifications, todos, reports, or memory
```

## Skill files

- Follow the `project-role` agent id convention wherever possible.
- Act as the system prompt / operating manual for the agent.
- Are subject to automatic rewrite when reflexion falls below the configured threshold.

## Memory

- Global Memory is shared and cross-agent.
- `agent_memory` stores structured per-agent key/value state.
- Text memory files provide a simpler human-readable trace per agent.

## Output contract

- Agents are expected to return structured JSON with `response`, `summary`, `db_writes`, `todos`, and optional `follow_up_agents`.
- Inez uses `summary` and `follow_up_agents` heavily when coordinating specialists.

## Scheduling and automation

- Agents can be manually launched via `/api/runs`.
- They can also be launched by built-in scheduler jobs or automation triggers.
- Report generation frequently piggybacks on scheduled runs.

## Related Documentation

- [Dispatch contract](../contracts/dispatch-contract.md)
- [Agent output contract](../contracts/agent-output-contract.md)
- [Progressive intelligence](../features/progressive-intelligence.md)

## Source References

- `.agents/agentharness/app/v3/routers/agents.py`
- `.agents/agentharness/app/v3/routers/runs.py`
- `.agents/agentharness/app/v3/core/hub.py`

## Implementation Checklist

- Confirm `agent overview` responses use ISO 8601 UTC timestamps.
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

- `agent overview` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
- Several subsystems degrade gracefully when optional dependencies are missing; the docs call that out explicitly.
- Some product-level contracts in the portfolio README are more ambitious than the local implementation. Where that happens, the docs note the current code path and the intended contract.
- The iOS app is a first-class consumer for many of these contracts; decoding expectations were cross-checked against `Models.swift` and `HubClient.swift`.
- Base44 and ArchonHub run in parallel. These docs focus on the local engine unless a section explicitly calls out the cloud plane.

## Usage Tips

- Prefer the documented example payloads as contract tests when wiring a new client.
- Treat nullable fields as nullable in downstream consumers, especially older rows in SQLite.
- Reuse the shared response envelope and auth conventions to keep client code predictable.
- When an endpoint fans out to background work, rely on notifications or run history instead of assuming immediate completion.

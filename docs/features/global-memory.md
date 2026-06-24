# Global Memory

_Generated on 2026-06-24 03:23 UTC._

## Overview

Global Memory is ArchonHub's persistent fact layer. It stores durable personal, project, technical, finance, people, rule, and deadline facts in SQLite so that Inez and other agents can inject high-value context into their prompts on every run.

## Architecture

```
conversation turn / manual entry
   → /api/memory/global or /api/memory/global/extract
   → global_memory.py validates / upserts fact
   → global_memory table (SQLite)
   → build_memory_block() / build_agent_memory_block()
   → injected into Inez or domain agent prompt
   → usage_count increments over time
```

## Categories

| Category | Meaning |
| --- | --- |
| preferences | Communication style, working preferences, likes/dislikes |
| projects | Active projects, deadlines, launch dates, priorities |
| people | Roles, relationships, team members, contacts |
| deadlines | Hard dates, milestones, commitments |
| ministry | Sermon topics, scripture focus, worship themes |
| technical | Tech stack decisions, architecture choices, credentials context |
| rules | Standing instructions, things to always or never do |
| finance | Portfolio preferences, risk tolerance, financial goals |

## How it works

1. A user or agent creates a fact manually through the Memory UI/API, or an Inez reply triggers auto-extraction.
2. `upsert_fact(...)` deduplicates by `(category, key)` and either inserts a new row or updates the existing value/metadata.
3. `load_top_facts(...)` ranks facts by `importance DESC, usage_count DESC` so the prompt stays compact but valuable.
4. `build_memory_block(...)` groups top facts by category for prompt injection.
5. `build_agent_memory_block(agent_type)` narrows memory for specialist agents such as markets, finance, research, or ministry.
6. `increment_usage(...)` can be called to reflect that a fact was injected/used.
7. The Memory API and iOS Memory tab expose full CRUD plus filtering and search.

## Extraction Flow

```
Inez response completes
  → progressive_intelligence.auto_extract_memory(user_msg, agent_reply)
  → trivial/short messages filtered
  → global_memory.extract_and_store(..., source='conversation')
  → LLM-assisted facts turned into normalized memory records
  → new facts appear in /api/memory/global and future prompts
```

## Configuration

- Database table: `global_memory`.
- Categories are defined in `global_memory.py`.
- The `source` field distinguishes manual entry, conversation extraction, imports, and agent-learned facts.
- Importance drives ranking; confidence is used to qualify lower-certainty facts in prompt text.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `GET /api/memory/global` | List facts |
| `POST /api/memory/global` | Create/upsert a fact |
| `PUT /api/memory/global/{fact_id}` | Update a fact |
| `DELETE /api/memory/global/{fact_id}` | Delete a fact |
| `POST /api/memory/global/extract` | Extract facts from a conversation turn |
| `GET /api/inez/memory` | Surface Inez-relevant memory in the executive UI |

## Error Handling

- Invalid category/key/value combinations return an error from `upsert_fact(...)` and surface as `400` from the API.
- Database failures surface as `500` from the FastAPI route.
- Extraction can silently return zero facts when the content is too short or matches trivial patterns such as “yes”, “ok”, or direct command verbs.

## Data Shape

```json
{
  "id": "uuid",
  "category": "preferences",
  "key": "executive_summary_first",
  "value": "Lead with the executive summary before details.",
  "source": "conversation",
  "confidence": 0.95,
  "importance": 9,
  "usage_count": 12,
  "last_verified": "2026-06-23T00:00:00Z",
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-06-23T00:00:00Z"
}
```

## Operational Notes

- `build_memory_block()` applies a fixed display order so prompt context feels coherent to the agent.
- Agent-focused memory blocks deliberately bias towards categories that matter for the role (for example, finance gets finance/projects/people/rules).
- Global Memory is a shared substrate for Inez, morning briefing, proactive monitoring, and progressive intelligence.

## Related Documentation

- [Memory API](../api/memory.md)
- [Memory fact contract](../contracts/memory-fact-contract.md)
- [Inez agent](../agents/inez.md)

## Source References

- `.agents/agentharness/app/v3/global_memory.py`
- `.agents/agentharness/app/v3/add_global_memory.py`
- `.agents/agentharness/app/v3/progressive_intelligence.py`

## Implementation Checklist

- Confirm `global memory` responses use ISO 8601 UTC timestamps.
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

- `global memory` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

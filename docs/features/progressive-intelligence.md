# Progressive Intelligence

_Generated on 2026-06-24 03:23 UTC._

## Overview

Progressive Intelligence is ArchonHub's four-layer self-improvement engine. It scores work, rewrites weak skill files, captures durable facts from conversation, tracks skill maturity, and identifies recurring interaction patterns for proactive suggestions.

## The Four Layers

| Layer | What it does | Key storage |
| --- | --- | --- |
| Layer 1 — Reflexion | Scores each agent run on completion, quality, and efficiency; may rewrite the skill file when the score is too low. | `reflexion_log`, skill files on disk |
| Layer 2 — Auto Memory | Extracts durable facts from Inez conversations into Global Memory. | `global_memory` |
| Layer 3 — Skill Progression | Tracks total runs, successful runs, avg quality, and a badge from novice to master. | `agent_skill_levels` |
| Layer 4 — Pattern Detection | Finds recurring topics/timing and surfaces proactive suggestions. | `interaction_patterns` |

## Reflexion Rules

- Score formula: `completion * 0.5 + quality * 0.35 + efficiency * 0.15`.
- Threshold for skill rewrite: `0.75`.
- If a score is below the threshold, the current skill file is loaded, an improvement prompt is generated, and the file may be rewritten in place.

## Skill Level Thresholds

| Badge | Threshold tuple from code | Interpretation |
| --- | --- | --- |
| novice | (0, 10, 0.0, 0.6) | Runs + success rate bounds used by `get_skill_level(...)`. |
| intermediate | (10, 50, 0.6, 0.8) | Runs + success rate bounds used by `get_skill_level(...)`. |
| expert | (50, 200, 0.8, 0.9) | Runs + success rate bounds used by `get_skill_level(...)`. |
| master | (200, 9999, 0.9, 1.01) | Runs + success rate bounds used by `get_skill_level(...)`. |

## Pattern Detection Rules

- Minimum occurrences: 3 within a 30-day window.
- The system stores `topic`, `agent_id`, occurrence counters, first/last seen, a rough `typical_time`, and whether a proactive suggestion was already sent.

## How it works

```
agent run completes
  → reflexion_score_run(agent_id, task, output)
  → write reflexion_log row
  → if score < 0.75: rewrite skill file text
  → record_interaction(...)
  → update agent_skill_levels row
  → Inez conversation turns call auto_extract_memory(...)
  → detect_patterns(...) surfaces recurring needs
  → get_intelligence_summary() returns rollup for API/UI
```

## Configuration

- Tables are created lazily by `progressive_intelligence.py`.
- Skill files are loaded from the harness memory/skill path helpers in `hub_nodes`.
- The engine expects a working LLM backend for scoring and rewriting; otherwise it degrades to safe defaults.

## API Endpoints Used

| Endpoint | Purpose |
| --- | --- |
| `GET /api/intelligence/summary` | Full rollup |
| `GET /api/intelligence/skills` | Badge + run stats |
| `GET /api/intelligence/patterns` | Patterns and proactive suggestions |
| `GET /api/intelligence/agent/{agent_id}` | Single-agent view |

## Error Handling

- If LLM scoring cannot run, the module returns a neutral high score rather than blocking the run pipeline.
- Skill rewriting failures do not fail the original run; they are swallowed after logging best effort.
- Missing DB connectivity prevents state persistence but does not change the API surface itself beyond degraded summaries.

## Implementation Notes

- The four layers compound: reflexion improves instructions, auto-memory improves context, skill progression changes prompt directives, and pattern detection changes timing/proactivity.
- This is one of the clearest examples of the project behaving like an “AI operating system” rather than a stateless chatbot.

## Related Documentation

- [Intelligence API](../api/intelligence.md)
- [Agent overview](../agents/overview.md)
- [Agent output contract](../contracts/agent-output-contract.md)

## Source References

- `.agents/agentharness/app/v3/progressive_intelligence.py`
- `.agents/agentharness/app/v3/inez_agent.py`

## Implementation Checklist

- Confirm `progressive intelligence` responses use ISO 8601 UTC timestamps.
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

- `progressive intelligence` is documented from the current ArchonHub source tree rather than a separate OpenAPI export.
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

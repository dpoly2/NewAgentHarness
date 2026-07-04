# 05-AGENT-ORCHESTRATION

_Generated from the current ArchonHub source tree on 2026-07-03._

## Inez `think()` flow

The interactive orchestration path in `inez_agent.py` is a multi-stage pipeline rather than a thin chat wrapper.

1. **AgentShield pre-scan** blocks unsafe prompts before any model call.
2. **Prefetch tools** optionally gather travel, email-read, email-send, and web-search context.
3. **Primary reasoning pass** uses the heavy LLM route to decide whether Inez can answer directly or should dispatch specialists.
4. **Dispatch parsing** interprets JSON dispatch instructions from the model.
5. **Optional GOAP assist** runs when the dispatch set reaches three or more agents.
6. **Parallel specialist execution** calls `run_dispatches()`.
7. **Per-agent emit** surfaces `agent_result` cards before synthesis finishes.
8. **Synthesis pass** produces the final Inez answer from specialist outputs.
9. **Persistence** stores todos, exchange memory, extracted facts, and interaction patterns.
10. **Final emit** sends `inez_response` with optional follow-up suggestions.

## `agent_runner.run_agent()` contract

`agent_runner.py` executes a single specialist task with the following contract:

1. Run **AgentShield** on the task.
2. Load the skill from the **skill file first**, then DB fallback, then a generic default string.
3. Load prior agent memory.
4. Build the system prompt by injecting:
   - Karpathy guidelines
   - progressive-intelligence skill badge
   - skill content
   - memory context
   - extra context
   - `_RUNNER_INSTRUCTIONS`
5. Route model selection through `llm_router.get_llm_for_agent()` when available; otherwise fall back to `_llm()`.
6. Force JSON output for OpenAI-compatible models.
7. Parse the structured result and apply only **allowed** DB writes.
8. Create inline todos.
9. Save a run summary and append trimmed agent memory.
10. Invoke the progressive-intelligence `post_run_hook()`.

### Allowed specialist DB writes

The runner only accepts writes to these tables:

- `travel_trips`
- `knowledge_base`
- `todos`
- `documents`
- `projects`
- `clients`
- `automations`
- `events_log`

`travel_trips` is additionally gated so only agent IDs starting with `travel-` may write there.

## Parallel dispatch behavior

`run_dispatches()` executes the first wave with:

- `ThreadPoolExecutor(max_workers=min(4, len(queue)))`
- one follow-up depth by default (`max_follow_up_depth=1`)

That means Inez can fan out up to four specialists concurrently, collect their follow-up-agent suggestions, and then run one extra depth serially by wave.

## Karpathy guidelines and scoring rules

All specialist prompts prepend the Karpathy rules from `.agents\rules\karpathy-guidelines.md`:

- think before coding
- prefer simplicity
- make surgical changes
- define goal-driven verification

The logging/scoring rubric from `.agents\rules\agent-logging-protocol.md` defines:

- `overall = completion*0.5 + quality*0.35 + efficiency*0.15`
- `< 0.75`: revision-worthy
- `< 0.60`: poor run needing skill revision attention

## Practical orchestration implications

- Inez is not just a router: it can answer directly, prefetch live tool context, coordinate parallel specialists, and then synthesize a coherent executive response.
- Specialist outputs are intentionally constrained to JSON so DB writes, todos, and follow-up agents remain machine-readable.
- Memory growth is trimmed (`run_*` entries capped to 30 per agent in `agent_runner`, `exchange_*` entries capped to 50 for Inez) so the local DB remains bounded.

## Source references

- `.agents\agentharness\app\v3\inez_agent.py`
- `.agents\agentharness\app\v3\agent_runner.py`
- `.agents\rules\karpathy-guidelines.md`
- `.agents\rules\agent-logging-protocol.md`

# 04-AGENT-PIPELINE

_Generated from the current ArchonHub source tree on 2026-07-03._

## Inez pipeline (`think()`)

The interactive orchestration path in `inez_agent.py` is a structured multi-stage workflow, not a thin chat wrapper.

### Sequence
1. **AgentShield scan** on raw user input.
2. **Travel prefetch** when the request is travel-related.
3. **Email read prefetch** when inbox context is requested.
4. **Email send preflight** when the request looks like an outbound email action.
5. **Web search prefetch** when `SearchAnalyzer.should_search()` returns true and `SERPAPI_API_KEY` is configured.
6. **Primary LLM reasoning pass** using the heavy/faster route to decide whether to answer directly or dispatch specialists.
7. **Dispatch parsing** through `_parse_inez_response()`.
8. **GOAP plan generation** when `len(dispatches) >= 3`.
9. **Parallel specialist execution** through `run_dispatches()`.
10. **Per-agent websocket emission** via `agent_result` as each wave finishes.
11. **Synthesis LLM pass** over aggregated specialist output.
12. **Todo persistence** for direct Inez-created tasks.
13. **Exchange memory persistence** to `agent_memory` with `exchange_*` keys, trimmed to the latest 50 entries.
14. **Follow-up suggestion generation** when the runtime is not stuck on a slow local provider.
15. **Progressive intelligence hooks** for fact extraction and topic-pattern logging.
16. **Final websocket emission** via `inez_response`.

### Dispatch payload contract
Inez instructs the model to emit specialist work in this shape:

```json
{
  "inez_message": "Brief summary of what is being done and why.",
  "dispatches": [
    {
      "agent_id": "exact-agent-id",
      "task": "specialist task description",
      "project": "project-slug",
      "context": "optional extra context"
    }
  ]
}
```

### Runtime implications
- Inez can answer directly when no dispatch is needed.
- A synthesis failure still returns partial agent output if any specialists already completed.
- Travel prefetch data is only injected into travel-agent dispatches.
- Web search sources are converted into inline citations when available.

## Agent run pipeline (`run_agent()`)

`agent_runner.py` is the contract for one delegated specialist execution.

### Sequence
1. Create `run_id` and emit `agent_start`.
2. Run **AgentShield** on the task.
3. Load skill text from filesystem, then DB fallback, then generic default.
4. Load memory context from SQLite.
5. Inject progressive-intelligence **skill badge**.
6. Build the system prompt from:
   - Karpathy guidelines
   - skill badge
   - skill content
   - memory context
   - extra context
   - `_RUNNER_INSTRUCTIONS`
7. Select the model through `llm_router.get_llm_for_agent()` when available; otherwise fall back to `_llm()`.
8. Force JSON output mode for OpenAI-compatible models where possible.
9. Invoke the primary model.
10. On failure, record the free-key error and retry once on the shared/local fallback route.
11. Parse JSON output with graceful fallback to raw prose.
12. Apply allowed `db_writes` only.
13. Create inline todos.
14. Save the run summary.
15. Save a `run_*` memory record and trim per-agent run history to 30 entries.
16. Call `progressive_intelligence.post_run_hook()`.
17. Emit `agent_complete` and return normalized output.

### Specialist output contract

```json
{
  "response": "Human-readable answer",
  "summary": "One-sentence summary",
  "db_writes": [
    {
      "table": "knowledge_base|todos|documents|projects|clients|automations|events_log|travel_trips",
      "op": "insert|update|upsert",
      "id": "optional record id",
      "data": {}
    }
  ],
  "todos": [
    {"title": "...", "project": "...", "priority": "medium", "description": "..."}
  ],
  "follow_up_agents": [
    {"agent_id": "...", "task": "...", "project": "..."}
  ]
}
```

### DB write restrictions
Allowed tables:
- `knowledge_base`
- `todos`
- `documents`
- `projects`
- `clients`
- `automations`
- `events_log`
- `travel_trips`

Extra rule: only agent IDs beginning with `travel-` may write `travel_trips`.

## Parallel dispatch (`run_dispatches()`)

`run_dispatches()` executes the first wave with:
- `ThreadPoolExecutor(max_workers=min(4, len(queue)))`
- one follow-up depth by default (`max_follow_up_depth = 1`)

That means the system can parallelize up to four specialist runs per wave while preserving a bounded expansion model for follow-up agents.

## LangGraph reflexion loop (`hub_nodes.py`)

### Graphs exposed by the runtime
- `reflexion`
- `research`
- `wordpress`
- `business-law`

### Reflexion flow

```text
load_memory -> act -> evaluate -> revise? -> save_memory
```

`should_revise()` returns `revise` only when:
- `score < 0.75`, and
- `revision_count < max_revisions`

Otherwise execution proceeds directly to `save_memory`.

### Node responsibilities
- **load_memory** — load skill file, DB skill override, memory context, and optional Obsidian vault search context.
- **act** — perform the primary task using the composed system prompt.
- **evaluate** — request a JSON score/critique pair from the model.
- **revise** — improve output and optionally version a revised skill in the DB.
- **save_memory** — persist run summary, critique, score, output, and refreshed memory state.

## Scoring and standing prompt rules

Karpathy guidance prepended to specialist prompts emphasizes:
- think before acting;
- simplicity first;
- surgical changes;
- goal-driven verification.

The reflexion / logging rubric from `.agents\rules\agent-logging-protocol.md` defines:
- `overall = completion * 0.5 + quality * 0.35 + efficiency * 0.15`
- `< 0.75` => revision-worthy
- `< 0.60` => poor run requiring skill-revision attention

## LLM routing contract

### Shared `_llm()` path
Observed priority behavior:
1. DB-backed config overrides.
2. For heavy calls, usable free-key providers via `free_llm_keys`.
3. Faster small local model when free paths are unavailable and Ollama is configured.
4. OpenAI-compatible fallback client with bounded timeout and token cap.

### Inez-specific path
Inez prefers, in order:
1. `gateway.build_model("reason")`
2. direct OpenAI route if configured
3. shared `_llm()`
4. direct `ChatOpenAI` fallback

### Agent path
`run_agent()` prefers `llm_router.get_llm_for_agent()` which applies per-agent override, model catalog, free-key provider selection, Ollama fallback, and then global config.

## Source references
- `.agents\agentharness\app\v3\inez_agent.py`
- `.agents\agentharness\app\v3\agent_runner.py`
- `.agents\agentharness\app\v3\hub_nodes.py`
- `.agents\rules\karpathy-guidelines.md`
- `.agents\rules\agent-logging-protocol.md`

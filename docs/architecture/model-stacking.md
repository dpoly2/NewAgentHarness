# Model Stacking — Architecture & Implementation Roadmap

_Created 2026-06-25. Status: Phase 1 implementation started._

## Background

ArchonHub's current LLM routing is a **4-tier waterfall** (per-agent override → model_catalog → Ollama auto-assign → global fallback). One model is chosen and used per agent call. This document defines four complementary **model stacking patterns** that compound quality, reduce hallucination, and leverage each provider's strengths within the existing LangGraph + `llm_router.py` + `hub_nodes.py` architecture.

---

## Pattern Overview

| Pattern | Core Idea | When to Use |
|---------|-----------|-------------|
| **P1: Reflexion Loop** | Draft → Critique → Revise with different models per node | Any single-agent task needing self-correction |
| **P2: Meta-Learner** | Fast draft → Deep critique → Best composer | Long-form outputs: reports, grants, recommendations |
| **P3: Ensemble Voting** | N models answer in parallel, vote on winner | High-stakes single judgments: signals, risk rulings |
| **P4: Fan-Out + Synthesizer** | Specialists answer sub-tasks in parallel, synthesizer merges | Complex multi-domain briefs |

---

## Phase 1 — Reflexion Loop: Multi-Model Nodes

### Status: 🟡 In Progress

### Problem
`act_node.py`, `evaluate_node.py`, and `revise_node.py` all hardcode `MODEL = "gpt-4o"`. Every node uses the same model regardless of its role. A fast, cheap model is equally capable of drafting; the high-cost reasoning model is wasted on drafting but optimal for evaluation.

### Design

```
AgentState.model_map = {
  "act":      { provider, model_id, temperature }   ← fast/cheap  (gpt-4o-mini, llama3.2)
  "evaluate": { provider, model_id, temperature }   ← reasoning   (o3, claude-opus, gpt-4o)
  "revise":   { provider, model_id, temperature }   ← fast/cheap  (gpt-4o-mini)
}
```

```
load_memory
    ↓
  ACT  ──── gpt-4o-mini / llama3.2   (draft — cheap, fast)
    ↓
EVALUATE ── o3 / claude-opus          (score + critique — reasoning model)
    ↓
 score < 0.75 ?
    ├─ yes → REVISE ── gpt-4o-mini    (apply critique, cheap)
    │             └──→ ACT  (loop, max 3)
    └─ no  → save_memory → END
```

### Files Changed

| File | Change |
|------|--------|
| `state/agent_state.py` | Add `model_map: dict` field + `NodeModelConfig` TypedDict to `AgentState`; update `default_state()` with sensible defaults |
| `nodes/model_utils.py` | **NEW** — `build_llm_for_node(state, node_name)` reads `model_map`, delegates to `llm_router.build_llm()` |
| `nodes/act_node.py` | Replace `ChatOpenAI(model=MODEL)` with `build_llm_for_node(state, "act")` |
| `nodes/evaluate_node.py` | Replace `ChatOpenAI(model=MODEL)` with `build_llm_for_node(state, "evaluate")` |
| `nodes/revise_node.py` | Replace `ChatOpenAI(model=MODEL)` with `build_llm_for_node(state, "revise")` |
| `graphs/reflexion_loop.py` | Accept `model_map: dict | None` param in `build_reflexion_graph()` and `run_agent()`; pass into `default_state()` |

### Default Model Map

```python
DEFAULT_MODEL_MAP = {
    "act": {
        "provider":    "openai",
        "model_id":    "gpt-4o-mini",
        "temperature": 0.2,
    },
    "evaluate": {
        "provider":    "openai",
        "model_id":    "gpt-4o",        # upgrade to o3 when budget allows
        "temperature": 0.0,             # deterministic scoring
    },
    "revise": {
        "provider":    "openai",
        "model_id":    "gpt-4o-mini",
        "temperature": 0.2,
    },
}
```

### Calling Convention

```python
# Default (uses DEFAULT_MODEL_MAP)
run_agent("markets-equity-analyst", "markets", "Analyse NVDA earnings catalyst")

# Custom map — reasoning model for high-stakes evaluation
run_agent(
    "markets-cro", "markets", "Review iron condor risk sizing",
    model_map={
        "act":      {"provider": "openai",     "model_id": "gpt-4o-mini", "temperature": 0.2},
        "evaluate": {"provider": "anthropic",  "model_id": "claude-opus-4-5", "temperature": 0.0},
        "revise":   {"provider": "openai",     "model_id": "gpt-4o-mini", "temperature": 0.2},
    }
)

# Ollama-only (fully local, no cloud spend)
run_agent(
    "xftc-plugin-dev", "xftc", "Build PHP validation function",
    model_map={
        "act":      {"provider": "ollama", "model_id": "codellama",  "temperature": 0.1},
        "evaluate": {"provider": "ollama", "model_id": "llama3.1",   "temperature": 0.0},
        "revise":   {"provider": "ollama", "model_id": "codellama",  "temperature": 0.1},
    }
)
```

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Already in codebase — minimal change (6 files) | 2–3× latency (3 sequential LLM calls minimum) |
| Cheap model drafts, expensive model critiques = cost-efficient | Evaluation quality ceiling limits revision quality |
| Score-gated: only revises when score < 0.75 | Loops can spin on ambiguous tasks (max_revisions guard needed) |
| Self-correcting outputs with structured scores | Score rubric needs domain tuning |
| Fully configurable per agent or per run | Not suitable for latency-sensitive real-time tasks |
| Natural audit trail: draft → critique → revision logged | — |

### Cost Profile (approximate)
- Default map: ~$0.002 per run (act+evaluate+revise at gpt-4o-mini + gpt-4o prices)
- Premium map (o3 evaluate): ~$0.02–0.10 per run depending on output length
- Ollama-only: $0

---

## Phase 2 — Meta-Learner: Draft → Critique → Compose

### Status: 🔴 Not Started

### Problem
Reflexion improves the *skill file* but still uses the same model for writing the final output. For long-form work (reports, grant applications, trade recommendations), the final composition benefits from a dedicated "writer" model that sees both the draft AND the critique before composing.

### Design

```
INPUT
  ↓
DRAFTER ── gpt-4o-mini / llama3.2
  │  (fast, cheap; generates raw structured content)
  ↓
CRITIC ─── o3 / claude-opus
  │  (deep reasoning; produces structured JSON critique)
  │  { strengths, weaknesses, missing_elements, suggestions, score }
  ↓
COMPOSER ── claude-opus / gpt-4.1
  │  (best writing model; sees original task + draft + critique)
  │  (produces polished final output)
  ↓
OUTPUT
```

### New Files

| File | Purpose |
|------|---------|
| `graphs/meta_learner_graph.py` | New LangGraph: drafter → critic → composer nodes |
| `nodes/draft_node.py` | Thin wrapper around act_node with "drafter" framing |
| `nodes/critic_node.py` | Structured critique (JSON with strengths, weaknesses, suggestions) |
| `nodes/compose_node.py` | Final composition using draft + critique as full context |

### State Extensions

```python
# Add to AgentState:
draft_output: str        # raw drafter output
critic_output: dict      # structured critique JSON
final_output: str        # composed final output
stacking_mode: str       # "reflexion" | "meta_learner" | "ensemble" | "fanout"
```

### Composer Prompt Pattern

```
You are a world-class [domain] writer.

ORIGINAL TASK:
{task}

DRAFT (from fast model):
{draft_output}

STRUCTURED CRITIQUE:
Strengths: {critic_output.strengths}
Weaknesses: {critic_output.weaknesses}
Missing: {critic_output.missing_elements}
Suggestions: {critic_output.suggestions}

Write the final, polished version that:
1. Preserves all the strengths identified
2. Directly addresses every weakness
3. Includes all missing elements
4. Follows every suggestion
Do NOT reference the draft or critique — produce a clean final output only.
```

### Use Case Mapping

| Agent | Drafter | Critic | Composer |
|-------|---------|--------|---------|
| `markets-tactical-alpha` | gpt-4o-mini | o3 | gpt-4.1 |
| `grants-research-agent` | llama3.1 | claude-opus | claude-opus |
| `yepc-grant-writer` | gpt-4o-mini | gpt-4o | claude-opus |
| `sigma-signal-writer` | llama3.2 | gpt-4o | claude-sonnet |

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Each model does exactly what it's best at | 3 sequential LLM calls = 30–90s latency |
| Critic produces reusable structured signal (feeds feedback loop) | Cost: draft + critique + compose = 3–5× single-model |
| Composer has full context before writing a single word | Error propagation: bad draft can anchor the critic |
| Excellent for reports, grants, trade recommendations | Composer must be prompted to actually USE the critique |
| Critique step doubles as quality signal for `AgentRunLog` | Requires careful prompt engineering at each stage |

---

## Phase 3 — Ensemble Voting

### Status: 🔴 Not Started

### Problem
For high-stakes binary/categorical judgments (signal conviction, CRO approval, risk classification), a single model answer carries all its biases and blind spots. Running N models and voting reduces variance and catches outlier failures.

### Design

```
INPUT
  ├──→ MODEL A (gpt-4o)        ─┐
  ├──→ MODEL B (claude-sonnet) ─┼──→ VOTE/SYNTHESIZE ──→ OUTPUT
  └──→ MODEL C (llama3.1)      ─┘
       (parallel, asyncio.gather)

Voting strategies:
  1. Majority vote   — categorical outputs (conviction: high/moderate/low)
  2. Average score   — numeric outputs (probability_score, risk_reward)
  3. Meta-judge      — pass all 3 responses to 4th model as judge
  4. Embedding sim   — embed all 3, pick centroid nearest response
```

### New Files

| File | Purpose |
|------|---------|
| `graphs/ensemble_graph.py` | Parallel fan-out node + voting node |
| `nodes/ensemble_node.py` | `async` dispatch to N models, collect responses |
| `nodes/vote_node.py` | Majority / average / meta-judge / embedding-sim strategies |

### State Extensions

```python
# Add to AgentState:
ensemble_responses: list[dict]   # [{model_id, provider, output, latency_ms}]
ensemble_vote: str               # winning output
vote_strategy: str               # "majority" | "average" | "meta_judge" | "embedding"
vote_confidence: float           # how strongly the models agreed (0.0–1.0)
```

### Configuration

```python
EnsembleConfig = {
    "models": [
        {"provider": "openai",    "model_id": "gpt-4o",          "weight": 1.0},
        {"provider": "anthropic", "model_id": "claude-sonnet-4-5", "weight": 1.0},
        {"provider": "ollama",    "model_id": "llama3.1",         "weight": 0.8},
    ],
    "vote_strategy":  "majority",    # or "average", "meta_judge", "embedding"
    "timeout_s":      30,            # drop slow models, vote with remainder
    "min_responses":  2,             # fail if fewer than this respond
    "meta_judge":     {"provider": "openai", "model_id": "gpt-4o"},
}
```

### Target Use Cases

| Use Case | Why Ensemble |
|----------|-------------|
| Market signal conviction scoring | Reduces single-model bias on conviction labels |
| CRO risk classification | High stakes — can't afford single point of failure |
| Inez response quality check | Vote on whether Inez answer is factually sound |
| Email cleanup category labels | Cheap models vote → reduces misclassification |

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Parallel execution — latency ~ slowest single model | N× API cost (3 models = 3× tokens) |
| Reduces hallucination risk — outliers get outvoted | Voting is hard: LLM outputs rarely match literally |
| No single point of failure | If all 3 share the same training bias, voting doesn't help |
| Diversity of reasoning styles surfaces blind spots | Meta-judge adds a 4th LLM call |
| `vote_confidence` doubles as uncertainty signal | Overkill for routine summarization or formatting |

---

## Phase 4 — Fan-Out + Synthesizer

### Status: 🔴 Not Started

### Problem
Complex outputs (morning briefing, trade recommendations, grant sections) require knowledge from multiple independent domains simultaneously: news + technicals + macro + risk + portfolio. Routing to a single model forces it to context-switch. Fan-out lets specialist models work in parallel, then a synthesizer merges their domain-expert outputs.

### Design

```
INPUT: "Generate pre-market brief for NVDA"
  │
  ├──→ TASK DECOMPOSER (fast model)
  │       ↓ decomposes into N independent sub-tasks
  │
  ├── Sub-task 1: "Summarise overnight NVDA news"
  │       → Perplexity Sonar Pro (search capability)
  │
  ├── Sub-task 2: "Analyse NVDA technical setup"
  │       → llama3.1 via Ollama (local, fast)
  │
  ├── Sub-task 3: "Assess macro environment impact"
  │       → claude-sonnet (reasoning)
  │
  └── Sub-task 4: "Check options flow for NVDA"
          → gpt-4o (agents capability)

          All run in parallel (asyncio.gather)
                    ↓
          SYNTHESIZER ── gpt-4.1 / claude-opus
                    ↓
                 OUTPUT
```

### New Files

| File | Purpose |
|------|---------|
| `graphs/fanout_graph.py` | Decomposer → parallel specialist nodes → synthesizer |
| `nodes/decompose_node.py` | Breaks task into N independent sub-tasks with model routing hints |
| `nodes/specialist_node.py` | Generic node: runs one sub-task on its assigned model |
| `nodes/synthesize_node.py` | Merges N specialist outputs into coherent final output |

### State Extensions

```python
# Add to AgentState:
sub_tasks: list[dict]            # [{task, model_hint, specialist_output}]
specialist_outputs: list[dict]   # [{sub_task, model_id, output, latency_ms}]
synthesizer_config: dict         # {provider, model_id, temperature}
decomposer_config: dict          # {provider, model_id, temperature}
```

### Decomposer Output Schema

```json
{
  "sub_tasks": [
    {
      "id": "news",
      "task": "Search for latest NVDA earnings news and analyst reactions",
      "capability_hint": "search",
      "max_tokens": 500
    },
    {
      "id": "technicals",
      "task": "Analyse NVDA daily chart: trend, support, resistance, RSI",
      "capability_hint": "reasoning",
      "max_tokens": 400
    }
  ]
}
```

### Use Case Mapping

| Agent/Feature | Sub-tasks | Synthesizer |
|--------------|-----------|-------------|
| Morning Brief | news, todos, markets, weather, deadlines | claude-opus |
| Trade Recommendation | news, technicals, macro, options flow | gpt-4.1 |
| Grant Application | requirements, narrative, budget, impact | claude-opus |
| Weekly Markets Report | performance, macro, signals, positions | claude-sonnet |

### Pros & Cons

| ✅ Pros | ❌ Cons |
|---------|---------|
| Best model per sub-task (Perplexity for news, Ollama for speed) | Most complex to implement — needs task decomposer |
| Parallel execution — latency ~ slowest single specialist | Synthesizer can lose nuance or contradict specialists |
| Naturally maps to ArchonHub's 31-agent department structure | Sub-tasks must be genuinely independent (no hidden deps) |
| Fully traceable: every sub-task has its own model + output | Higher total token cost than sequential |
| Ideal for morning brief + trade recommendations | Synthesis prompt engineering is hard to get right |

---

## Combined Architecture

All four patterns compose. A full production run for a critical trade recommendation:

```
1. FAN-OUT      → 4 specialists gather domain intel in parallel
2. META-LEARNER → drafter drafts from specialist outputs,
                  critic identifies gaps, composer writes final rec
3. REFLEXION    → evaluator scores final rec, revises if < 0.75
4. ENSEMBLE     → 3 models vote on final conviction label
```

---

## Implementation Priority & Effort

| Phase | Files Added/Changed | Estimated Effort | Token Cost Multiplier | Latency |
|-------|-------------------|-----------------|----------------------|---------|
| P1: Reflexion multi-model | 6 changed, 1 new | **4 hours** | 1.5–2× (cheaper act/revise) | 2–3× |
| P2: Meta-Learner | 4 new, 1 changed | **1 day** | 3–5× | 3× |
| P3: Ensemble Voting | 3 new, 1 changed | **1 day** | 3× | ~1× (parallel) |
| P4: Fan-Out + Synthesizer | 5 new, 2 changed | **2–3 days** | 4–6× | ~1.5× (parallel) |
| All 4 + stacking selector UI | +router/UI work | **1 week total** | varies | varies |

---

## Recommended Build Order

```
✅ Done    — Single-model routing (llm_router.py + model_catalog.py)
🟡 P1 Now  — Reflexion: multi-model nodes (model_map in AgentState)
⏭ P2 Next  — Meta-Learner: draft/critic/compose graph
⏭ P3       — Ensemble: parallel voting for signal validation
⏭ P4 Last  — Fan-Out + Synthesizer: morning brief + trade rec
```

---

## Agent × Pattern Matrix

| Agent | P1 Reflexion | P2 Meta-Learner | P3 Ensemble | P4 Fan-Out |
|-------|-------------|-----------------|-------------|-----------|
| `markets-tactical-alpha` | ✓ | ✓ | — | ✓ |
| `markets-cro` | ✓ | — | ✓ | — |
| `markets-quant` | ✓ | ✓ | ✓ | — |
| `inez-chief-of-staff` | ✓ | ✓ | — | ✓ |
| `grants-research-agent` | ✓ | ✓ | — | ✓ |
| `yepc-grant-writer` | ✓ | ✓ | — | — |
| `sigma-signal-writer` | ✓ | ✓ | — | — |
| `xftc-plugin-dev` | ✓ | — | — | — |
| `pbs-fundraising-agent` | ✓ | ✓ | — | — |

---

## Source References

### Current (P1 foundation)
- `.agents/agentharness/graphs/reflexion_loop.py`
- `.agents/agentharness/nodes/act_node.py`
- `.agents/agentharness/nodes/evaluate_node.py`
- `.agents/agentharness/nodes/revise_node.py`
- `.agents/agentharness/state/agent_state.py`
- `.agents/agentharness/app/v3/llm_router.py`
- `.agents/agentharness/app/v3/model_catalog.py`

### Planned (P2–P4)
- `.agents/agentharness/graphs/meta_learner_graph.py`
- `.agents/agentharness/graphs/ensemble_graph.py`
- `.agents/agentharness/graphs/fanout_graph.py`
- `.agents/agentharness/nodes/draft_node.py`
- `.agents/agentharness/nodes/critic_node.py`
- `.agents/agentharness/nodes/compose_node.py`
- `.agents/agentharness/nodes/ensemble_node.py`
- `.agents/agentharness/nodes/vote_node.py`
- `.agents/agentharness/nodes/decompose_node.py`
- `.agents/agentharness/nodes/specialist_node.py`
- `.agents/agentharness/nodes/synthesize_node.py`
- `.agents/agentharness/nodes/model_utils.py`

## Related Documentation

- [Architecture overview](overview.md)
- [Model catalog](../../.agents/agentharness/app/v3/model_catalog.py)
- [LLM router](../../.agents/agentharness/app/v3/llm_router.py)
- [Agent state](../../.agents/agentharness/state/agent_state.py)

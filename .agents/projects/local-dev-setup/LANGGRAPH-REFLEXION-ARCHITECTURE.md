# AgentHarness — LangGraph + Reflexion Architecture
**Version:** 1.0
**Date:** 2026-05-27
**Status:** Design Phase

---

## GOAL

Build a self-improving agent layer that:
1. Runs **inside Base44** (cloud, automated, always-on)
2. Runs **offline** in the AgentHarness local tool (VS Code / terminal)
3. Uses **LangGraph** for multi-step stateful agent workflows
4. Uses **Reflexion** so agents evaluate and improve their own skills over time
5. Is **portable** — the same graph logic runs in both environments

---

## CORE DESIGN PRINCIPLE: ENVIRONMENT ADAPTER PATTERN

The agent graph itself is environment-agnostic.
What changes per environment is the **adapter** — how the graph
reads/writes state, calls tools, and stores memory.

```
┌─────────────────────────────────────────┐
│           AGENT GRAPH (shared)          │
│  LangGraph state machine + Reflexion    │
│  - graph.py (pure Python)               │
│  - nodes: Act → Evaluate → Revise       │
│  - state: AgentState (TypedDict)        │
└────────────┬──────────────┬─────────────┘
             │              │
    ┌─────────▼──┐    ┌──────▼──────────┐
    │  Base44    │    │  Offline / Local │
    │  Adapter   │    │  Adapter         │
    │            │    │                  │
    │ - Entities │    │ - SQLite / JSON  │
    │ - Skills   │    │ - .agents/skills/│
    │ - REST API │    │ - Local FS       │
    │ - Automations│  │ - LangGraph      │
    │             │   │   Studio UI      │
    └────────────┘    └──────────────────┘
```

---

## DIRECTORY STRUCTURE

```
.agents/
├── langgraph/
│   ├── README.md
│   ├── graphs/
│   │   ├── base_agent_graph.py       ← Core LangGraph state machine
│   │   ├── reflexion_loop.py         ← Reflexion: Act → Evaluate → Revise
│   │   ├── research_graph.py         ← Multi-hop research workflow
│   │   └── wordpress_graph.py        ← WP agent multi-step workflow
│   ├── nodes/
│   │   ├── act_node.py               ← Execute the task
│   │   ├── evaluate_node.py          ← Score the output (0.0–1.0)
│   │   ├── revise_node.py            ← Rewrite skill if score < threshold
│   │   └── memory_node.py            ← Read/write agent memory
│   ├── state/
│   │   └── agent_state.py            ← Shared TypedDict state schema
│   ├── adapters/
│   │   ├── base44_adapter.py         ← Base44 entity + skill bridge
│   │   └── local_adapter.py          ← SQLite + filesystem bridge
│   ├── skills_db/
│   │   └── skills_index.json         ← Registry of all learnable skills
│   └── memory/
│       └── agent_memory.json         ← Persistent cross-run memory (local)
├── skills/                           ← Existing skills (auto-discovered)
└── projects/
    └── local-dev-setup/
        └── LANGGRAPH-REFLEXION-ARCHITECTURE.md  ← this file
```

---

## THE STATE SCHEMA (shared across environments)

```python
# state/agent_state.py
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Core identity
    agent_id: str          # e.g. "xftc-plugin-dev"
    project: str           # e.g. "xftc"
    task: str              # Natural language task description

    # Execution
    messages: Annotated[list, add_messages]   # Full message history
    tool_calls: List[dict]                     # Tools invoked this run
    output: str                                # Current best output

    # Reflexion
    score: float           # 0.0–1.0 quality score from evaluator
    critique: str          # What was wrong / what to improve
    revision_count: int    # How many times revised this run
    max_revisions: int     # Cap (default: 3)

    # Memory
    skill_name: str        # Which skill file this run maps to
    skill_version: int     # Version of skill being used
    memory_context: str    # Retrieved long-term memory

    # Environment
    environment: str       # "base44" | "local"
    run_id: str            # Unique ID for this execution
```

---

## THE REFLEXION LOOP (core graph)

```
┌─────────┐
│  START  │
└────┬────┘
     ▼
┌──────────────────┐
│  memory_node     │  ← Pull relevant past runs, skill history
│  Load context    │
└────┬─────────────┘
     ▼
┌──────────────────┐
│  act_node        │  ← Execute task using current skill
│  (LLM + tools)   │
└────┬─────────────┘
     ▼
┌──────────────────┐
│  evaluate_node   │  ← Score output on 3 criteria:
│  Self-critique   │    1. Task completion (0-1)
└────┬─────────────┘    2. Quality / accuracy (0-1)
     │                  3. Efficiency (0-1)
     │  score < 0.75?
     ├──YES──────────────────────────────────┐
     │                                        ▼
     │                           ┌──────────────────────┐
     │                           │  revise_node          │
     │                           │  Rewrite skill file   │
     │                           │  Increment version    │
     │                           │  Log to skills_db     │
     │                           └────────┬─────────────┘
     │                                    │
     │            revision_count < max?   │
     │            ◄───────────────────────┘
     │            YES → back to act_node
     │            NO  → fall through
     │
     ▼  score >= 0.75 OR max revisions hit
┌──────────────────┐
│  memory_node     │  ← Write outcome + learnings to memory
│  Save learnings  │
└────┬─────────────┘
     ▼
┌─────────┐
│   END   │
└─────────┘
```

---

## THE SKILL EVOLUTION SYSTEM

Every agent has a skill file in `.agents/skills/`.
Skills are versioned and scored over time.

```json
// skills_db/skills_index.json
{
  "xftc-plugin-dev": {
    "current_version": 3,
    "avg_score": 0.82,
    "total_runs": 14,
    "skill_file": ".agents/skills/xftc_plugin_dev.md",
    "history": [
      { "version": 1, "score": 0.61, "critique": "Missing error handling for Stripe webhooks", "date": "2026-05-20" },
      { "version": 2, "score": 0.74, "critique": "Incomplete test coverage for registration flow", "date": "2026-05-23" },
      { "version": 3, "score": 0.82, "critique": "Good. Add caching for leaderboard queries.", "date": "2026-05-27" }
    ]
  }
}
```

When `revise_node` fires, it:
1. Reads the current skill file
2. Generates a critique-driven rewrite using the LLM
3. Saves a new versioned skill file
4. Updates `skills_index.json`
5. Logs the improvement delta

---

## ENVIRONMENT ADAPTERS

### Base44 Adapter
```python
# adapters/base44_adapter.py

class Base44Adapter:
    """Bridge between LangGraph state and Base44 platform"""

    def read_memory(self, agent_id):
        # Reads from Base44 AgentMemory entity via REST API
        ...

    def write_memory(self, agent_id, content):
        # Writes to Base44 AgentMemory entity
        ...

    def read_skill(self, skill_name):
        # Reads from .agents/skills/ via Base44 file tools
        ...

    def write_skill(self, skill_name, content, version):
        # Overwrites .agents/skills/<skill_name>.md
        # Triggers GitHub push automation
        ...

    def run_tool(self, tool_name, args):
        # Calls Base44 skill runner or backend function
        ...

    def log_run(self, run_id, agent_id, score, critique):
        # Writes to AgentRunLog entity for dashboard visibility
        ...
```

### Local Adapter
```python
# adapters/local_adapter.py

class LocalAdapter:
    """Bridge for offline AgentHarness tool"""

    def read_memory(self, agent_id):
        # Reads from langgraph/memory/agent_memory.json
        ...

    def write_memory(self, agent_id, content):
        # Writes to langgraph/memory/agent_memory.json
        ...

    def read_skill(self, skill_name):
        # Reads from .agents/skills/ on local filesystem
        ...

    def write_skill(self, skill_name, content, version):
        # Writes to .agents/skills/ locally
        # git commit + push to AgentHarness repo
        ...

    def run_tool(self, tool_name, args):
        # Runs local skill scripts via subprocess
        ...

    def log_run(self, run_id, agent_id, score, critique):
        # Writes to SQLite: langgraph/memory/runs.db
        ...
```

---

## NEW ENTITIES NEEDED (Base44)

```
AgentSkillVersion
  - agent_id: string
  - skill_name: string
  - version: number
  - content: text
  - avg_score: number
  - total_runs: number
  - last_critique: text
  - created_date: auto

AgentRunLog
  - run_id: string
  - agent_id: string
  - project: string
  - task: string
  - score: number
  - critique: string
  - revision_count: number
  - output_summary: text
  - environment: string (base44 | local)
  - created_date: auto
```

---

## PHASE PLAN

### Phase 1 — Foundation (Week 1)
- [ ] Set up `langgraph/` directory structure
- [ ] Write `agent_state.py` TypedDict
- [ ] Build `base_agent_graph.py` (minimal loop: act → evaluate → END)
- [ ] Build `base44_adapter.py` (memory read/write)
- [ ] Create `AgentSkillVersion` + `AgentRunLog` entities in Base44
- [ ] Test with one simple agent (grants-research-agent)

### Phase 2 — Reflexion Loop (Week 2)
- [ ] Add `evaluate_node.py` with 3-criteria scorer
- [ ] Add `revise_node.py` with LLM skill rewriter
- [ ] Wire full Reflexion loop in `reflexion_loop.py`
- [ ] Test with xftc-plugin-dev agent on a real task
- [ ] Validate skill version history is logged correctly

### Phase 3 — Local Adapter (Week 3)
- [ ] Build `local_adapter.py` with SQLite backend
- [ ] Add LangGraph Studio config (`langgraph.json`)
- [ ] Test full offline run from AgentHarness local tool
- [ ] Validate parity between Base44 and local runs

### Phase 4 — Multi-Agent Graphs (Week 4)
- [ ] Build `research_graph.py` (grants research multi-hop)
- [ ] Build `wordpress_graph.py` (WP agent plan → execute → verify)
- [ ] Connect project-lead agents as graph orchestrators
- [ ] Weekly skill improvement report automation

---

## TECH STACK

| Component | Tool |
|-----------|------|
| Graph framework | LangGraph (Python) |
| LLM | OpenAI GPT-4o (or local Ollama for offline) |
| State persistence (Base44) | Base44 entities via REST |
| State persistence (local) | SQLite + JSON files |
| Skill storage | Markdown files in `.agents/skills/` |
| Local dev UI | LangGraph Studio |
| Version control | GitHub AgentHarness repo |
| Package manager | `uv` (fast Python) |

---

## OFFLINE TOOL INTEGRATION

The local AgentHarness tool (from `AGENTHARNESS-BUILD-PROMPT.md`) gets:
- A **LangGraph Studio** panel showing live graph state
- A **Skills Dashboard** showing version history + scores per agent
- A **Run History** tab pulling from SQLite runs.db
- A **Reflexion Trigger** button to manually fire improve cycle on any agent

---

## DEPENDENCY FILE (requirements.txt)

```
langgraph>=0.2.0
langchain>=0.3.0
langchain-openai>=0.1.0
langchain-community>=0.3.0
openai>=1.0.0
pydantic>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
sqlite-utils>=3.35.0
```

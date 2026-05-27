# AgentHarness — LangGraph + Reflexion Engine
**Version:** 1.0  
**Date:** 2026-05-27  
**Status:** Phase 1–4 Complete

---

## What This Is

A self-improving agent layer built on **LangGraph** and **Reflexion** that runs in:
- ☁️ **Base44** (cloud, always-on, automated)
- 💻 **Offline** (AgentHarness local tool, LangGraph Studio)

Agents execute tasks, evaluate their own output, and rewrite their skill files
when they score below 0.75 — automatically getting smarter over time.

---

## Directory Structure

```
langgraph/
├── graphs/
│   ├── base_agent_graph.py     # Minimal base — wraps reflexion_loop
│   ├── reflexion_loop.py       # Core Act → Evaluate → Revise graph
│   ├── research_graph.py       # Multi-hop grant research workflow
│   └── wordpress_graph.py      # WP Plan → Implement → Verify workflow
├── nodes/
│   ├── act_node.py             # Execute task with LLM
│   ├── evaluate_node.py        # Score output (0.0–1.0), decide revise/save
│   ├── revise_node.py          # Rewrite skill file from critique
│   └── memory_node.py          # Load/save memory at run boundaries
├── state/
│   └── agent_state.py          # Shared TypedDict — same in all environments
├── adapters/
│   ├── base44_adapter.py       # Base44 entities + skills bridge
│   └── local_adapter.py        # SQLite + filesystem bridge
├── skills_db/
│   └── skills_index.json       # Version history for all agent skills
├── memory/
│   └── agent_memory.json       # Local cross-run memory store
├── langgraph.json              # LangGraph Studio config
├── requirements.txt
└── README.md
```

---

## Quick Start (Local)

```bash
# Install dependencies
cd .agents/langgraph
pip install -r requirements.txt

# Set your OpenAI key
export OPENAI_API_KEY=sk-...

# Run any agent
python3 -c "
from graphs.reflexion_loop import run_agent
result = run_agent(
    agent_id='grants-research-agent',
    project='xftc',
    task='Find 3 active grants for youth track programs in Texas under 501c3 nonprofits',
    environment='local'
)
print(result['output'])
print(f'Score: {result[\"score\"]:.2f}')
"

# Open LangGraph Studio UI
langgraph dev
```

---

## Quick Start (Base44 Cloud)

```python
# In a Base44 backend function or automation:
from langgraph.graphs.reflexion_loop import run_agent

result = run_agent(
    agent_id="xftc-plugin-dev",
    project="xftc",
    task="Write a PHP function to register a custom REST API endpoint for athlete leaderboard data",
    environment="base44"
)
```

---

## How Reflexion Works

```
load_memory → act → evaluate → [score < 0.75?] → revise → act (loop)
                                [score >= 0.75] → save_memory → END
```

1. **load_memory** — pulls prior skill version + critique from storage
2. **act** — LLM executes task using current skill as context
3. **evaluate** — scores output on Completion (50%) + Quality (35%) + Efficiency (15%)
4. **revise** — if score < 0.75, rewrites skill file addressing the critique (max 3×)
5. **save_memory** — logs run to AgentRunLog entity / SQLite

---

## Graphs Available

| Graph | File | Best For |
|-------|------|----------|
| `reflexion_loop` | `graphs/reflexion_loop.py` | Any general agent task |
| `research_graph` | `graphs/research_graph.py` | Grant research, multi-hop info gathering |
| `wordpress_graph` | `graphs/wordpress_graph.py` | WP plugin dev, page updates, REST API tasks |

---

## Entities (Base44)

| Entity | Purpose |
|--------|---------|
| `AgentSkillVersion` | Version history for every agent's skill file |
| `AgentRunLog` | Every run logged with score, critique, revision count |

---

## Adding a New Agent

1. Create skill stub: `.agents/skills/my_agent.md`
2. Add to `skills_db/skills_index.json`
3. Call `run_agent("my-agent-id", "project-name", "task description")`
4. The Reflexion loop handles the rest — the agent improves automatically

---

## Environment Variables Required

```
OPENAI_API_KEY=sk-...
BASE44_API_KEY=...          # Only needed for base44 environment
BASE44_APP_ID=6a0bce17b730c0de488b80fb
```

# AgentHarness v3
## LangGraph Native Desktop App

AgentHarness v3 is a single-file Tkinter desktop application with **LangGraph fully integrated** — no subprocess calls, no separate engine. All graphs compile and execute inside the GUI process.

---

## What's New in v3 (vs v2)

| Feature | v2 | v3 |
|---------|----|----|
| LangGraph integration | External module import | **Fully embedded — runs in-process** |
| Graph visualizer | Static canvas | **Live node highlight during execution** |
| Business Law graph | ❌ | **✅ 3-node: analyze → draft → review** |
| Agent grouping | Flat list | **Team-grouped dropdowns** |
| Skill viewer tab | ❌ | **✅ Reads .md skill files from disk** |
| Output tab | Log only | **✅ Dedicated live output panel** |
| DB persistence | SQLite | **SQLite v3 — separate schema** |
| Run streaming | Blocking | **✅ Streamed per-node with live UI update** |

---

## 4 Graphs Available

| Graph | Nodes | Best For |
|-------|-------|---------|
| **Reflexion** | load_memory → act → evaluate → revise* → save | General tasks, any agent |
| **Research** | load_memory → plan → search → synthesize → evaluate → revise* → save | Grant research, market research |
| **WordPress** | load_memory → wp_plan → wp_implement → wp_verify → evaluate → revise* → save | WP dev, plugin work, REST API |
| **Business Law** | load_memory → legal_analyze → legal_draft → legal_review → evaluate → revise* → save | Legal docs, contracts, compliance |

All graphs use the same Reflexion loop (evaluate → revise → loop) for self-improvement.

---

## Quick Start

### Windows (PowerShell)
```powershell
.\.agents\agentharness\app\v3\start.ps1
```

### Manual
```bash
pip install langgraph langchain-openai langchain-core
export OPENAI_API_KEY=sk-...
python .agents/agentharness/app/v3/main.py
```

---

## Agent Teams

| Team | Agents |
|------|--------|
| **Business Law** | project-lead, entity, contracts, IP, employment, real estate, regulatory |
| **XFTC** | project-lead, plugin-dev, frontend-dev, payments, QA |
| **Grants/YEPC** | research, writer, yepc-grant-writer, real-estate-research, PM |
| **S2T Designs** | project-lead, webdev, SEO |
| **SmithCap Finance** | CFO, CPA, tax-strategist, bookkeeper, advisor |
| **Ministry** | project-lead, sermon-writer |
| **Social Media** | project-lead, content-strategist, copywriter, ads-manager |
| **Solar** | project-lead, marketing |
| **Sigma Signal** | project-lead, writer |

---

## Architecture

```
main.py (1,200 lines — all-in-one)
├── COLOUR PALETTE
├── AGENT REGISTRY (team → [agents])
├── DATABASE (SQLite — runs_v3.db, skills table)
├── LANGGRAPH NODES
│   ├── node_act         — executes task with skill + memory
│   ├── node_evaluate    — scores output 0.0-1.0
│   ├── node_revise      — rewrites skill file if score < 0.75
│   ├── node_save        — persists run to SQLite
│   ├── node_plan/search/synthesize  — research graph
│   ├── node_wp_plan/implement/verify — wordpress graph
│   └── node_legal_analyze/draft/review — business law graph
├── GRAPH BUILDERS (4 compiled StateGraphs)
├── GRAPH VISUALIZER (live Canvas node diagram)
└── AgentHarnessV3 (Tkinter app class)
    ├── Controls panel (team, agent, project, task, max revisions)
    ├── Live Log tab
    ├── Output tab
    ├── Skill Viewer tab
    └── Run History tab (Treeview + SQLite)
```

---

## Skill Files

Business Law agents read their TX Bar-trained skill files from:
```
.agents/agents/projects/business-law/<agent-id>.md
```

All other agents read from:
```
.agents/agents/projects/<team>/<agent-id>.md
```

Skills auto-upgrade when score < 0.75 — new version saved to SQLite.

---

*AgentHarness v3 | Built May 2026 | Smith Capital Portfolio*

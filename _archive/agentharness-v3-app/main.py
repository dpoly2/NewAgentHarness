"""
AgentHarness v3 — LangGraph Fully Integrated Desktop App
=========================================================
All LangGraph graph logic (reflexion, research, wordpress, business-law)
runs directly inside this process — no subprocess, no separate engine.

Run: python .agents/agentharness/app/v3/main.py
Requires: pip install langgraph langchain-openai
"""

import sys
import os
import threading
import queue
import json
import uuid
import sqlite3
from datetime import datetime
from pathlib import Path
from functools import partial

# ── Path setup ──────────────────────────────────────────────────────────────
HERE       = Path(__file__).parent                        # app/v3/
HARNESS    = HERE.parent.parent                           # agentharness/
AGENTS_DIR = HARNESS.parent                               # .agents/
APP_ROOT   = AGENTS_DIR.parent                            # /app
SKILLS_DIR = AGENTS_DIR / "agents" / "projects"
MEMORY_DIR = HARNESS / "memory"
DB_PATH    = MEMORY_DIR / "runs_v3.db"

for p in [str(AGENTS_DIR), str(APP_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── LangGraph / LangChain ────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGGRAPH_OK = True
except ImportError:
    LANGGRAPH_OK = False

# ── Tkinter ──────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font as tkfont

# ════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE
# ════════════════════════════════════════════════════════════════════════════
BG        = "#0f1117"
PANEL     = "#1a1d27"
BORDER    = "#2a2d3e"
ACCENT    = "#5b5ff5"
ACCENT2   = "#7c3aed"
SUCCESS   = "#22c55e"
WARNING   = "#f59e0b"
ERROR     = "#ef4444"
TEXT      = "#e2e8f0"
TEXT_DIM  = "#64748b"
HIGHLIGHT = "#1e2235"
GOLD      = "#f59e0b"

NODE_COLORS = {
    "load_memory":    "#0ea5e9",
    "act":            "#8b5cf6",
    "evaluate":       "#f59e0b",
    "revise":         "#ef4444",
    "save_memory":    "#22c55e",
    "plan":           "#06b6d4",
    "search":         "#3b82f6",
    "synthesize":     "#a855f7",
    "wp_plan":        "#06b6d4",
    "wp_implement":   "#8b5cf6",
    "wp_verify":      "#22c55e",
    "legal_analyze":  "#f97316",
    "legal_draft":    "#ec4899",
    "legal_review":   "#14b8a6",
    "END":            "#475569",
}

# ════════════════════════════════════════════════════════════════════════════
# AGENT / PROJECT REGISTRY
# ════════════════════════════════════════════════════════════════════════════
AGENT_REGISTRY = {
    "XFTC": [
        "xftc-project-lead", "xftc-plugin-dev", "xftc-frontend-dev",
        "xftc-payments-agent", "xftc-qa-agent",
    ],
    "Grants / YEPC": [
        "grants-research-agent", "grant-writer-agent",
        "yepc-grant-writer-agent", "yepc-real-estate-research-agent",
        "yepc-project-manager",
    ],
    "S2T Designs": [
        "s2t-project-lead", "s2t-webdev-agent", "s2t-seo-agent",
    ],
    "Business Law": [
        "business-law-project-lead", "business-law-entity-agent",
        "business-law-contracts-agent", "business-law-ip-agent",
        "business-law-employment-agent", "business-law-realestate-agent",
        "business-law-regulatory-agent",
    ],
    "SmithCap Finance": [
        "finance-cfo", "finance-cpa", "finance-tax-strategist",
        "finance-bookkeeper", "finance-advisor",
    ],
    "Ministry": [
        "ministry-project-lead", "ministry-sermon-writer",
    ],
    "Social Media": [
        "social-project-lead", "social-content-strategist",
        "social-copywriter", "social-ads-manager",
    ],
    "Solar": [
        "solar-project-lead", "solar-marketing-agent",
    ],
    "Sigma Signal": [
        "sigma-signal-project-lead", "sigma-signal-writer",
    ],
}

GRAPHS = ["reflexion", "research", "wordpress", "business-law"]

PROJECTS = [
    "xftc", "yepc", "pbs-foundation", "s2tdesigns",
    "smithcap", "smithcap-finance", "ministry", "business-law",
    "social-media", "solar-repair", "sigma-signal",
    "nutrue", "the-elevation", "travel", "holdings",
]

# Flat agent list for combobox
ALL_AGENTS = [a for agents in AGENT_REGISTRY.values() for a in agents]

# ════════════════════════════════════════════════════════════════════════════
# LOG QUEUE — background thread writes, UI polls
# ════════════════════════════════════════════════════════════════════════════
log_queue: queue.Queue = queue.Queue()

def q(msg: str, color: str = TEXT, bold: bool = False):
    log_queue.put({"text": msg, "color": color, "bold": bold})


# ════════════════════════════════════════════════════════════════════════════
# PATCH print → GUI log
# ════════════════════════════════════════════════════════════════════════════
_orig_print = print

def _gui_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    _orig_print(msg, **kwargs)
    color = TEXT_DIM
    if "[ActNode]"        in msg: color = NODE_COLORS["act"]
    elif "[EvaluateNode]" in msg: color = NODE_COLORS["evaluate"]
    elif "[MemoryNode]"   in msg: color = NODE_COLORS["load_memory"]
    elif "[ReviseNode]"   in msg: color = NODE_COLORS["revise"]
    elif "[LegalGraph]"   in msg: color = NODE_COLORS["legal_analyze"]
    elif "[ResearchGraph" in msg: color = NODE_COLORS["search"]
    elif "[WPGraph"       in msg: color = NODE_COLORS["wp_plan"]
    elif "REFLEXION RUN"  in msg: color = ACCENT
    elif "COMPLETE"       in msg: color = SUCCESS
    elif "ERROR"          in msg: color = ERROR
    elif "SCORE"          in msg: color = GOLD
    log_queue.put({"text": msg, "color": color, "bold": False})

import builtins
builtins.print = _gui_print


# ════════════════════════════════════════════════════════════════════════════
# DATABASE (SQLite — local persistence)
# ════════════════════════════════════════════════════════════════════════════
def _get_db():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT, agent_id TEXT, project TEXT, graph TEXT,
            task TEXT, score REAL, critique TEXT,
            revision_count INTEGER, output TEXT,
            skill_version INTEGER, status TEXT, created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT, skill_name TEXT, version INTEGER,
            content TEXT, avg_score REAL, last_critique TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def db_save_run(run: dict):
    conn = _get_db()
    conn.execute("""
        INSERT INTO runs (run_id, agent_id, project, graph, task, score,
            critique, revision_count, output, skill_version, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        run["run_id"], run["agent_id"], run["project"], run.get("graph","reflexion"),
        run["task"][:500], run["score"], run["critique"],
        run["revision_count"], run["output"][:1000],
        run["skill_version"], run["status"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def db_load_runs(limit=50) -> list:
    conn = _get_db()
    rows = conn.execute(
        "SELECT run_id, agent_id, project, graph, score, status, created_at "
        "FROM runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows


def db_load_skill(skill_name: str):
    conn = _get_db()
    row = conn.execute(
        "SELECT content, version FROM skills WHERE skill_name=? "
        "ORDER BY version DESC LIMIT 1", (skill_name,)
    ).fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return "", 1


def db_save_skill(agent_id, skill_name, version, content, score, critique):
    conn = _get_db()
    conn.execute("""
        INSERT INTO skills (agent_id, skill_name, version, content, avg_score,
            last_critique, created_at)
        VALUES (?,?,?,?,?,?,?)
    """, (agent_id, skill_name, version, content, score, critique,
          datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def read_agent_skill_file(agent_id: str) -> str:
    """Try to read the agent's .md skill file from the agents/projects directory."""
    project_map = {
        "business-law": "business-law",
        "xftc": "xftc",
        "finance": "smithcap-finance",
        "ministry": "ministry",
        "social": "social-media",
        "solar": "solar-repair",
        "sigma-signal": "sigma-signal",
        "s2t": "s2tdesigns",
        "yepc": "yepc",
        "grant": "grants",
        "travel": "travel",
    }
    for key, folder in project_map.items():
        if key in agent_id:
            skill_path = SKILLS_DIR / folder / f"{agent_id}.md"
            if skill_path.exists():
                return skill_path.read_text()
    # Try flat scan
    for md in SKILLS_DIR.rglob(f"{agent_id}.md"):
        return md.read_text()
    return ""


# ════════════════════════════════════════════════════════════════════════════
# LANGGRAPH STATE
# ════════════════════════════════════════════════════════════════════════════
from typing import TypedDict, List, Annotated, Optional

try:
    from langgraph.graph.message import add_messages

    class AgentState(TypedDict):
        agent_id: str
        project: str
        task: str
        graph_type: str
        messages: Annotated[list, add_messages]
        output: str
        score: float
        critique: str
        revision_count: int
        max_revisions: int
        skill_name: str
        skill_version: int
        skill_content: str
        memory_context: str
        run_id: str

    def default_state(agent_id, project, task, graph_type="reflexion", max_rev=3):
        skill_name = agent_id.replace("-", "_")
        skill_content, skill_version = db_load_skill(skill_name)
        if not skill_content:
            skill_content = read_agent_skill_file(agent_id)
        memory_context = _load_memory_context(agent_id)
        return AgentState(
            agent_id=agent_id, project=project, task=task,
            graph_type=graph_type,
            messages=[], output="", score=0.0, critique="",
            revision_count=0, max_revisions=max_rev,
            skill_name=skill_name, skill_version=skill_version,
            skill_content=skill_content, memory_context=memory_context,
            run_id=str(uuid.uuid4())[:8],
        )

except ImportError:
    AgentState = dict
    def default_state(*a, **kw): return {}


def _load_memory_context(agent_id: str) -> str:
    conn = _get_db()
    row = conn.execute(
        "SELECT score, critique, skill_version, created_at FROM runs "
        "WHERE agent_id=? ORDER BY id DESC LIMIT 1", (agent_id,)
    ).fetchone()
    conn.close()
    if row:
        return f"Last run ({row[3][:10]}): score={row[0]:.2f}, skill_v{row[2]}. Critique: {row[1] or 'none'}"
    return "No prior runs found."


# ════════════════════════════════════════════════════════════════════════════
# LANGGRAPH NODES
# ════════════════════════════════════════════════════════════════════════════
MODEL = "gpt-4o"

def _get_llm(temp=0.2):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    return ChatOpenAI(model=MODEL, temperature=temp, api_key=api_key)


# ── Act ──────────────────────────────────────────────────────────────────────
def node_act(state: AgentState) -> AgentState:
    llm = _get_llm(0.2)
    parts = [
        f"You are the '{state['agent_id']}' agent for the '{state['project']}' project.",
        "Complete the task accurately and thoroughly.",
    ]
    if state.get("skill_content"):
        parts.append(f"\n## Your Skill (v{state['skill_version']}):\n{state['skill_content'][:3000]}")
    if state.get("memory_context"):
        parts.append(f"\n## Prior Context:\n{state['memory_context']}")
    if state["revision_count"] > 0:
        parts.append(f"\n## Critique to Address:\n{state['critique']}")

    sys_prompt = "\n\n".join(parts)
    msgs = [SystemMessage(content=sys_prompt), HumanMessage(content=state["task"])]
    if state["revision_count"] > 0 and state.get("messages"):
        msgs = state["messages"] + [HumanMessage(
            content=f"REVISION {state['revision_count']} — Address this critique:\n{state['critique']}\n\nTask: {state['task']}"
        )]

    print(f"[ActNode] Agent={state['agent_id']} Rev={state['revision_count']} Run={state['run_id']}")
    resp = llm.invoke(msgs)
    return {**state, "output": resp.content, "messages": msgs + [resp]}


# ── Evaluate ─────────────────────────────────────────────────────────────────
EVAL_SYS = """You are a strict quality evaluator. Score the output on:
1. COMPLETION (0-1): Did the agent fully complete the task?
2. QUALITY (0-1): Is the output accurate, well-structured, and useful?
3. EFFICIENCY (0-1): Is it concise and free of padding?

Respond ONLY with valid JSON:
{"completion": 0.0, "quality": 0.0, "efficiency": 0.0, "overall": 0.0, "critique": "..."}

overall = completion*0.5 + quality*0.35 + efficiency*0.15"""

def node_evaluate(state: AgentState) -> AgentState:
    llm = _get_llm(0.0)
    resp = llm.invoke([
        SystemMessage(content=EVAL_SYS),
        HumanMessage(content=f"TASK:\n{state['task']}\n\nOUTPUT:\n{state['output']}")
    ])
    try:
        raw = resp.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(raw)
        score    = float(data.get("overall", 0.6))
        critique = data.get("critique", "")
    except Exception:
        score, critique = 0.6, f"Parse error: {resp.content[:100]}"
    print(f"[EvaluateNode] SCORE={score:.2f} — {critique[:80]}")
    return {**state, "score": score, "critique": critique}


def should_revise(state: AgentState) -> str:
    if state["score"] < 0.75 and state["revision_count"] < state["max_revisions"]:
        print(f"[EvaluateNode] → REVISE (score={state['score']:.2f})")
        return "revise"
    print(f"[EvaluateNode] → SAVE (score={state['score']:.2f})")
    return "save"


# ── Revise ───────────────────────────────────────────────────────────────────
REVISE_SYS = """You are an AI skill optimizer. Rewrite the skill file to fix the critique.
Keep Markdown format. Increment version number in header.
Output ONLY the rewritten skill file."""

def node_revise(state: AgentState) -> AgentState:
    llm = _get_llm(0.3)
    skill = state.get("skill_content") or f"# Skill: {state['skill_name']} v1\n\nComplete tasks accurately."
    new_v = state["skill_version"] + 1
    resp = llm.invoke([
        SystemMessage(content=REVISE_SYS),
        HumanMessage(content=(
            f"## Skill (v{state['skill_version']}):\n{skill[:2000]}\n\n"
            f"## Task:\n{state['task']}\n\n"
            f"## Critique:\n{state['critique']}\n\n"
            f"Rewrite as v{new_v}."
        ))
    ])
    new_skill = resp.content.strip()
    db_save_skill(state["agent_id"], state["skill_name"], new_v,
                  new_skill, state["score"], state["critique"])
    print(f"[ReviseNode] Skill '{state['skill_name']}' v{state['skill_version']} → v{new_v}")
    return {**state, "skill_content": new_skill, "skill_version": new_v,
            "revision_count": state["revision_count"] + 1}


# ── Save ─────────────────────────────────────────────────────────────────────
def node_save(state: AgentState) -> AgentState:
    db_save_run({
        "run_id": state["run_id"], "agent_id": state["agent_id"],
        "project": state["project"], "graph": state.get("graph_type","reflexion"),
        "task": state["task"], "score": state["score"],
        "critique": state["critique"], "revision_count": state["revision_count"],
        "output": state["output"], "skill_version": state["skill_version"],
        "status": "complete",
    })
    print(f"[MemoryNode] Saved run={state['run_id']} score={state['score']:.2f}")
    return state


# ── Research-specific nodes ──────────────────────────────────────────────────
def node_plan(state: AgentState) -> AgentState:
    llm = _get_llm(0.2)
    resp = llm.invoke([
        SystemMessage(content="You are a research planning assistant. Output 3-5 specific search queries as a numbered list only."),
        HumanMessage(content=f"Research task: {state['task']}")
    ])
    print(f"[ResearchGraph:plan] Queries generated")
    return {**state, "output": f"RESEARCH PLAN:\n{resp.content}", "messages": state["messages"] + [resp]}


def node_search(state: AgentState) -> AgentState:
    llm = _get_llm(0.1)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a grant research specialist with knowledge of federal, state, and private "
            "foundation funding opportunities as of 2026. For each search query, synthesize the "
            "most relevant funding opportunities: name, funder, amount, deadline, eligibility, link."
        )),
        HumanMessage(content=f"Project: {state['project']}\nMemory: {state.get('memory_context','')}\n\nQueries:\n{state['output']}")
    ])
    print(f"[ResearchGraph:search] Results gathered")
    return {**state, "output": resp.content, "messages": state["messages"] + [resp]}


def node_synthesize(state: AgentState) -> AgentState:
    llm = _get_llm(0.1)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a grant writing strategist. Produce a clean prioritized digest:\n"
            "1. TOP OPPORTUNITIES (3-5 best fits, ranked)\n"
            "2. QUICK WINS (low barrier, fast deadline)\n"
            "3. ACTION ITEMS\n4. WATCH LIST"
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nRaw research:\n{state['output']}")
    ])
    print(f"[ResearchGraph:synthesize] Digest complete")
    return {**state, "output": resp.content, "messages": state["messages"] + [resp]}


# ── WordPress-specific nodes ─────────────────────────────────────────────────
def node_wp_plan(state: AgentState) -> AgentState:
    llm = _get_llm(0.1)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a senior WordPress developer. Output a numbered implementation plan "
            "with specific technical steps including: files to modify, functions to write, "
            "REST API calls, WP hooks/filters. Be concrete."
        )),
        HumanMessage(content=f"Agent: {state['agent_id']}\nProject: {state['project']}\nSkill: {state.get('skill_content','')[:500]}\nTask: {state['task']}")
    ])
    print(f"[WPGraph:plan] Plan generated")
    return {**state, "output": f"IMPLEMENTATION PLAN:\n{resp.content}", "messages": state["messages"] + [resp]}


def node_wp_implement(state: AgentState) -> AgentState:
    llm = _get_llm(0.1)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a senior WordPress developer. Produce complete, working code or REST API "
            "call sequences. Include full PHP/JS, exact endpoints and payloads, error handling, "
            "and inline comments. Output must be immediately usable."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nPlan:\n{state['output']}")
    ])
    print(f"[WPGraph:implement] Code generated")
    return {**state, "output": resp.content, "messages": state["messages"] + [resp]}


def node_wp_verify(state: AgentState) -> AgentState:
    llm = _get_llm(0.0)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a WordPress code reviewer. Check for: (1) SQL injection / missing nonces "
            "/ capability checks, (2) WP coding standards, (3) REST API auth issues, "
            "(4) missing error handling. If clean, say 'VERIFIED: No issues.' Then output "
            "the corrected/verified final implementation."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nImplementation:\n{state['output']}")
    ])
    print(f"[WPGraph:verify] Verification complete")
    return {**state, "output": resp.content, "messages": state["messages"] + [resp]}


# ── Business Law-specific nodes ──────────────────────────────────────────────
LEGAL_TRIAGE_SYS = """You are the business-law-project-lead for the Smith Capital portfolio.
You are trained to Texas Bar Exam standard across: entity formation, contracts, IP, employment,
real estate, and regulatory/licensing.

For the given legal task:
1. Identify the primary practice area(s)
2. Identify the relevant TX statute or federal law
3. State the applicable legal standard or test
4. Route to the specialist agent if needed
5. Flag any urgent risks with 🔴"""

def node_legal_analyze(state: AgentState) -> AgentState:
    llm = _get_llm(0.1)
    skill = state.get("skill_content") or ""
    resp = llm.invoke([
        SystemMessage(content=LEGAL_TRIAGE_SYS + (f"\n\n## Your TX Bar Skill:\n{skill[:3000]}" if skill else "")),
        HumanMessage(content=f"Legal task for {state['project']}:\n{state['task']}")
    ])
    print(f"[LegalGraph:analyze] Issue identified")
    return {**state, "output": f"## LEGAL ANALYSIS\n{resp.content}", "messages": state["messages"] + [resp]}


def node_legal_draft(state: AgentState) -> AgentState:
    llm = _get_llm(0.2)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a Texas-trained business law specialist. Based on the legal analysis provided, "
            "draft the requested document, contract, opinion, or action plan. "
            "Apply Texas law throughout. Cite TX statutes where relevant. "
            "End with: 'Review with a licensed Texas attorney before executing.'"
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nAnalysis:\n{state['output']}")
    ])
    print(f"[LegalGraph:draft] Document drafted")
    return {**state, "output": resp.content, "messages": state["messages"] + [resp]}


def node_legal_review(state: AgentState) -> AgentState:
    llm = _get_llm(0.0)
    resp = llm.invoke([
        SystemMessage(content=(
            "You are a senior Texas attorney reviewing a legal document or analysis. Check for:\n"
            "1. Correct Texas law applied (TX BOC, TX Property Code, TX Bus. & Com. Code, etc.)\n"
            "2. Missing elements (parties, consideration, governing law clause)\n"
            "3. Enforceability risks under Texas law\n"
            "4. Anything that could expose David Smith or his entities to liability\n"
            "If issues found, list them and provide corrected language. "
            "If clean, say 'REVIEWED: No issues found.' then confirm the final document."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nDocument/Analysis:\n{state['output']}")
    ])
    print(f"[LegalGraph:review] Review complete")
    return {**state, "output": resp.content, "messages": state["messages"] + [resp]}


# ════════════════════════════════════════════════════════════════════════════
# GRAPH BUILDERS
# ════════════════════════════════════════════════════════════════════════════
def build_reflexion_graph():
    g = StateGraph(AgentState)
    g.add_node("load_memory", lambda s: {**s, "memory_context": _load_memory_context(s["agent_id"])})
    g.add_node("act",         node_act)
    g.add_node("evaluate",    node_evaluate)
    g.add_node("revise",      node_revise)
    g.add_node("save_memory", node_save)
    g.set_entry_point("load_memory")
    g.add_edge("load_memory", "act")
    g.add_edge("act",         "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save_memory"})
    g.add_edge("revise",      "act")
    g.add_edge("save_memory", END)
    return g.compile()


def build_research_graph():
    g = StateGraph(AgentState)
    g.add_node("load_memory", lambda s: {**s, "memory_context": _load_memory_context(s["agent_id"])})
    g.add_node("plan",        node_plan)
    g.add_node("search",      node_search)
    g.add_node("synthesize",  node_synthesize)
    g.add_node("evaluate",    node_evaluate)
    g.add_node("revise",      node_revise)
    g.add_node("save_memory", node_save)
    g.set_entry_point("load_memory")
    g.add_edge("load_memory", "plan")
    g.add_edge("plan",        "search")
    g.add_edge("search",      "synthesize")
    g.add_edge("synthesize",  "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save_memory"})
    g.add_edge("revise",      "synthesize")
    g.add_edge("save_memory", END)
    return g.compile()


def build_wordpress_graph():
    g = StateGraph(AgentState)
    g.add_node("load_memory",  lambda s: {**s, "memory_context": _load_memory_context(s["agent_id"])})
    g.add_node("wp_plan",      node_wp_plan)
    g.add_node("wp_implement", node_wp_implement)
    g.add_node("wp_verify",    node_wp_verify)
    g.add_node("evaluate",     node_evaluate)
    g.add_node("revise",       node_revise)
    g.add_node("save_memory",  node_save)
    g.set_entry_point("load_memory")
    g.add_edge("load_memory",  "wp_plan")
    g.add_edge("wp_plan",      "wp_implement")
    g.add_edge("wp_implement", "wp_verify")
    g.add_edge("wp_verify",    "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save_memory"})
    g.add_edge("revise",       "wp_plan")
    g.add_edge("save_memory",  END)
    return g.compile()


def build_legal_graph():
    """Business Law graph: analyze → draft → review → evaluate → revise* → save"""
    g = StateGraph(AgentState)
    g.add_node("load_memory",   lambda s: {**s, "skill_content": read_agent_skill_file(s["agent_id"]) or s.get("skill_content",""), "memory_context": _load_memory_context(s["agent_id"])})
    g.add_node("legal_analyze", node_legal_analyze)
    g.add_node("legal_draft",   node_legal_draft)
    g.add_node("legal_review",  node_legal_review)
    g.add_node("evaluate",      node_evaluate)
    g.add_node("revise",        node_revise)
    g.add_node("save_memory",   node_save)
    g.set_entry_point("load_memory")
    g.add_edge("load_memory",   "legal_analyze")
    g.add_edge("legal_analyze", "legal_draft")
    g.add_edge("legal_draft",   "legal_review")
    g.add_edge("legal_review",  "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save_memory"})
    g.add_edge("revise",        "legal_analyze")
    g.add_edge("save_memory",   END)
    return g.compile()


GRAPH_BUILDERS = {
    "reflexion":    build_reflexion_graph,
    "research":     build_research_graph,
    "wordpress":    build_wordpress_graph,
    "business-law": build_legal_graph,
}


# ════════════════════════════════════════════════════════════════════════════
# GRAPH VISUALIZER — Canvas-drawn node diagram
# ════════════════════════════════════════════════════════════════════════════
GRAPH_LAYOUTS = {
    "reflexion": {
        "nodes": ["load_memory","act","evaluate","revise","save_memory"],
        "edges": [
            ("load_memory","act"), ("act","evaluate"),
            ("evaluate","save_memory"), ("evaluate","revise"), ("revise","act"),
        ],
        "dashed": [("evaluate","revise"), ("revise","act")],
    },
    "research": {
        "nodes": ["load_memory","plan","search","synthesize","evaluate","revise","save_memory"],
        "edges": [
            ("load_memory","plan"),("plan","search"),("search","synthesize"),
            ("synthesize","evaluate"),("evaluate","save_memory"),
            ("evaluate","revise"),("revise","synthesize"),
        ],
        "dashed": [("evaluate","revise"),("revise","synthesize")],
    },
    "wordpress": {
        "nodes": ["load_memory","wp_plan","wp_implement","wp_verify","evaluate","revise","save_memory"],
        "edges": [
            ("load_memory","wp_plan"),("wp_plan","wp_implement"),("wp_implement","wp_verify"),
            ("wp_verify","evaluate"),("evaluate","save_memory"),
            ("evaluate","revise"),("revise","wp_plan"),
        ],
        "dashed": [("evaluate","revise"),("revise","wp_plan")],
    },
    "business-law": {
        "nodes": ["load_memory","legal_analyze","legal_draft","legal_review","evaluate","revise","save_memory"],
        "edges": [
            ("load_memory","legal_analyze"),("legal_analyze","legal_draft"),
            ("legal_draft","legal_review"),("legal_review","evaluate"),
            ("evaluate","save_memory"),("evaluate","revise"),("revise","legal_analyze"),
        ],
        "dashed": [("evaluate","revise"),("revise","legal_analyze")],
    },
}


def draw_graph(canvas: tk.Canvas, graph_type: str, active_node: str = ""):
    canvas.delete("all")
    layout = GRAPH_LAYOUTS.get(graph_type, GRAPH_LAYOUTS["reflexion"])
    nodes = layout["nodes"]
    edges = layout["edges"]
    dashed = layout.get("dashed", [])

    cw = canvas.winfo_width()  or 700
    ch = canvas.winfo_height() or 120

    n = len(nodes)
    pad = 60
    spacing = (cw - 2 * pad) / max(n - 1, 1)
    y_mid = ch // 2

    pos = {}
    for i, node in enumerate(nodes):
        x = pad + i * spacing
        pos[node] = (x, y_mid)

    # Draw edges
    for src, dst in edges:
        if src not in pos or dst not in pos: continue
        x1, y1 = pos[src]
        x2, y2 = pos[dst]
        is_dashed = (src, dst) in dashed
        dash = (5, 3) if is_dashed else ()
        # Curved return edges (revise loops)
        if x2 < x1:
            canvas.create_line(x1, y1, x1, y1 - 35, x2, y2 - 35, x2, y2,
                               fill=BORDER, width=1, smooth=True,
                               dash=dash, arrow=tk.LAST, arrowshape=(8,10,4))
        else:
            canvas.create_line(x1, y1, x2, y2,
                               fill=TEXT_DIM, width=1, dash=dash,
                               arrow=tk.LAST, arrowshape=(8,10,4))

    # Draw nodes
    R = 22
    for node in nodes:
        if node not in pos: continue
        x, y = pos[node]
        color = NODE_COLORS.get(node, ACCENT)
        is_active = node == active_node
        fill = color if is_active else PANEL
        outline = color
        lw = 3 if is_active else 1
        canvas.create_oval(x-R, y-R, x+R, y+R, fill=fill, outline=outline, width=lw)
        label = node.replace("_"," ").replace("wp ","").replace("legal ","")
        canvas.create_text(x, y + R + 10, text=label,
                           fill=color if is_active else TEXT_DIM,
                           font=("Consolas", 7))


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════════
class AgentHarnessV3(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("AgentHarness v3")
        self.geometry("1380x860")
        self.minsize(960, 640)
        self.configure(bg=BG)

        self._running    = False
        self._thread     = None
        self._active_node = ""
        self._last_state  = {}

        self._setup_fonts()
        self._build_ui()
        self._poll_log()
        self.after(300, self._check_api)

    # ── Fonts ────────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.fH  = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.fL  = tkfont.Font(family="Segoe UI", size=10)
        self.fS  = tkfont.Font(family="Segoe UI", size=9)
        self.fM  = tkfont.Font(family="Consolas",  size=10)
        self.fMs = tkfont.Font(family="Consolas",  size=9)
        self.fB  = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.fSc = tkfont.Font(family="Segoe UI", size=24, weight="bold")

    # ── Top-level layout ─────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=PANEL, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⬡  AgentHarness", font=self.fH, bg=PANEL, fg=ACCENT).pack(side=tk.LEFT, padx=16, pady=10)
        tk.Label(hdr, text="v3  ·  LangGraph Native", font=self.fL, bg=PANEL, fg=TEXT_DIM).pack(side=tk.LEFT)
        self._api_lbl = tk.Label(hdr, text="● API: checking…", font=self.fL, bg=PANEL, fg=WARNING)
        self._api_lbl.pack(side=tk.RIGHT, padx=16)
        self._lg_lbl = tk.Label(hdr,
            text="● LangGraph: OK" if LANGGRAPH_OK else "⚠ LangGraph: NOT INSTALLED",
            font=self.fL, bg=PANEL, fg=SUCCESS if LANGGRAPH_OK else ERROR)
        self._lg_lbl.pack(side=tk.RIGHT, padx=8)

        # Graph visualizer strip
        viz_frame = tk.Frame(self, bg=PANEL, height=110)
        viz_frame.pack(fill=tk.X, pady=(0, 0))
        viz_frame.pack_propagate(False)
        self._canvas = tk.Canvas(viz_frame, bg=PANEL, highlightthickness=0, height=110)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self._canvas.bind("<Configure>", lambda e: self._redraw_graph())

        # Main paned
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(paned, bg=PANEL, width=340)
        left.pack_propagate(False)
        paned.add(left, minsize=280)
        self._build_controls(left)

        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=440)
        self._build_right(right)

    # ── Controls ─────────────────────────────────────────────────────────────
    def _build_controls(self, p):
        def sec(title):
            tk.Label(p, text=title.upper(),
                     font=tkfont.Font(family="Segoe UI", size=8, weight="bold"),
                     bg=PANEL, fg=TEXT_DIM).pack(anchor=tk.W, padx=14, pady=(12,2))

        # Graph type
        sec("Graph")
        self._graph_var = tk.StringVar(value="reflexion")
        gf = tk.Frame(p, bg=PANEL)
        gf.pack(fill=tk.X, padx=12, pady=(0,6))
        for g in GRAPHS:
            tk.Radiobutton(
                gf, text=g.capitalize().replace("-"," "), variable=self._graph_var,
                value=g, bg=PANEL, fg=TEXT, selectcolor=ACCENT,
                activebackground=PANEL, font=self.fS, cursor="hand2",
                command=self._redraw_graph
            ).pack(side=tk.LEFT, padx=(0,8))

        # Team / Agent group
        sec("Team")
        self._team_var = tk.StringVar(value=list(AGENT_REGISTRY.keys())[0])
        team_combo = ttk.Combobox(p, textvariable=self._team_var,
                                  values=list(AGENT_REGISTRY.keys()),
                                  state="readonly", font=self.fL)
        team_combo.pack(fill=tk.X, padx=12, pady=(0,6))
        team_combo.bind("<<ComboboxSelected>>", self._on_team_change)
        self._style_combo(team_combo)

        # Agent
        sec("Agent")
        self._agent_var = tk.StringVar(value=ALL_AGENTS[0])
        self._agent_combo = ttk.Combobox(p, textvariable=self._agent_var,
                                         values=ALL_AGENTS, state="readonly", font=self.fL)
        self._agent_combo.pack(fill=tk.X, padx=12, pady=(0,6))
        self._style_combo(self._agent_combo)

        # Project
        sec("Project")
        self._proj_var = tk.StringVar(value=PROJECTS[0])
        proj_combo = ttk.Combobox(p, textvariable=self._proj_var,
                                  values=PROJECTS, state="readonly", font=self.fL)
        proj_combo.pack(fill=tk.X, padx=12, pady=(0,6))
        self._style_combo(proj_combo)

        # Task
        sec("Task")
        self._task = tk.Text(p, height=7, font=self.fMs, bg=HIGHLIGHT, fg=TEXT,
                             insertbackground=TEXT, relief=tk.FLAT, padx=8, pady=6, wrap=tk.WORD)
        self._task.pack(fill=tk.X, padx=12, pady=(0,4))
        ph = "Describe the task…"
        self._task.insert("1.0", ph)
        self._task.bind("<FocusIn>",  lambda e: self._task.delete("1.0", tk.END) if self._task.get("1.0","end-1c")==ph else None)
        self._task.bind("<FocusOut>", lambda e: self._task.insert("1.0", ph) if not self._task.get("1.0","end-1c").strip() else None)

        # Max revisions
        rev_row = tk.Frame(p, bg=PANEL)
        rev_row.pack(fill=tk.X, padx=12, pady=(0,8))
        tk.Label(rev_row, text="Max revisions:", font=self.fS, bg=PANEL, fg=TEXT_DIM).pack(side=tk.LEFT)
        self._max_rev = tk.IntVar(value=3)
        for v in [1,2,3,5]:
            tk.Radiobutton(rev_row, text=str(v), variable=self._max_rev, value=v,
                           bg=PANEL, fg=TEXT, selectcolor=ACCENT, font=self.fS,
                           activebackground=PANEL).pack(side=tk.LEFT, padx=3)

        # Buttons
        btn_frame = tk.Frame(p, bg=PANEL)
        btn_frame.pack(fill=tk.X, padx=12, pady=(4,12))

        self._run_btn = tk.Button(btn_frame, text="▶  Run Agent",
            font=self.fB, bg=ACCENT, fg="white", relief=tk.FLAT,
            activebackground=ACCENT2, cursor="hand2",
            padx=14, pady=8, command=self._run_agent)
        self._run_btn.pack(fill=tk.X, pady=(0,4))

        self._stop_btn = tk.Button(btn_frame, text="■  Stop",
            font=self.fB, bg=ERROR, fg="white", relief=tk.FLAT,
            activebackground="#b91c1c", cursor="hand2",
            padx=14, pady=6, command=self._stop_agent, state=tk.DISABLED)
        self._stop_btn.pack(fill=tk.X)

        # Score display
        self._score_lbl = tk.Label(p, text="—", font=self.fSc, bg=PANEL, fg=TEXT_DIM)
        self._score_lbl.pack(pady=(8,0))
        tk.Label(p, text="Last Score", font=self.fS, bg=PANEL, fg=TEXT_DIM).pack()

        # API key entry
        sec("OpenAI API Key")
        self._key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY",""))
        key_entry = tk.Entry(p, textvariable=self._key_var, show="•",
                             font=self.fMs, bg=HIGHLIGHT, fg=TEXT,
                             insertbackground=TEXT, relief=tk.FLAT)
        key_entry.pack(fill=tk.X, padx=12, pady=(0,4))
        tk.Button(p, text="Save Key", font=self.fS, bg=BORDER, fg=TEXT,
                  relief=tk.FLAT, cursor="hand2",
                  command=self._save_key).pack(padx=12, pady=(0,8), anchor=tk.W)

    # ── Right panel ───────────────────────────────────────────────────────────
    def _build_right(self, p):
        nb = ttk.Notebook(p)
        nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._style_notebook(nb)

        # Tab 1 — Live Log
        log_tab = tk.Frame(nb, bg=BG)
        nb.add(log_tab, text=" 📟 Live Log ")
        self._log = scrolledtext.ScrolledText(log_tab, font=self.fMs, bg=BG, fg=TEXT,
                                               insertbackground=TEXT, relief=tk.FLAT,
                                               state=tk.DISABLED, wrap=tk.WORD)
        self._log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._log.tag_configure("bold", font=tkfont.Font(family="Consolas", size=10, weight="bold"))

        btn_row = tk.Frame(log_tab, bg=BG)
        btn_row.pack(fill=tk.X, padx=4, pady=(0,4))
        tk.Button(btn_row, text="Clear Log", font=self.fS, bg=BORDER, fg=TEXT,
                  relief=tk.FLAT, cursor="hand2",
                  command=lambda: self._clear_log()).pack(side=tk.LEFT, padx=4)

        # Tab 2 — Output
        out_tab = tk.Frame(nb, bg=BG)
        nb.add(out_tab, text=" 📄 Output ")
        self._output = scrolledtext.ScrolledText(out_tab, font=self.fM, bg=BG, fg=TEXT,
                                                  insertbackground=TEXT, relief=tk.FLAT,
                                                  state=tk.DISABLED, wrap=tk.WORD)
        self._output.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        tk.Button(out_tab, text="Copy Output", font=self.fS, bg=BORDER, fg=TEXT,
                  relief=tk.FLAT, cursor="hand2",
                  command=self._copy_output).pack(anchor=tk.W, padx=4, pady=(0,4))

        # Tab 3 — Skill Viewer
        skill_tab = tk.Frame(nb, bg=BG)
        nb.add(skill_tab, text=" 🧠 Skill ")
        ctrl = tk.Frame(skill_tab, bg=BG)
        ctrl.pack(fill=tk.X, padx=4, pady=4)
        tk.Button(ctrl, text="Load Skill for Agent", font=self.fS, bg=ACCENT, fg="white",
                  relief=tk.FLAT, cursor="hand2",
                  command=self._load_skill_view).pack(side=tk.LEFT, padx=4)
        self._skill_ver_lbl = tk.Label(ctrl, text="", font=self.fS, bg=BG, fg=TEXT_DIM)
        self._skill_ver_lbl.pack(side=tk.LEFT, padx=8)
        self._skill_view = scrolledtext.ScrolledText(skill_tab, font=self.fMs, bg=BG, fg=TEXT,
                                                      insertbackground=TEXT, relief=tk.FLAT,
                                                      wrap=tk.WORD)
        self._skill_view.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 4 — Run History
        hist_tab = tk.Frame(nb, bg=BG)
        nb.add(hist_tab, text=" 📊 History ")
        cols = ("run_id","agent","project","graph","score","status","date")
        self._tree = ttk.Treeview(hist_tab, columns=cols, show="headings",
                                   selectmode="browse")
        for col, w in zip(cols, [70,180,120,110,60,70,140]):
            self._tree.heading(col, text=col.capitalize())
            self._tree.column(col, width=w, minwidth=50)
        vsb = ttk.Scrollbar(hist_tab, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        tk.Button(hist_tab, text="↻  Refresh", font=self.fS, bg=BORDER, fg=TEXT,
                  relief=tk.FLAT, cursor="hand2",
                  command=self._refresh_history).pack(anchor=tk.W, padx=4, pady=(0,4))
        self._refresh_history()
        nb.select(0)

    # ── Styling helpers ───────────────────────────────────────────────────────
    def _style_combo(self, w):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=HIGHLIGHT, background=PANEL,
                        foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER, relief="flat")

    def _style_notebook(self, nb):
        style = ttk.Style()
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=TEXT_DIM,
                        padding=[10,4], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", BG)],
                  foreground=[("selected", ACCENT)])

    # ── Event handlers ────────────────────────────────────────────────────────
    def _on_team_change(self, *_):
        team = self._team_var.get()
        agents = AGENT_REGISTRY.get(team, ALL_AGENTS)
        self._agent_combo["values"] = agents
        self._agent_var.set(agents[0])

    def _redraw_graph(self, *_):
        self.after(50, lambda: draw_graph(self._canvas, self._graph_var.get(), self._active_node))

    def _check_api(self):
        key = os.environ.get("OPENAI_API_KEY","")
        if key and key.startswith("sk-"):
            self._api_lbl.config(text="● API: Connected", fg=SUCCESS)
        else:
            self._api_lbl.config(text="● API: No key set", fg=ERROR)

    def _save_key(self):
        key = self._key_var.get().strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
            self._check_api()
            q("✓ API key saved for this session.", SUCCESS)

    def _clear_log(self):
        self._log.config(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.config(state=tk.DISABLED)

    def _copy_output(self):
        txt = self._output.get("1.0", tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(txt)
        q("✓ Output copied to clipboard.", SUCCESS)

    def _load_skill_view(self):
        agent = self._agent_var.get()
        content = read_agent_skill_file(agent)
        skill_name = agent.replace("-","_")
        db_content, version = db_load_skill(skill_name)
        final = db_content if db_content else content
        self._skill_view.config(state=tk.NORMAL)
        self._skill_view.delete("1.0", tk.END)
        if final:
            self._skill_view.insert("1.0", final)
            self._skill_ver_lbl.config(text=f"v{version} — {agent}", fg=ACCENT)
        else:
            self._skill_view.insert("1.0", f"No skill file found for: {agent}")
            self._skill_ver_lbl.config(text="", fg=TEXT_DIM)

    def _refresh_history(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        for row in db_load_runs():
            run_id, agent, proj, graph, score, status, ts = row
            score_str = f"{score:.2f}" if score is not None else "—"
            tag = "good" if (score or 0) >= 0.75 else "warn"
            self._tree.insert("", tk.END, values=(run_id, agent, proj, graph, score_str, status, ts[:16]), tags=(tag,))
        self._tree.tag_configure("good", foreground=SUCCESS)
        self._tree.tag_configure("warn", foreground=WARNING)

    # ── Run agent ─────────────────────────────────────────────────────────────
    def _run_agent(self):
        if self._running:
            return

        if not LANGGRAPH_OK:
            messagebox.showerror("Missing Dependency",
                "LangGraph not installed.\n\npip install langgraph langchain-openai")
            return

        api_key = self._key_var.get().strip() or os.environ.get("OPENAI_API_KEY","")
        if not api_key or not api_key.startswith("sk-"):
            messagebox.showerror("API Key Required",
                "Enter your OpenAI API key in the field below the Stop button.")
            return

        os.environ["OPENAI_API_KEY"] = api_key

        agent   = self._agent_var.get()
        project = self._proj_var.get()
        task    = self._task.get("1.0", tk.END).strip()
        graph   = self._graph_var.get()
        max_rev = self._max_rev.get()

        if not task or task == "Describe the task…":
            messagebox.showwarning("No Task", "Enter a task description first.")
            return

        self._running = True
        self._run_btn.config(state=tk.DISABLED)
        self._stop_btn.config(state=tk.NORMAL)
        self._score_lbl.config(text="…", fg=WARNING)

        self._clear_log()
        q(f"{'='*55}", BORDER)
        q(f"  AGENTHARNESS v3 — {graph.upper()} GRAPH", ACCENT, bold=True)
        q(f"  Agent:   {agent}", TEXT)
        q(f"  Project: {project}", TEXT)
        q(f"  Task:    {task[:80]}{'...' if len(task)>80 else ''}", TEXT)
        q(f"{'='*55}", BORDER)

        self._thread = threading.Thread(
            target=self._run_thread_fn,
            args=(agent, project, task, graph, max_rev),
            daemon=True
        )
        self._thread.start()

    def _run_thread_fn(self, agent, project, task, graph_type, max_rev):
        try:
            builder = GRAPH_BUILDERS.get(graph_type, build_reflexion_graph)
            compiled = builder()
            state    = default_state(agent, project, task, graph_type, max_rev)

            # Stream execution — update active node highlight
            for chunk in compiled.stream(state):
                node_name = list(chunk.keys())[0]
                self._active_node = node_name
                self.after(0, self._redraw_graph)
                # Update output tab live if act/draft node
                if node_name in ("act","legal_draft","wp_implement","synthesize"):
                    out = chunk[node_name].get("output","")
                    if out:
                        self.after(0, lambda o=out: self._update_output(o))

            # Final state from last chunk
            final = list(chunk.values())[0] if chunk else {}
            self._last_state = final
            score = final.get("score", 0.0)

            self.after(0, lambda s=score: self._on_run_complete(s, final))

        except Exception as e:
            import traceback
            q(f"ERROR: {e}", ERROR, bold=True)
            q(traceback.format_exc(), ERROR)
            self.after(0, self._on_run_error)

    def _on_run_complete(self, score, final):
        self._running = False
        self._run_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)
        self._active_node = "save_memory"
        self._redraw_graph()

        color = SUCCESS if score >= 0.75 else (WARNING if score >= 0.5 else ERROR)
        self._score_lbl.config(text=f"{score:.2f}", fg=color)

        q(f"\n{'='*55}", BORDER)
        q(f"  COMPLETE — score:{score:.2f}  revisions:{final.get('revision_count',0)}  skill_v:{final.get('skill_version',1)}", SUCCESS, bold=True)
        critique = final.get("critique","")
        if critique:
            q(f"  Critique: {critique[:120]}", TEXT_DIM)
        q(f"{'='*55}", BORDER)

        self._update_output(final.get("output","(no output)"))
        self._refresh_history()
        self._active_node = ""

    def _on_run_error(self):
        self._running = False
        self._run_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)
        self._score_lbl.config(text="ERR", fg=ERROR)

    def _stop_agent(self):
        q("⚠ Stop requested — run will finish current node.", WARNING)
        self._running = False
        self._run_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)

    def _update_output(self, text):
        self._output.config(state=tk.NORMAL)
        self._output.delete("1.0", tk.END)
        self._output.insert("1.0", text)
        self._output.config(state=tk.DISABLED)

    # ── Log polling ───────────────────────────────────────────────────────────
    def _poll_log(self):
        while not log_queue.empty():
            item = log_queue.get_nowait()
            self._log.config(state=tk.NORMAL)
            tag = f"color_{id(item)}"
            self._log.tag_configure(tag, foreground=item["color"],
                                    font=tkfont.Font(family="Consolas", size=10,
                                                     weight="bold" if item.get("bold") else "normal"))
            self._log.insert(tk.END, item["text"] + "\n", tag)
            self._log.see(tk.END)
            self._log.config(state=tk.DISABLED)
        self.after(80, self._poll_log)


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = AgentHarnessV3()
    app.mainloop()

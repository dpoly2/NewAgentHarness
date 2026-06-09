"""
AgentHarness Hub — Shared LangGraph Nodes
hub_nodes.py

All graph node functions extracted from main_m365.py and shared between:
  - hub_server.py  (server execution, always-on)
  - main_m365.py   (desktop fallback, when Hub is offline)

Node functions are pure Python — no Tkinter, no GUI references.
Progress is reported via an injected `emit` callable so the caller
can send WebSocket events (Hub) or GUI queue events (Desktop).
"""

from __future__ import annotations
import json
import os
import uuid
from pathlib import Path
from typing import Callable, TypedDict, List, Annotated

# ── Paths (resolved relative to this file) ───────────────────────────────────
HERE       = Path(__file__).parent
HARNESS    = HERE.parent.parent
SKILLS_DIR = HARNESS.parent / "agents" / "projects"

# ── LangGraph imports ─────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGGRAPH_OK = True
except ImportError:
    LANGGRAPH_OK = False
    print("[hub_nodes] WARNING: LangGraph not installed — nodes will not execute")

# ── DB imports ────────────────────────────────────────────────────────────────
from hub_db import (
    save_run, save_skill, load_skill, load_memory_context
)

# ── LLM factory ──────────────────────────────────────────────────────────────
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

def _llm(temperature: float = 0.2) -> "ChatOpenAI":
    return ChatOpenAI(
        model=MODEL,
        temperature=temperature,
        api_key=os.environ.get("OPENAI_API_KEY", "")
    )


# ── Agent State ───────────────────────────────────────────────────────────────
if LANGGRAPH_OK:
    class AgentState(TypedDict):
        run_id:         str
        agent_id:       str
        project:        str
        graph_type:     str
        task:           str
        skill_name:     str
        skill_content:  str
        skill_version:  int
        memory_context: str
        output:         str
        score:          float
        critique:       str
        revision_count: int
        max_revisions:  int
        messages:       Annotated[List, add_messages]
        cancel_flag:    object   # threading.Event — checked between nodes


# ── Emit helper ───────────────────────────────────────────────────────────────
_NOOP_EMIT: Callable = lambda event_type, **data: None

def _e(emit: Callable, event_type: str, **data):
    """Safe emit — never raises."""
    try:
        emit(event_type, **data)
    except Exception:
        pass


# ── Skill file reader ─────────────────────────────────────────────────────────
def read_agent_skill_file(agent_id: str) -> str:
    """Read the agent's .md skill file from disk."""
    for md in SKILLS_DIR.rglob(f"{agent_id}.md"):
        return md.read_text(encoding="utf-8", errors="ignore")
    return ""


def write_agent_skill_file(agent_id: str, content: str):
    """Write updated skill content back to disk."""
    for md in SKILLS_DIR.rglob(f"{agent_id}.md"):
        md.write_text(content, encoding="utf-8")
        return
    # If no file exists, create in first matching project dir
    target = SKILLS_DIR / "global" / f"{agent_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# ── State initializer ─────────────────────────────────────────────────────────
def make_initial_state(config: dict) -> dict:
    """
    Build the initial AgentState dict from a job config.
    config keys: agent_id, project, graph, task, max_revisions
    """
    agent_id   = config["agent_id"]
    skill_name = agent_id.replace("-", "_")
    skill_content, skill_version = load_skill(skill_name)
    if not skill_content:
        skill_content = read_agent_skill_file(agent_id)
    memory_context = load_memory_context(agent_id)

    return {
        "run_id":         config.get("run_id") or uuid.uuid4().hex[:8],
        "agent_id":       agent_id,
        "project":        config.get("project", "global"),
        "graph_type":     config.get("graph", "reflexion"),
        "task":           config["task"],
        "skill_name":     skill_name,
        "skill_content":  skill_content,
        "skill_version":  skill_version,
        "memory_context": memory_context,
        "output":         "",
        "score":          0.0,
        "critique":       "",
        "revision_count": 0,
        "max_revisions":  config.get("max_revisions", 2),
        "messages":       [],
        "cancel_flag":    config.get("cancel_flag"),
    }


# ── Cancellation check ────────────────────────────────────────────────────────
def _cancelled(state: dict) -> bool:
    flag = state.get("cancel_flag")
    return flag is not None and flag.is_set()


# ════════════════════════════════════════════════════════════════════════════════
# REFLEXION GRAPH NODES
# ════════════════════════════════════════════════════════════════════════════════

EVAL_SYS = (
    "Score the output on COMPLETION, QUALITY, and EFFICIENCY (each 0.0–1.0). "
    "overall = completion*0.5 + quality*0.35 + efficiency*0.15. "
    'Return JSON only — no markdown, no preamble: '
    '{"completion":0.0,"quality":0.0,"efficiency":0.0,"overall":0.0,"critique":"..."}'
)

REVISE_SYS = (
    "Rewrite the skill file to address the critique. "
    "Keep Markdown format. Increment the version number in the header. "
    "Output ONLY the rewritten skill file — no preamble."
)


def node_load_memory(state: dict, emit=_NOOP_EMIT) -> dict:
    _e(emit, "node_update", node="load_memory", status="running")
    skill_content, skill_version = load_skill(state["skill_name"])
    if not skill_content:
        skill_content = read_agent_skill_file(state["agent_id"])
    memory_context = load_memory_context(state["agent_id"])
    _e(emit, "node_update", node="load_memory", status="complete")
    return {**state,
            "skill_content": skill_content,
            "skill_version": skill_version,
            "memory_context": memory_context}


def node_act(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="act", status="running")

    parts = [
        f"You are the '{state['agent_id']}' agent for the '{state['project']}' project. "
        "Complete the task accurately and thoroughly."
    ]
    if state.get("skill_content"):
        parts.append(f"\n## Skill v{state['skill_version']}:\n{state['skill_content'][:3000]}")
    if state.get("memory_context"):
        parts.append(f"\n## Prior Context:\n{state['memory_context']}")
    if state["revision_count"] > 0:
        parts.append(f"\n## Critique to Address:\n{state['critique']}")

    if state["revision_count"] > 0 and state.get("messages"):
        msgs = state["messages"] + [HumanMessage(
            content=f"REVISION {state['revision_count']} — {state['critique']}\n\nTask: {state['task']}"
        )]
    else:
        msgs = [
            SystemMessage(content="\n\n".join(parts)),
            HumanMessage(content=state["task"])
        ]

    print(f"[ActNode] {state['agent_id']} rev={state['revision_count']} run={state['run_id']}")
    result = _llm(0.2).invoke(msgs)
    _e(emit, "node_update", node="act", status="complete")
    return {**state, "output": result.content, "messages": msgs + [result]}


def node_evaluate(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return {**state, "score": 0.0, "critique": "Cancelled"}
    _e(emit, "node_update", node="evaluate", status="running")

    result = _llm(0.0).invoke([
        SystemMessage(content=EVAL_SYS),
        HumanMessage(content=f"TASK:\n{state['task']}\n\nOUTPUT:\n{state['output']}")
    ])
    try:
        raw = result.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        d = json.loads(raw)
        score   = float(d.get("overall", 0.6))
        critique = d.get("critique", "")
    except Exception:
        score, critique = 0.6, f"Parse error: {result.content[:80]}"

    print(f"[EvaluateNode] SCORE={score:.2f} — {critique[:80]}")
    _e(emit, "node_update", node="evaluate", status="complete", score=score, critique=critique)
    return {**state, "score": score, "critique": critique}


def should_revise(state: dict) -> str:
    if _cancelled(state):
        return "save"
    if state["score"] < 0.75 and state["revision_count"] < state["max_revisions"]:
        print(f"[EvaluateNode] → REVISE (score {state['score']:.2f})")
        return "revise"
    print(f"[EvaluateNode] → SAVE (score {state['score']:.2f})")
    return "save"


def node_revise(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="revise", status="running")

    skill  = state.get("skill_content") or f"# Skill: {state['skill_name']} v1\n\nComplete tasks accurately."
    new_ver = state["skill_version"] + 1

    result = _llm(0.3).invoke([
        SystemMessage(content=REVISE_SYS),
        HumanMessage(content=(
            f"## Skill v{state['skill_version']}:\n{skill[:2000]}\n\n"
            f"## Task:\n{state['task']}\n\n"
            f"## Critique:\n{state['critique']}\n\n"
            f"Rewrite as v{new_ver}."
        ))
    ])

    new_content = result.content.strip()
    save_skill(state["agent_id"], state["skill_name"], new_ver, new_content,
               state["score"], state["critique"])
    write_agent_skill_file(state["agent_id"], new_content)

    print(f"[ReviseNode] {state['skill_name']} v{state['skill_version']}→v{new_ver}")
    _e(emit, "node_update", node="revise", status="complete", new_version=new_ver)
    return {**state,
            "skill_content":  new_content,
            "skill_version":  new_ver,
            "revision_count": state["revision_count"] + 1}


def node_save(state: dict, emit=_NOOP_EMIT) -> dict:
    _e(emit, "node_update", node="save", status="running")
    save_run({
        "run_id":         state["run_id"],
        "agent_id":       state["agent_id"],
        "project":        state["project"],
        "graph":          state.get("graph_type", "reflexion"),
        "task":           state["task"],
        "score":          state["score"],
        "critique":       state["critique"],
        "revision_count": state["revision_count"],
        "output":         state["output"],
        "skill_version":  state["skill_version"],
        "status":         "complete",
    })
    print(f"[SaveNode] Saved run={state['run_id']} score={state['score']:.2f}")
    _e(emit, "node_update", node="save", status="complete")
    return state


# ════════════════════════════════════════════════════════════════════════════════
# RESEARCH GRAPH NODES
# ════════════════════════════════════════════════════════════════════════════════

def node_plan(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="plan", status="running")
    result = _llm(0.2).invoke([
        SystemMessage(content="Output 3–5 specific, targeted search queries as a numbered list only."),
        HumanMessage(content=f"Research task: {state['task']}")
    ])
    print("[ResearchGraph:plan]")
    _e(emit, "node_update", node="plan", status="complete")
    return {**state, "output": f"PLAN:\n{result.content}", "messages": state["messages"] + [result]}


def node_search(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="search", status="running")
    result = _llm(0.1).invoke([
        SystemMessage(content=(
            "You are a grant and funding research specialist. "
            "For each query, provide: Grant/Program Name, Funder, Amount, "
            "Deadline, Eligibility Requirements, and Application Link."
        )),
        HumanMessage(content=f"Project: {state['project']}\n\nSearch queries:\n{state['output']}")
    ])
    print("[ResearchGraph:search]")
    _e(emit, "node_update", node="search", status="complete")
    return {**state, "output": result.content, "messages": state["messages"] + [result]}


def node_synthesize(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="synthesize", status="running")
    result = _llm(0.1).invoke([
        SystemMessage(content=(
            "Synthesize the research into 4 sections:\n"
            "1) TOP OPPORTUNITIES (ranked by fit + deadline)\n"
            "2) QUICK WINS (apply within 30 days)\n"
            "3) ACTION ITEMS (specific next steps)\n"
            "4) WATCH LIST (not yet open but promising)"
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nResearch:\n{state['output']}")
    ])
    print("[ResearchGraph:synthesize]")
    _e(emit, "node_update", node="synthesize", status="complete")
    return {**state, "output": result.content, "messages": state["messages"] + [result]}


# ════════════════════════════════════════════════════════════════════════════════
# WORDPRESS GRAPH NODES
# ════════════════════════════════════════════════════════════════════════════════

def node_wp_plan(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="wp_plan", status="running")
    result = _llm(0.1).invoke([
        SystemMessage(content=(
            "You are a senior WordPress developer. Output a numbered implementation plan "
            "covering: files to create/edit, functions, REST API endpoints, hooks/filters, "
            "and database operations needed."
        )),
        HumanMessage(content=f"Agent: {state['agent_id']} | Project: {state['project']}\n\nTask: {state['task']}")
    ])
    print("[WPGraph:plan]")
    _e(emit, "node_update", node="wp_plan", status="complete")
    return {**state, "output": f"PLAN:\n{result.content}", "messages": state["messages"] + [result]}


def node_wp_implement(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="wp_implement", status="running")
    result = _llm(0.1).invoke([
        SystemMessage(content=(
            "Senior WordPress developer. Produce complete, working code with: "
            "full PHP/JS, REST API endpoints, error handling, inline comments, "
            "and any SQL needed. No placeholders."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nImplementation Plan:\n{state['output']}")
    ])
    print("[WPGraph:implement]")
    _e(emit, "node_update", node="wp_implement", status="complete")
    return {**state, "output": result.content, "messages": state["messages"] + [result]}


def node_wp_verify(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="wp_verify", status="running")
    result = _llm(0.1).invoke([
        SystemMessage(content=(
            "WordPress QA engineer. Review the implementation for: "
            "security vulnerabilities, missing nonce checks, SQL injection, "
            "XSS, missing error handling, and PHP best practices. "
            "Output: ISSUES FOUND (list) and VERIFIED ITEMS (list)."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nImplementation:\n{state['output']}")
    ])
    print("[WPGraph:verify]")
    _e(emit, "node_update", node="wp_verify", status="complete")
    return {**state, "output": result.content, "messages": state["messages"] + [result]}


# ════════════════════════════════════════════════════════════════════════════════
# BUSINESS LAW GRAPH NODES
# ════════════════════════════════════════════════════════════════════════════════

def node_legal_analyze(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="legal_analyze", status="running")
    result = _llm(0.1).invoke([
        SystemMessage(content=(
            "Texas Bar-trained legal analyst. Analyze the legal request covering: "
            "applicable Texas statutes, relevant case law, key risk factors, "
            "compliance requirements, and jurisdiction notes. "
            "Be specific to Texas law."
        )),
        HumanMessage(content=f"Agent: {state['agent_id']}\n\nLegal Task: {state['task']}")
    ])
    print("[LegalGraph:analyze]")
    _e(emit, "node_update", node="legal_analyze", status="complete")
    return {**state, "output": f"ANALYSIS:\n{result.content}", "messages": state["messages"] + [result]}


def node_legal_draft(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="legal_draft", status="running")
    result = _llm(0.2).invoke([
        SystemMessage(content=(
            "Texas-licensed attorney drafting specialist. Produce a complete, "
            "professional legal document or memo based on the analysis. "
            "Include all standard clauses, definitions, and governing law provisions. "
            "Note: output is for informational purposes — advise client to have "
            "a licensed attorney review before execution."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nAnalysis:\n{state['output']}")
    ])
    print("[LegalGraph:draft]")
    _e(emit, "node_update", node="legal_draft", status="complete")
    return {**state, "output": result.content, "messages": state["messages"] + [result]}


def node_legal_review(state: dict, emit=_NOOP_EMIT) -> dict:
    if _cancelled(state): return state
    _e(emit, "node_update", node="legal_review", status="running")
    result = _llm(0.0).invoke([
        SystemMessage(content=(
            "Senior Texas legal reviewer. Check the draft for: "
            "missing clauses, ambiguous terms, legal accuracy, "
            "Texas-specific compliance gaps, and enforceability issues. "
            "Output: CRITICAL ISSUES (must fix), MINOR ISSUES (recommended), APPROVED SECTIONS."
        )),
        HumanMessage(content=f"Task: {state['task']}\n\nDraft:\n{state['output']}")
    ])
    print("[LegalGraph:review]")
    _e(emit, "node_update", node="legal_review", status="complete")
    return {**state, "output": result.content, "messages": state["messages"] + [result]}


# ════════════════════════════════════════════════════════════════════════════════
# GRAPH BUILDERS — returns a compiled LangGraph
# ════════════════════════════════════════════════════════════════════════════════

def _wrap(fn, emit):
    """Wrap a node function to inject the emit callable."""
    def wrapped(state): return fn(state, emit=emit)
    return wrapped


def build_reflexion_graph(emit=_NOOP_EMIT):
    if not LANGGRAPH_OK: raise RuntimeError("LangGraph not installed")
    g = StateGraph(AgentState)
    g.add_node("load_memory", _wrap(node_load_memory, emit))
    g.add_node("act",         _wrap(node_act,         emit))
    g.add_node("evaluate",    _wrap(node_evaluate,    emit))
    g.add_node("revise",      _wrap(node_revise,      emit))
    g.add_node("save",        _wrap(node_save,        emit))
    g.set_entry_point("load_memory")
    g.add_edge("load_memory", "act")
    g.add_edge("act",         "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save"})
    g.add_edge("revise",      "act")
    g.add_edge("save",        END)
    return g.compile()


def build_research_graph(emit=_NOOP_EMIT):
    if not LANGGRAPH_OK: raise RuntimeError("LangGraph not installed")
    g = StateGraph(AgentState)
    g.add_node("load_memory", _wrap(node_load_memory,  emit))
    g.add_node("plan",        _wrap(node_plan,         emit))
    g.add_node("search",      _wrap(node_search,       emit))
    g.add_node("synthesize",  _wrap(node_synthesize,   emit))
    g.add_node("evaluate",    _wrap(node_evaluate,     emit))
    g.add_node("revise",      _wrap(node_revise,       emit))
    g.add_node("save",        _wrap(node_save,         emit))
    g.set_entry_point("load_memory")
    g.add_edge("load_memory", "plan")
    g.add_edge("plan",        "search")
    g.add_edge("search",      "synthesize")
    g.add_edge("synthesize",  "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save"})
    g.add_edge("revise",      "synthesize")
    g.add_edge("save",        END)
    return g.compile()


def build_wordpress_graph(emit=_NOOP_EMIT):
    if not LANGGRAPH_OK: raise RuntimeError("LangGraph not installed")
    g = StateGraph(AgentState)
    g.add_node("load_memory",   _wrap(node_load_memory,    emit))
    g.add_node("wp_plan",       _wrap(node_wp_plan,        emit))
    g.add_node("wp_implement",  _wrap(node_wp_implement,   emit))
    g.add_node("wp_verify",     _wrap(node_wp_verify,      emit))
    g.add_node("evaluate",      _wrap(node_evaluate,       emit))
    g.add_node("revise",        _wrap(node_revise,         emit))
    g.add_node("save",          _wrap(node_save,           emit))
    g.set_entry_point("load_memory")
    g.add_edge("load_memory",   "wp_plan")
    g.add_edge("wp_plan",       "wp_implement")
    g.add_edge("wp_implement",  "wp_verify")
    g.add_edge("wp_verify",     "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save"})
    g.add_edge("revise",        "wp_plan")
    g.add_edge("save",          END)
    return g.compile()


def build_business_law_graph(emit=_NOOP_EMIT):
    if not LANGGRAPH_OK: raise RuntimeError("LangGraph not installed")
    g = StateGraph(AgentState)
    g.add_node("load_memory",    _wrap(node_load_memory,   emit))
    g.add_node("legal_analyze",  _wrap(node_legal_analyze, emit))
    g.add_node("legal_draft",    _wrap(node_legal_draft,   emit))
    g.add_node("legal_review",   _wrap(node_legal_review,  emit))
    g.add_node("evaluate",       _wrap(node_evaluate,      emit))
    g.add_node("revise",         _wrap(node_revise,        emit))
    g.add_node("save",           _wrap(node_save,          emit))
    g.set_entry_point("load_memory")
    g.add_edge("load_memory",    "legal_analyze")
    g.add_edge("legal_analyze",  "legal_draft")
    g.add_edge("legal_draft",    "legal_review")
    g.add_edge("legal_review",   "evaluate")
    g.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save": "save"})
    g.add_edge("revise",         "legal_analyze")
    g.add_edge("save",           END)
    return g.compile()


GRAPH_BUILDERS = {
    "reflexion":     build_reflexion_graph,
    "research":      build_research_graph,
    "wordpress":     build_wordpress_graph,
    "business-law":  build_business_law_graph,
}


def run_graph(config: dict, emit: Callable = _NOOP_EMIT) -> dict:
    """
    High-level entry point used by hub_server.py workers.

    config: { agent_id, project, graph, task, max_revisions, run_id?, cancel_flag? }
    emit:   callable(event_type: str, **data) — hub sends WebSocket events here
    Returns the final state dict.
    """
    graph_key = config.get("graph", "reflexion")
    builder   = GRAPH_BUILDERS.get(graph_key, build_reflexion_graph)
    graph     = builder(emit=emit)
    state     = make_initial_state(config)

    _e(emit, "run_started",
       run_id=state["run_id"], agent_id=state["agent_id"],
       graph=graph_key, project=state["project"])

    try:
        final = graph.invoke(state)
        _e(emit, "run_complete",
           run_id=final["run_id"], score=final["score"],
           critique=final["critique"],
           output_preview=final["output"][:300])
        return final
    except Exception as exc:
        error_msg = str(exc)
        print(f"[run_graph] ERROR: {error_msg}")
        _e(emit, "run_failed", run_id=state["run_id"], error=error_msg)
        raise

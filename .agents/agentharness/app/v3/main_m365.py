"""
AgentHarness v3 — M365-Style Desktop UI
=========================================
Microsoft 365-inspired layout:
  • Narrow left rail (icon nav, like Teams/Outlook)
  • Wide content area split into Command + Detail panes
  • Fluent Design colour tokens (Midnight Blue + Accent Violet)
  • Ribbon-style toolbar per section
  • Card-based agent grid in the Home view
  • Live LangGraph execution with animated node pipeline
  • Run history, skill viewer, settings — all in-pane

Run:  python .agents/agentharness/app/v3/main_m365.py
Deps: pip install langgraph langchain-openai langchain-core
"""

import sys, os, threading, queue, json, uuid, sqlite3
from datetime import datetime
from pathlib import Path
from functools import partial

# ── Paths ────────────────────────────────────────────────────────────────────
HERE       = Path(__file__).parent
HARNESS    = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
APP_ROOT   = AGENTS_DIR.parent
SKILLS_DIR = AGENTS_DIR / "agents" / "projects"
MEMORY_DIR = HARNESS / "memory"
DB_PATH    = MEMORY_DIR / "runs_v3.db"

for p in [str(AGENTS_DIR), str(APP_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from typing import TypedDict, List, Annotated
    from langgraph.graph.message import add_messages
    LANGGRAPH_OK = True
except ImportError:
    LANGGRAPH_OK = False

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font as tkfont

# ════════════════════════════════════════════════════════════════════════════
# FLUENT DESIGN TOKENS  (M365 / WinUI3 palette)
# ════════════════════════════════════════════════════════════════════════════
# Base surfaces
BG_CANVAS    = "#1f1f2e"   # App canvas (darkest)
BG_RAIL      = "#141422"   # Left nav rail
BG_PANEL     = "#252535"   # Cards, panels
BG_CARD      = "#2d2d42"   # Elevated card
BG_INPUT     = "#1a1a2e"   # Input fields
BG_HOVER     = "#333350"   # Hover state
BG_SELECTED  = "#3a3a5c"   # Selected state

# Accent / brand
ACCENT       = "#6264a7"   # M365 Teams blue-violet (primary)
ACCENT_LIGHT = "#8b8cc7"   # Lighter accent
ACCENT_DARK  = "#4a4b8c"   # Pressed accent
ACCENT2      = "#c879ff"   # Purple highlight (run active)
SUCCESS      = "#92c353"   # Teams green
WARNING      = "#f8b400"   # Amber
ERROR        = "#e74856"   # Red
INFO         = "#00bcf2"   # Cyan info

# Text
TEXT_PRIMARY = "#ffffff"
TEXT_BODY    = "#d6d6d6"
TEXT_MUTED   = "#8a8aaa"
TEXT_HINT    = "#555570"

# Borders / dividers
DIVIDER      = "#3a3a5c"
BORDER_CARD  = "#404060"

# Node colours (graph pipeline)
NC = {
    "load_memory":    "#00bcf2",
    "act":            "#8b5cf6",
    "evaluate":       "#f8b400",
    "revise":         "#e74856",
    "save_memory":    "#92c353",
    "plan":           "#06b6d4",
    "search":         "#3b82f6",
    "synthesize":     "#a855f7",
    "wp_plan":        "#06b6d4",
    "wp_implement":   "#8b5cf6",
    "wp_verify":      "#92c353",
    "legal_analyze":  "#f97316",
    "legal_draft":    "#ec4899",
    "legal_review":   "#14b8a6",
    "END":            "#475569",
}

# ════════════════════════════════════════════════════════════════════════════
# AGENT / PROJECT REGISTRY
# ════════════════════════════════════════════════════════════════════════════
AGENT_REGISTRY = {
    "Business Law":    ["business-law-project-lead","business-law-entity-agent","business-law-contracts-agent","business-law-ip-agent","business-law-employment-agent","business-law-realestate-agent","business-law-regulatory-agent"],
    "XFTC":            ["xftc-project-lead","xftc-plugin-dev","xftc-frontend-dev","xftc-payments-agent","xftc-qa-agent"],
    "Grants / YEPC":   ["grants-research-agent","grant-writer-agent","yepc-grant-writer-agent","yepc-real-estate-research-agent","yepc-project-manager"],
    "S2T Designs":     ["s2t-project-lead","s2t-webdev-agent","s2t-seo-agent"],
    "SmithCap Finance":["finance-cfo","finance-cpa","finance-tax-strategist","finance-bookkeeper","finance-advisor"],
    "Ministry":        ["ministry-project-lead","ministry-sermon-writer"],
    "Social Media":    ["social-project-lead","social-content-strategist","social-copywriter","social-ads-manager"],
    "Solar":           ["solar-project-lead","solar-marketing-agent"],
    "Sigma Signal":    ["sigma-signal-project-lead","sigma-signal-writer"],
    "Holdings":        ["holdings-project-lead","holdings-legal-agent","holdings-finance-agent","holdings-tax-agent","holdings-compliance-agent"],
}

TEAM_ICONS = {
    "Business Law":    "⚖️",
    "XFTC":            "🏃",
    "Grants / YEPC":   "📋",
    "S2T Designs":     "🎨",
    "SmithCap Finance":"💰",
    "Ministry":        "✝️",
    "Social Media":    "📱",
    "Solar":           "☀️",
    "Sigma Signal":    "Σ",
    "Holdings":        "🏢",
}

GRAPHS       = ["reflexion", "research", "wordpress", "business-law"]
GRAPH_ICONS  = {"reflexion":"🔄", "research":"🔍", "wordpress":"🌐", "business-law":"⚖️"}

PROJECTS = [
    "xftc","yepc","pbs-foundation","s2tdesigns","smithcap","smithcap-finance",
    "ministry","business-law","social-media","solar-repair","sigma-signal",
    "nutrue","the-elevation","travel","holdings",
]

ALL_AGENTS = [a for v in AGENT_REGISTRY.values() for a in v]

# ════════════════════════════════════════════════════════════════════════════
# GLOBAL LOG QUEUE
# ════════════════════════════════════════════════════════════════════════════
log_queue: queue.Queue = queue.Queue()

def qlog(msg, color=TEXT_BODY, bold=False):
    log_queue.put({"text": msg, "color": color, "bold": bold})

_orig_print = print
def _gui_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    _orig_print(msg, **kwargs)
    color = TEXT_MUTED
    if "[ActNode]"        in msg: color = NC["act"]
    elif "[EvaluateNode]" in msg: color = NC["evaluate"]
    elif "[MemoryNode]"   in msg: color = NC["load_memory"]
    elif "[ReviseNode]"   in msg: color = NC["revise"]
    elif "[LegalGraph]"   in msg: color = NC["legal_analyze"]
    elif "[ResearchGraph" in msg: color = NC["search"]
    elif "[WPGraph"       in msg: color = NC["wp_plan"]
    elif "REFLEXION RUN"  in msg: color = ACCENT_LIGHT
    elif "COMPLETE"       in msg: color = SUCCESS
    elif "ERROR"          in msg: color = ERROR
    elif "SCORE"          in msg: color = WARNING
    log_queue.put({"text": msg, "color": color, "bold": False})
import builtins
builtins.print = _gui_print

# ════════════════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════════════════
def _get_db():
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT, agent_id TEXT, project TEXT, graph TEXT,
        task TEXT, score REAL, critique TEXT,
        revision_count INTEGER, output TEXT,
        skill_version INTEGER, status TEXT, created_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT, skill_name TEXT, version INTEGER,
        content TEXT, avg_score REAL, last_critique TEXT, created_at TEXT)""")
    conn.commit()
    return conn

def db_save_run(r):
    c = _get_db()
    c.execute("INSERT INTO runs (run_id,agent_id,project,graph,task,score,critique,revision_count,output,skill_version,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (r["run_id"],r["agent_id"],r["project"],r.get("graph","reflexion"),r["task"][:500],r["score"],r["critique"],r["revision_count"],r["output"][:1000],r["skill_version"],r["status"],datetime.utcnow().isoformat()))
    c.commit(); c.close()

def db_load_runs(limit=100):
    c = _get_db()
    rows = c.execute("SELECT run_id,agent_id,project,graph,score,status,created_at FROM runs ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
    c.close(); return rows

def db_load_skill(skill_name):
    c = _get_db()
    row = c.execute("SELECT content,version FROM skills WHERE skill_name=? ORDER BY version DESC LIMIT 1",(skill_name,)).fetchone()
    c.close()
    return (row[0], row[1]) if row else ("",1)

def db_save_skill(agent_id, skill_name, version, content, score, critique):
    c = _get_db()
    c.execute("INSERT INTO skills (agent_id,skill_name,version,content,avg_score,last_critique,created_at) VALUES (?,?,?,?,?,?,?)",
        (agent_id,skill_name,version,content,score,critique,datetime.utcnow().isoformat()))
    c.commit(); c.close()

def db_agent_stats():
    """Returns dict of agent_id -> {last_score, runs, avg_score}"""
    c = _get_db()
    rows = c.execute("SELECT agent_id, COUNT(*), AVG(score), MAX(score) FROM runs GROUP BY agent_id").fetchall()
    c.close()
    return {r[0]: {"runs": r[1], "avg": round(r[2] or 0,2), "best": round(r[3] or 0,2)} for r in rows}

def _load_memory_context(agent_id):
    c = _get_db()
    row = c.execute("SELECT score,critique,skill_version,created_at FROM runs WHERE agent_id=? ORDER BY id DESC LIMIT 1",(agent_id,)).fetchone()
    c.close()
    if row: return f"Last run ({row[3][:10]}): score={row[0]:.2f}, skill_v{row[2]}. Critique: {row[1] or 'none'}"
    return "No prior runs."

def read_agent_skill_file(agent_id):
    for md in SKILLS_DIR.rglob(f"{agent_id}.md"):
        return md.read_text()
    return ""

# ════════════════════════════════════════════════════════════════════════════
# LANGGRAPH STATE + NODES  (identical logic to v3/main.py)
# ════════════════════════════════════════════════════════════════════════════
if LANGGRAPH_OK:
    class AgentState(TypedDict):
        agent_id: str; project: str; task: str; graph_type: str
        messages: Annotated[list, add_messages]
        output: str; score: float; critique: str
        revision_count: int; max_revisions: int
        skill_name: str; skill_version: int; skill_content: str
        memory_context: str; run_id: str

def default_state(agent_id, project, task, graph_type="reflexion", max_rev=3):
    sk = agent_id.replace("-","_")
    sc, sv = db_load_skill(sk)
    if not sc: sc = read_agent_skill_file(agent_id)
    return dict(agent_id=agent_id, project=project, task=task, graph_type=graph_type,
        messages=[], output="", score=0.0, critique="", revision_count=0, max_revisions=max_rev,
        skill_name=sk, skill_version=sv, skill_content=sc,
        memory_context=_load_memory_context(agent_id), run_id=str(uuid.uuid4())[:8])

MODEL = "gpt-4o"
def _llm(t=0.2): return ChatOpenAI(model=MODEL, temperature=t, api_key=os.environ.get("OPENAI_API_KEY",""))

def node_act(s):
    llm = _llm(0.2)
    parts = [f"You are the '{s['agent_id']}' agent for the '{s['project']}' project. Complete the task accurately."]
    if s.get("skill_content"): parts.append(f"\n## Skill v{s['skill_version']}:\n{s['skill_content'][:3000]}")
    if s.get("memory_context"): parts.append(f"\n## Prior Context:\n{s['memory_context']}")
    if s["revision_count"]>0: parts.append(f"\n## Critique to Address:\n{s['critique']}")
    msgs = [SystemMessage(content="\n\n".join(parts)), HumanMessage(content=s["task"])]
    if s["revision_count"]>0 and s.get("messages"):
        msgs = s["messages"] + [HumanMessage(content=f"REVISION {s['revision_count']} — {s['critique']}\n\nTask: {s['task']}")]
    print(f"[ActNode] {s['agent_id']} rev={s['revision_count']} run={s['run_id']}")
    r = llm.invoke(msgs)
    return {**s, "output": r.content, "messages": msgs+[r]}

EVAL_SYS = 'Score on COMPLETION, QUALITY, EFFICIENCY (0-1 each). JSON only: {"completion":0,"quality":0,"efficiency":0,"overall":0,"critique":"..."}\noverall=completion*0.5+quality*0.35+efficiency*0.15'
def node_evaluate(s):
    llm = _llm(0.0)
    r = llm.invoke([SystemMessage(content=EVAL_SYS), HumanMessage(content=f"TASK:\n{s['task']}\n\nOUTPUT:\n{s['output']}")])
    try:
        raw = r.content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        d = json.loads(raw); score=float(d.get("overall",0.6)); critique=d.get("critique","")
    except: score,critique = 0.6,f"Parse error: {r.content[:80]}"
    print(f"[EvaluateNode] SCORE={score:.2f} — {critique[:80]}")
    return {**s, "score": score, "critique": critique}

def should_revise(s):
    if s["score"]<0.75 and s["revision_count"]<s["max_revisions"]:
        print(f"[EvaluateNode] → REVISE"); return "revise"
    print(f"[EvaluateNode] → SAVE"); return "save"

REVISE_SYS = "Rewrite the skill file to fix the critique. Keep Markdown. Increment version. Output ONLY the rewritten skill."
def node_revise(s):
    llm = _llm(0.3)
    skill = s.get("skill_content") or f"# Skill: {s['skill_name']} v1\n\nComplete tasks accurately."
    nv = s["skill_version"]+1
    r = llm.invoke([SystemMessage(content=REVISE_SYS), HumanMessage(content=f"## Skill v{s['skill_version']}:\n{skill[:2000]}\n\n## Task:\n{s['task']}\n\n## Critique:\n{s['critique']}\n\nRewrite as v{nv}.")])
    db_save_skill(s["agent_id"],s["skill_name"],nv,r.content.strip(),s["score"],s["critique"])
    print(f"[ReviseNode] {s['skill_name']} v{s['skill_version']}→v{nv}")
    return {**s, "skill_content":r.content.strip(), "skill_version":nv, "revision_count":s["revision_count"]+1}

def node_save(s):
    db_save_run({"run_id":s["run_id"],"agent_id":s["agent_id"],"project":s["project"],"graph":s.get("graph_type","reflexion"),"task":s["task"],"score":s["score"],"critique":s["critique"],"revision_count":s["revision_count"],"output":s["output"],"skill_version":s["skill_version"],"status":"complete"})
    print(f"[MemoryNode] Saved run={s['run_id']} score={s['score']:.2f}")
    return s

def node_plan(s):
    r = _llm(0.2).invoke([SystemMessage(content="Output 3-5 specific search queries as a numbered list only."), HumanMessage(content=f"Research task: {s['task']}")])
    print("[ResearchGraph:plan]"); return {**s,"output":f"PLAN:\n{r.content}","messages":s["messages"]+[r]}

def node_search(s):
    r = _llm(0.1).invoke([SystemMessage(content="Grant/funding research specialist. For each query: name, funder, amount, deadline, eligibility, link."), HumanMessage(content=f"Project:{s['project']}\nQueries:\n{s['output']}")])
    print("[ResearchGraph:search]"); return {**s,"output":r.content,"messages":s["messages"]+[r]}

def node_synth(s):
    r = _llm(0.1).invoke([SystemMessage(content="Produce: 1)TOP OPPS 2)QUICK WINS 3)ACTION ITEMS 4)WATCH LIST"), HumanMessage(content=f"Task:{s['task']}\n\nResearch:\n{s['output']}")])
    print("[ResearchGraph:synthesize]"); return {**s,"output":r.content,"messages":s["messages"]+[r]}

def node_wp_plan(s):
    r = _llm(0.1).invoke([SystemMessage(content="WordPress developer. Output numbered implementation plan with files, functions, REST calls, hooks."), HumanMessage(content=f"{s['agent_id']} | {s['project']}\nTask:{s['task']}")])
    print("[WPGraph:plan]"); return {**s,"output":f"PLAN:\n{r.content}","messages":s["messages"]+[r]}

def node_wp_impl(s):
    r = _llm(0.1).invoke([SystemMessage(content="Senior WP dev. Produce complete working code with full PHP/JS, endpoints, error handling, comments."), HumanMessage(content=f"Task:{s['task']}\n\nPlan:\n{s['output']}")])
    print("[WPGraph:implement]"); return {**s,"output":r.content,"messages":s["messages"]+[r]}

def node_wp_verify(s):
    r = _llm(0.0).invoke([SystemMessage(content="WP code reviewer. Check: SQL injection, nonces, capability checks, WP standards, REST auth. If clean say 'VERIFIED'."), HumanMessage(content=f"Task:{s['task']}\n\nCode:\n{s['output']}")])
    print("[WPGraph:verify]"); return {**s,"output":r.content,"messages":s["messages"]+[r]}

LEGAL_SYS = "You are the business-law-project-lead trained to TX Bar Exam standard. Identify practice area, statute, legal standard, routing. Flag urgent risks 🔴."
def node_legal_analyze(s):
    sk = s.get("skill_content","")
    r = _llm(0.1).invoke([SystemMessage(content=LEGAL_SYS+(f"\n\n## TX Bar Skill:\n{sk[:2000]}" if sk else "")), HumanMessage(content=f"Legal task for {s['project']}:\n{s['task']}")])
    print("[LegalGraph:analyze]"); return {**s,"output":f"## LEGAL ANALYSIS\n{r.content}","messages":s["messages"]+[r]}

def node_legal_draft(s):
    r = _llm(0.2).invoke([SystemMessage(content="TX business law specialist. Draft the requested document/contract/plan. Cite TX statutes. End with: 'Review with a licensed Texas attorney before executing.'"), HumanMessage(content=f"Task:{s['task']}\n\nAnalysis:\n{s['output']}")])
    print("[LegalGraph:draft]"); return {**s,"output":r.content,"messages":s["messages"]+[r]}

def node_legal_review(s):
    r = _llm(0.0).invoke([SystemMessage(content="Senior TX attorney reviewing legal doc. Check: correct TX law, missing elements, enforceability, liability exposure. If clean say 'REVIEWED: No issues.'"), HumanMessage(content=f"Task:{s['task']}\n\nDoc:\n{s['output']}")])
    print("[LegalGraph:review]"); return {**s,"output":r.content,"messages":s["messages"]+[r]}

def _mem(s): return {**s,"memory_context":_load_memory_context(s["agent_id"]),"skill_content":read_agent_skill_file(s["agent_id"]) or s.get("skill_content","")}

def build_reflexion_graph():
    g=StateGraph(AgentState); g.add_node("load_memory",_mem); g.add_node("act",node_act); g.add_node("evaluate",node_evaluate); g.add_node("revise",node_revise); g.add_node("save_memory",node_save)
    g.set_entry_point("load_memory"); g.add_edge("load_memory","act"); g.add_edge("act","evaluate")
    g.add_conditional_edges("evaluate",should_revise,{"revise":"revise","save":"save_memory"}); g.add_edge("revise","act"); g.add_edge("save_memory",END); return g.compile()

def build_research_graph():
    g=StateGraph(AgentState); [g.add_node(n,f) for n,f in [("load_memory",_mem),("plan",node_plan),("search",node_search),("synthesize",node_synth),("evaluate",node_evaluate),("revise",node_revise),("save_memory",node_save)]]
    g.set_entry_point("load_memory"); g.add_edge("load_memory","plan"); g.add_edge("plan","search"); g.add_edge("search","synthesize"); g.add_edge("synthesize","evaluate")
    g.add_conditional_edges("evaluate",should_revise,{"revise":"revise","save":"save_memory"}); g.add_edge("revise","synthesize"); g.add_edge("save_memory",END); return g.compile()

def build_wordpress_graph():
    g=StateGraph(AgentState); [g.add_node(n,f) for n,f in [("load_memory",_mem),("wp_plan",node_wp_plan),("wp_implement",node_wp_impl),("wp_verify",node_wp_verify),("evaluate",node_evaluate),("revise",node_revise),("save_memory",node_save)]]
    g.set_entry_point("load_memory"); g.add_edge("load_memory","wp_plan"); g.add_edge("wp_plan","wp_implement"); g.add_edge("wp_implement","wp_verify"); g.add_edge("wp_verify","evaluate")
    g.add_conditional_edges("evaluate",should_revise,{"revise":"revise","save":"save_memory"}); g.add_edge("revise","wp_plan"); g.add_edge("save_memory",END); return g.compile()

def build_legal_graph():
    g=StateGraph(AgentState); [g.add_node(n,f) for n,f in [("load_memory",_mem),("legal_analyze",node_legal_analyze),("legal_draft",node_legal_draft),("legal_review",node_legal_review),("evaluate",node_evaluate),("revise",node_revise),("save_memory",node_save)]]
    g.set_entry_point("load_memory"); g.add_edge("load_memory","legal_analyze"); g.add_edge("legal_analyze","legal_draft"); g.add_edge("legal_draft","legal_review"); g.add_edge("legal_review","evaluate")
    g.add_conditional_edges("evaluate",should_revise,{"revise":"revise","save":"save_memory"}); g.add_edge("revise","legal_analyze"); g.add_edge("save_memory",END); return g.compile()


# ════════════════════════════════════════════════════════════════════════════
# LIGHT THEME TOKENS  (M365 Light mode)
# ════════════════════════════════════════════════════════════════════════════
LIGHT = {
    "BG_CANVAS": "#f3f2f1", "BG_RAIL": "#ffffff", "BG_PANEL": "#ffffff",
    "BG_CARD": "#faf9f8",   "BG_INPUT": "#f3f2f1", "BG_HOVER": "#edebe9",
    "BG_SELECTED": "#e1dfdd","ACCENT": "#6264a7",   "ACCENT_LIGHT": "#444791",
    "ACCENT_DARK": "#33367a","TEXT_PRIMARY": "#201f1e","TEXT_BODY": "#323130",
    "TEXT_MUTED": "#605e5c", "TEXT_HINT": "#a19f9d", "DIVIDER": "#edebe9",
    "BORDER_CARD": "#d2d0ce",
}
DARK = {
    "BG_CANVAS": "#1f1f2e", "BG_RAIL": "#141422", "BG_PANEL": "#252535",
    "BG_CARD": "#2d2d42",   "BG_INPUT": "#1a1a2e", "BG_HOVER": "#333350",
    "BG_SELECTED": "#3a3a5c","ACCENT": "#6264a7",  "ACCENT_LIGHT": "#8b8cc7",
    "ACCENT_DARK": "#4a4b8c","TEXT_PRIMARY": "#ffffff","TEXT_BODY": "#d6d6d6",
    "TEXT_MUTED": "#8a8aaa", "TEXT_HINT": "#555570", "DIVIDER": "#3a3a5c",
    "BORDER_CARD": "#404060",
}
_current_theme = "dark"

GRAPH_BUILDERS = {"reflexion":build_reflexion_graph,"research":build_research_graph,"wordpress":build_wordpress_graph,"business-law":build_legal_graph}

GRAPH_LAYOUTS = {
    "reflexion":    {"nodes":["load_memory","act","evaluate","revise","save_memory"],"edges":[("load_memory","act"),("act","evaluate"),("evaluate","save_memory"),("evaluate","revise"),("revise","act")],"loop":[("evaluate","revise"),("revise","act")]},
    "research":     {"nodes":["load_memory","plan","search","synthesize","evaluate","revise","save_memory"],"edges":[("load_memory","plan"),("plan","search"),("search","synthesize"),("synthesize","evaluate"),("evaluate","save_memory"),("evaluate","revise"),("revise","synthesize")],"loop":[("evaluate","revise"),("revise","synthesize")]},
    "wordpress":    {"nodes":["load_memory","wp_plan","wp_implement","wp_verify","evaluate","revise","save_memory"],"edges":[("load_memory","wp_plan"),("wp_plan","wp_implement"),("wp_implement","wp_verify"),("wp_verify","evaluate"),("evaluate","save_memory"),("evaluate","revise"),("revise","wp_plan")],"loop":[("evaluate","revise"),("revise","wp_plan")]},
    "business-law": {"nodes":["load_memory","legal_analyze","legal_draft","legal_review","evaluate","revise","save_memory"],"edges":[("load_memory","legal_analyze"),("legal_analyze","legal_draft"),("legal_draft","legal_review"),("legal_review","evaluate"),("evaluate","save_memory"),("evaluate","revise"),("revise","legal_analyze")],"loop":[("evaluate","revise"),("revise","legal_analyze")]},
}

def draw_pipeline(canvas, graph_type, active_node=""):
    canvas.delete("all")
    layout = GRAPH_LAYOUTS.get(graph_type, GRAPH_LAYOUTS["reflexion"])
    nodes = layout["nodes"]; edges = layout["edges"]; loops = layout.get("loop",[])
    cw = canvas.winfo_width() or 800; ch = canvas.winfo_height() or 90
    n = len(nodes); pad = 50; spacing = (cw - 2*pad) / max(n-1,1); y = ch//2
    pos = {node: (pad + i*spacing, y) for i,node in enumerate(nodes)}
    for src,dst in edges:
        if src not in pos or dst not in pos: continue
        x1,y1=pos[src]; x2,y2=pos[dst]
        is_loop = (src,dst) in loops
        col = BORDER_CARD
        dash = (4,3) if is_loop else ()
        if x2 < x1:
            canvas.create_line(x1,y1,x1,y1-32,x2,y2-32,x2,y2, fill=col, width=1, smooth=True, dash=dash, arrow=tk.LAST, arrowshape=(7,9,3))
        else:
            canvas.create_line(x1,y1,x2,y2, fill=col, width=1, dash=dash, arrow=tk.LAST, arrowshape=(7,9,3))
    R = 20
    for node in nodes:
        if node not in pos: continue
        x,y2 = pos[node]
        color = NC.get(node, ACCENT)
        is_active = node == active_node
        fill = color if is_active else BG_PANEL
        glow = 4 if is_active else 1
        if is_active:
            canvas.create_oval(x-R-4,y2-R-4,x+R+4,y2+R+4, fill="", outline=color, width=1, dash=(2,2))
        canvas.create_oval(x-R,y2-R,x+R,y2+R, fill=fill, outline=color, width=glow)
        short = node.replace("_"," ").replace("load ","").replace("save ","").replace("wp ","").replace("legal ","")
        canvas.create_text(x, y2+R+11, text=short, fill=color if is_active else TEXT_MUTED, font=("Segoe UI",7))


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP — M365 LAYOUT
# ════════════════════════════════════════════════════════════════════════════
class AgentHarnessM365(tk.Tk):

    NAV_ITEMS = [
        ("🏠", "Home",    "home"),
        ("▶",  "Run",     "run"),
        ("📊", "History", "history"),
        ("🧠", "Skills",  "skills"),
        ("⚙️", "Settings","settings"),
    ]

    def __init__(self):
        super().__init__()
        self.title("AgentHarness — Smith Capital Portfolio")
        self.geometry("1440x900")
        self.minsize(1100, 700)
        self.configure(bg=BG_CANVAS)

        self._running     = False
        self._thread      = None
        self._active_node = ""
        self._active_view = tk.StringVar(value="home")
        self._views       = {}
        self._theme       = "dark"          # "dark" | "light"
        self._notifs      = []              # list of {msg, color, ts}
        self._notif_count = tk.IntVar(value=0)
        self._notif_panel = None            # toplevel when open
        self._run_count   = 0               # total completed runs this session
        self._last_agent  = ""              # last agent that ran
        self._last_score  = None            # last score (float|None)
        self._cmd_palette = None            # command palette Toplevel

        self._setup_fonts()
        self._setup_styles()
        self._build_layout()
        self._poll_log()
        self.after(200, self._check_api)

    # ── Fonts ────────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.fTitle  = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        self.fH1     = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.fH2     = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.fBody   = tkfont.Font(family="Segoe UI", size=10)
        self.fSmall  = tkfont.Font(family="Segoe UI", size=9)
        self.fMono   = tkfont.Font(family="Consolas",  size=10)
        self.fMonoSm = tkfont.Font(family="Consolas",  size=9)
        self.fScore  = tkfont.Font(family="Segoe UI", size=28, weight="bold")
        self.fIcon   = tkfont.Font(family="Segoe UI", size=16)
        self.fNavLbl = tkfont.Font(family="Segoe UI", size=8)
        self.fBtn    = tkfont.Font(family="Segoe UI", size=10, weight="bold")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_PANEL,
                        foreground=TEXT_BODY, arrowcolor=TEXT_MUTED,
                        bordercolor=DIVIDER, relief="flat", selectbackground=BG_SELECTED)
        style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)])
        style.configure("Treeview", background=BG_PANEL, foreground=TEXT_BODY,
                        fieldbackground=BG_PANEL, borderwidth=0,
                        rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=BG_CARD, foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", BG_SELECTED)],
                  foreground=[("selected", TEXT_PRIMARY)])
        style.configure("Vertical.TScrollbar", background=BG_CARD,
                        troughcolor=BG_PANEL, borderwidth=0, arrowcolor=TEXT_MUTED)

    # ════════════════════════════════════════════════════════════════════════
    # LAYOUT SHELL: Rail + Title Bar + Content Area
    # ════════════════════════════════════════════════════════════════════════
    def _build_layout(self):
        # ── Title bar (slim, M365-style) ──────────────────────────────────
        titlebar = tk.Frame(self, bg=BG_RAIL, height=38)
        titlebar.pack(fill=tk.X, side=tk.TOP)
        titlebar.pack_propagate(False)
        tk.Label(titlebar, text="  ⬡  AgentHarness", font=self.fH2,
                 bg=BG_RAIL, fg=ACCENT_LIGHT).pack(side=tk.LEFT, padx=8, pady=6)
        tk.Label(titlebar, text="Smith Capital Portfolio  ·  LangGraph Native",
                 font=self.fSmall, bg=BG_RAIL, fg=TEXT_MUTED).pack(side=tk.LEFT)
        self._api_pill = tk.Label(titlebar, text="● API", font=self.fSmall,
                                  bg=BG_RAIL, fg=WARNING, padx=8)
        self._api_pill.pack(side=tk.RIGHT, padx=6)
        self._lg_pill = tk.Label(titlebar,
            text="LangGraph ✓" if LANGGRAPH_OK else "LangGraph ✗",
            font=self.fSmall, bg=BG_RAIL,
            fg=SUCCESS if LANGGRAPH_OK else ERROR, padx=8)
        self._lg_pill.pack(side=tk.RIGHT)

        # Theme toggle button
        self._theme_btn = tk.Label(titlebar, text="☀", font=self.fSmall,
                                   bg=BG_RAIL, fg=TEXT_MUTED, padx=6, cursor="hand2")
        self._theme_btn.pack(side=tk.RIGHT, padx=2)
        self._theme_btn.bind("<Button-1>", lambda e: self._toggle_theme())

        # Bell notification button
        self._bell_frame = tk.Frame(titlebar, bg=BG_RAIL, cursor="hand2")
        self._bell_frame.pack(side=tk.RIGHT, padx=4)
        self._bell_lbl = tk.Label(self._bell_frame, text="🔔", font=self.fSmall,
                                  bg=BG_RAIL, fg=TEXT_MUTED, padx=4)
        self._bell_lbl.pack(side=tk.LEFT)
        self._badge_lbl = tk.Label(self._bell_frame, textvariable=self._notif_count,
                                   font=tkfont.Font(family="Segoe UI",size=7,weight="bold"),
                                   bg=ERROR, fg="white", padx=3, pady=1)
        # badge hidden until there are notifs
        self._bell_frame.bind("<Button-1>", lambda e: self._toggle_notif_panel())
        self._bell_lbl.bind("<Button-1>",   lambda e: self._toggle_notif_panel())

        # ── Main body row ─────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_CANVAS)
        body.pack(fill=tk.BOTH, expand=True)

        # Left nav rail (narrow — icon + label like Teams)
        self._rail = tk.Frame(body, bg=BG_RAIL, width=72)
        self._rail.pack(side=tk.LEFT, fill=tk.Y)
        self._rail.pack_propagate(False)
        self._build_rail()

        # Content area
        self._content = tk.Frame(body, bg=BG_CANVAS)
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Build all views (stacked, shown/hidden via pack_forget)
        self._build_view_home()
        self._build_view_run()
        self._build_view_history()
        self._build_view_skills()
        self._build_view_settings()

        # ── VS Code-style status bar (bottom) ──────────────────────────────
        self._statusbar = tk.Frame(self, bg=ACCENT_DARK, height=24)
        self._statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self._statusbar.pack_propagate(False)
        # Left: current view / active agent
        self._sb_left = tk.Label(self._statusbar, text="  ⬡ AgentHarness  ·  Ready",
            font=tkfont.Font(family="Segoe UI",size=8), bg=ACCENT_DARK, fg=TEXT_PRIMARY, anchor=tk.W)
        self._sb_left.pack(side=tk.LEFT, padx=6)
        # Right: run count · last score · theme indicator
        self._sb_right = tk.Label(self._statusbar, text="",
            font=tkfont.Font(family="Segoe UI",size=8), bg=ACCENT_DARK, fg=TEXT_PRIMARY, anchor=tk.E)
        self._sb_right.pack(side=tk.RIGHT, padx=10)
        # Ctrl+K → command palette
        self.bind("<Control-k>", lambda e: self._open_cmd_palette())
        self.bind("<Control-K>", lambda e: self._open_cmd_palette())
        self._update_statusbar()

        self._show_view("home")

    # ── Left nav rail ────────────────────────────────────────────────────────
    def _build_rail(self):
        tk.Frame(self._rail, bg=BG_RAIL, height=8).pack()
        self._rail_btns = {}
        for icon, label, key in self.NAV_ITEMS:
            btn_frame = tk.Frame(self._rail, bg=BG_RAIL, cursor="hand2")
            btn_frame.pack(fill=tk.X, pady=2)
            icon_lbl = tk.Label(btn_frame, text=icon, font=self.fIcon,
                                bg=BG_RAIL, fg=TEXT_MUTED, pady=6)
            icon_lbl.pack()
            lbl = tk.Label(btn_frame, text=label, font=self.fNavLbl,
                           bg=BG_RAIL, fg=TEXT_MUTED)
            lbl.pack()
            self._rail_btns[key] = (btn_frame, icon_lbl, lbl)
            for w in [btn_frame, icon_lbl, lbl]:
                w.bind("<Button-1>", lambda e, k=key: self._show_view(k))
                w.bind("<Enter>", lambda e, f=btn_frame: f.configure(bg=BG_HOVER) or [c.configure(bg=BG_HOVER) for c in f.winfo_children()])
                w.bind("<Leave>", lambda e, f=btn_frame, k2=key: self._rail_leave(f, k2))

    def _rail_leave(self, frame, key):
        is_active = self._active_view.get() == key
        col = BG_SELECTED if is_active else BG_RAIL
        frame.configure(bg=col)
        for c in frame.winfo_children(): c.configure(bg=col)

    def _show_view(self, key):
        self._active_view.set(key)
        for k, (fr, il, ll) in self._rail_btns.items():
            if k == key:
                fr.configure(bg=BG_SELECTED); il.configure(bg=BG_SELECTED, fg=ACCENT_LIGHT); ll.configure(bg=BG_SELECTED, fg=ACCENT_LIGHT)
            else:
                fr.configure(bg=BG_RAIL); il.configure(bg=BG_RAIL, fg=TEXT_MUTED); ll.configure(bg=BG_RAIL, fg=TEXT_MUTED)
        for k, v in self._views.items():
            if k == key: v.pack(fill=tk.BOTH, expand=True)
            else: v.pack_forget()
        if key == "history": self._refresh_history()
        if key == "home":    self._refresh_home_cards()
        self._update_statusbar()

    # ════════════════════════════════════════════════════════════════════════
    # VIEW: HOME — Agent card grid (M365 App Launcher style)
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_home(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["home"] = f

        # Page header
        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20,10))
        tk.Label(hdr, text="Agent Teams", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        tk.Label(hdr, text="Smith Capital Portfolio — 10 Teams  ·  45 Agents", font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=16, pady=4)

        # Scrollable card grid
        outer = tk.Frame(f, bg=BG_CANVAS)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._home_canvas = tk.Canvas(outer, bg=BG_CANVAS, highlightthickness=0, yscrollcommand=vsb.set)
        self._home_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._home_canvas.yview)
        self._home_inner = tk.Frame(self._home_canvas, bg=BG_CANVAS)
        self._home_canvas.create_window((0,0), window=self._home_inner, anchor="nw")
        self._home_inner.bind("<Configure>", lambda e: self._home_canvas.configure(scrollregion=self._home_canvas.bbox("all")))

    def _refresh_home_cards(self):
        for w in self._home_inner.winfo_children(): w.destroy()
        stats = db_agent_stats()
        COLS = 4
        row_f = None
        for i, (team, agents) in enumerate(AGENT_REGISTRY.items()):
            if i % COLS == 0:
                row_f = tk.Frame(self._home_inner, bg=BG_CANVAS)
                row_f.pack(fill=tk.X, padx=8, pady=6)
            self._make_team_card(row_f, team, agents, stats)

    def _make_team_card(self, parent, team, agents, stats):
        card = tk.Frame(parent, bg=BG_CARD, relief=tk.FLAT, bd=0,
                        highlightbackground=BORDER_CARD, highlightthickness=1)
        card.pack(side=tk.LEFT, padx=8, ipadx=12, ipady=10, anchor=tk.N)

        icon = TEAM_ICONS.get(team, "●")
        tk.Label(card, text=icon, font=self.fTitle, bg=BG_CARD, fg=ACCENT_LIGHT).pack(anchor=tk.W, padx=12, pady=(10,2))
        tk.Label(card, text=team, font=self.fH2, bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor=tk.W, padx=12)
        tk.Frame(card, bg=DIVIDER, height=1).pack(fill=tk.X, padx=12, pady=6)

        for agent in agents:
            s = stats.get(agent, {})
            runs = s.get("runs", 0)
            avg  = s.get("avg", 0.0)
            color = SUCCESS if avg >= 0.75 else (WARNING if avg >= 0.5 else TEXT_MUTED)
            row = tk.Frame(card, bg=BG_CARD)
            row.pack(fill=tk.X, padx=12, pady=1)
            name_short = agent.replace(team.lower().replace(" ","-")+"-","").replace("business-law-","").replace("-agent","").replace("-"," ")
            tk.Label(row, text=f"  {name_short}", font=self.fSmall, bg=BG_CARD, fg=TEXT_BODY, anchor=tk.W, width=18).pack(side=tk.LEFT)
            if runs > 0:
                tk.Label(row, text=f"{avg:.2f}", font=self.fSmall, bg=BG_CARD, fg=color).pack(side=tk.RIGHT, padx=4)
                tk.Label(row, text=f"{runs}r", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.RIGHT)

        # Launch button
        tk.Button(card, text=f"▶ Run {team} Agent",
            font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=8, pady=4,
            activebackground=ACCENT_DARK,
            command=lambda t=team: self._launch_team(t)
        ).pack(fill=tk.X, padx=12, pady=(8,10))

    def _launch_team(self, team):
        agents = AGENT_REGISTRY.get(team, [])
        if agents:
            self._agent_var.set(agents[0])
        self._show_view("run")

    # ════════════════════════════════════════════════════════════════════════
    # VIEW: RUN — M365 Command/Detail split pane
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_run(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["run"] = f

        # Ribbon bar
        ribbon = tk.Frame(f, bg=BG_PANEL, height=44)
        ribbon.pack(fill=tk.X)
        ribbon.pack_propagate(False)
        tk.Label(ribbon, text="Run Agent", font=self.fH2, bg=BG_PANEL, fg=TEXT_PRIMARY).pack(side=tk.LEFT, padx=16, pady=10)

        self._run_btn = tk.Button(ribbon, text="▶  Run", font=self.fBtn, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, padx=16, pady=4, cursor="hand2",
            activebackground=ACCENT_DARK, command=self._run_agent)
        self._run_btn.pack(side=tk.LEFT, padx=8, pady=6)
        self._stop_btn = tk.Button(ribbon, text="■  Stop", font=self.fBtn, bg=ERROR, fg=TEXT_PRIMARY,
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2",
            activebackground="#b91c1c", state=tk.DISABLED, command=self._stop_agent)
        self._stop_btn.pack(side=tk.LEFT, padx=4, pady=6)

        self._score_pill = tk.Label(ribbon, text="Score: —", font=self.fH2, bg=BG_PANEL, fg=TEXT_MUTED, padx=12)
        self._score_pill.pack(side=tk.RIGHT, padx=12)

        # Graph pipeline strip
        pipe_frame = tk.Frame(f, bg=BG_PANEL, height=96)
        pipe_frame.pack(fill=tk.X)
        pipe_frame.pack_propagate(False)
        self._pipe_canvas = tk.Canvas(pipe_frame, bg=BG_PANEL, highlightthickness=0)
        self._pipe_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        self._pipe_canvas.bind("<Configure>", lambda e: self._redraw_pipe())

        # Separator
        tk.Frame(f, bg=DIVIDER, height=1).pack(fill=tk.X)

        # Command / Detail split
        split = tk.PanedWindow(f, orient=tk.HORIZONTAL, bg=BG_CANVAS, sashwidth=4, sashrelief=tk.FLAT)
        split.pack(fill=tk.BOTH, expand=True)

        # LEFT: Command panel (config)
        cmd = tk.Frame(split, bg=BG_PANEL, width=320)
        cmd.pack_propagate(False)
        split.add(cmd, minsize=260)
        self._build_command_panel(cmd)

        # RIGHT: Detail panel (tabs: log, output)
        detail = tk.Frame(split, bg=BG_CANVAS)
        split.add(detail, minsize=500)
        self._build_detail_panel(detail)

    def _build_command_panel(self, p):
        def sec(title):
            tk.Label(p, text=title, font=tkfont.Font(family="Segoe UI",size=8,weight="bold"),
                     bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor=tk.W, padx=14, pady=(14,2))

        sec("GRAPH TYPE")
        self._graph_var = tk.StringVar(value="reflexion")
        gf = tk.Frame(p, bg=BG_PANEL); gf.pack(fill=tk.X, padx=12, pady=(0,8))
        for g in GRAPHS:
            rb = tk.Radiobutton(gf, text=f"{GRAPH_ICONS[g]} {g.capitalize().replace('-',' ')}",
                variable=self._graph_var, value=g, bg=BG_PANEL, fg=TEXT_BODY,
                selectcolor=ACCENT, activebackground=BG_PANEL, font=self.fSmall,
                cursor="hand2", command=self._redraw_pipe)
            rb.pack(side=tk.LEFT, padx=(0,6))

        sec("TEAM")
        self._team_var = tk.StringVar(value=list(AGENT_REGISTRY.keys())[0])
        tc = ttk.Combobox(p, textvariable=self._team_var, values=list(AGENT_REGISTRY.keys()), state="readonly", font=self.fBody)
        tc.pack(fill=tk.X, padx=12, pady=(0,8))
        tc.bind("<<ComboboxSelected>>", self._on_team_change)

        sec("AGENT")
        self._agent_var = tk.StringVar(value=ALL_AGENTS[0])
        self._agent_cb = ttk.Combobox(p, textvariable=self._agent_var, values=ALL_AGENTS, state="readonly", font=self.fBody)
        self._agent_cb.pack(fill=tk.X, padx=12, pady=(0,8))

        sec("PROJECT")
        self._proj_var = tk.StringVar(value=PROJECTS[0])
        pc = ttk.Combobox(p, textvariable=self._proj_var, values=PROJECTS, state="readonly", font=self.fBody)
        pc.pack(fill=tk.X, padx=12, pady=(0,8))

        sec("TASK")
        self._task = tk.Text(p, height=8, font=self.fMonoSm, bg=BG_INPUT, fg=TEXT_BODY,
                             insertbackground=TEXT_BODY, relief=tk.FLAT, padx=8, pady=6, wrap=tk.WORD,
                             highlightthickness=1, highlightbackground=DIVIDER, highlightcolor=ACCENT)
        self._task.pack(fill=tk.X, padx=12, pady=(0,6))
        ph = "Describe the task for this agent…"
        self._task.insert("1.0", ph)
        self._task.bind("<FocusIn>",  lambda e: self._task.delete("1.0",tk.END) if self._task.get("1.0","end-1c")==ph else None)
        self._task.bind("<FocusOut>", lambda e: self._task.insert("1.0",ph) if not self._task.get("1.0","end-1c").strip() else None)

        sec("MAX REVISIONS")
        rev_row = tk.Frame(p, bg=BG_PANEL); rev_row.pack(fill=tk.X, padx=12, pady=(0,10))
        self._max_rev = tk.IntVar(value=3)
        for v in [1,2,3,5]:
            tk.Radiobutton(rev_row, text=str(v), variable=self._max_rev, value=v,
                bg=BG_PANEL, fg=TEXT_BODY, selectcolor=ACCENT, font=self.fSmall,
                activebackground=BG_PANEL).pack(side=tk.LEFT, padx=5)

    def _build_detail_panel(self, p):
        nb = ttk.Notebook(p)
        nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        style = ttk.Style()
        style.configure("TNotebook", background=BG_CANVAS, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_PANEL, foreground=TEXT_MUTED,
                        padding=[12,5], font=("Segoe UI",9))
        style.map("TNotebook.Tab", background=[("selected",BG_CANVAS)], foreground=[("selected",ACCENT_LIGHT)])

        # Tab: Live Log
        log_tab = tk.Frame(nb, bg=BG_CANVAS); nb.add(log_tab, text="  📟 Live Log  ")
        self._log = scrolledtext.ScrolledText(log_tab, font=self.fMonoSm, bg=BG_CANVAS, fg=TEXT_BODY,
            insertbackground=TEXT_BODY, relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD)
        self._log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        tk.Button(log_tab, text="Clear", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", command=self._clear_log).pack(anchor=tk.W, padx=6, pady=2)

        # Tab: Output
        out_tab = tk.Frame(nb, bg=BG_CANVAS); nb.add(out_tab, text="  📄 Output  ")
        self._output = scrolledtext.ScrolledText(out_tab, font=self.fMono, bg=BG_CANVAS, fg=TEXT_BODY,
            insertbackground=TEXT_BODY, relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD)
        self._output.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        tk.Button(out_tab, text="Copy", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", command=self._copy_output).pack(anchor=tk.W, padx=6, pady=2)

    # ════════════════════════════════════════════════════════════════════════
    # VIEW: HISTORY
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_history(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["history"] = f

        hdr = tk.Frame(f, bg=BG_CANVAS); hdr.pack(fill=tk.X, padx=24, pady=(20,8))
        tk.Label(hdr, text="Run History", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        tk.Button(hdr, text="↻ Refresh", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", command=self._refresh_history).pack(side=tk.RIGHT, padx=6)

        cols = ("run_id","agent","project","graph","score","status","date")
        tree_f = tk.Frame(f, bg=BG_CANVAS); tree_f.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)
        vsb = ttk.Scrollbar(tree_f, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree = ttk.Treeview(tree_f, columns=cols, show="headings", selectmode="browse", yscrollcommand=vsb.set)
        vsb.configure(command=self._tree.yview)
        for col, w in zip(cols,[70,190,120,110,65,75,150]):
            self._tree.heading(col, text=col.capitalize())
            self._tree.column(col, width=w, minwidth=50)
        self._tree.pack(fill=tk.BOTH, expand=True)

    def _refresh_history(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        for row in db_load_runs():
            run_id,agent,proj,graph,score,status,ts = row
            sc = f"{score:.2f}" if score is not None else "—"
            tag = "good" if (score or 0)>=0.75 else "warn"
            self._tree.insert("","end",values=(run_id,agent,proj,graph,sc,status,ts[:16]),tags=(tag,))
        self._tree.tag_configure("good",foreground=SUCCESS)
        self._tree.tag_configure("warn",foreground=WARNING)

    # ════════════════════════════════════════════════════════════════════════
    # VIEW: SKILLS
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_skills(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["skills"] = f

        hdr = tk.Frame(f, bg=BG_CANVAS); hdr.pack(fill=tk.X, padx=24, pady=(20,8))
        tk.Label(hdr, text="Skill Files", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)

        ctrl = tk.Frame(f, bg=BG_CANVAS); ctrl.pack(fill=tk.X, padx=16, pady=(0,8))
        tk.Label(ctrl, text="Agent:", font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(0,6))
        self._skill_agent_var = tk.StringVar(value=ALL_AGENTS[0])
        sc = ttk.Combobox(ctrl, textvariable=self._skill_agent_var, values=ALL_AGENTS, state="readonly", font=self.fBody, width=35)
        sc.pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl, text="Load Skill", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", command=self._load_skill_view).pack(side=tk.LEFT, padx=8)
        self._skill_ver_lbl = tk.Label(ctrl, text="", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED)
        self._skill_ver_lbl.pack(side=tk.LEFT, padx=8)

        self._skill_view = scrolledtext.ScrolledText(f, font=self.fMono, bg=BG_PANEL, fg=TEXT_BODY,
            insertbackground=TEXT_BODY, relief=tk.FLAT, wrap=tk.WORD,
            highlightthickness=1, highlightbackground=DIVIDER)
        self._skill_view.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0,12))

    def _load_skill_view(self):
        agent = self._skill_agent_var.get()
        content = read_agent_skill_file(agent)
        sk_name = agent.replace("-","_")
        db_content, version = db_load_skill(sk_name)
        final = db_content if db_content else content
        self._skill_view.config(state=tk.NORMAL)
        self._skill_view.delete("1.0", tk.END)
        self._skill_view.insert("1.0", final if final else f"No skill file found for: {agent}")
        self._skill_ver_lbl.config(text=f"v{version}  ·  {agent}" if final else "Not found", fg=ACCENT_LIGHT if final else ERROR)

    # ════════════════════════════════════════════════════════════════════════
    # VIEW: SETTINGS
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_settings(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["settings"] = f

        tk.Label(f, text="Settings", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(anchor=tk.W, padx=24, pady=(20,16))

        def card(parent, title):
            c = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_CARD, highlightthickness=1)
            c.pack(fill=tk.X, padx=16, pady=6, ipady=8)
            tk.Label(c, text=title, font=self.fH2, bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor=tk.W, padx=16, pady=(10,4))
            return c

        # API Key card
        api_card = card(f, "OpenAI API Key")
        key_row = tk.Frame(api_card, bg=BG_CARD); key_row.pack(fill=tk.X, padx=16, pady=(0,10))
        self._key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY",""))
        key_entry = tk.Entry(key_row, textvariable=self._key_var, show="•", font=self.fMono,
                             bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                             relief=tk.FLAT, width=52,
                             highlightthickness=1, highlightbackground=DIVIDER)
        key_entry.pack(side=tk.LEFT, padx=(0,8), ipady=4)
        tk.Button(key_row, text="Save", font=self.fBtn, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=12, pady=4, command=self._save_key).pack(side=tk.LEFT)
        self._api_status_full = tk.Label(api_card, text="", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED)
        self._api_status_full.pack(anchor=tk.W, padx=16, pady=(0,8))

        # Model info card
        info_card = card(f, "Model & Environment")
        for txt in [f"Model:       {MODEL}", f"LangGraph:   {'Installed ✓' if LANGGRAPH_OK else 'Not Installed ✗'}", f"DB Path:     {DB_PATH}", f"Skills Dir:  {SKILLS_DIR}"]:
            tk.Label(info_card, text=txt, font=self.fMono, bg=BG_CARD, fg=TEXT_MUTED, anchor=tk.W).pack(anchor=tk.W, padx=16, pady=1)
        tk.Frame(info_card, height=8, bg=BG_CARD).pack()

    # ════════════════════════════════════════════════════════════════════════
    # AGENT EXECUTION
    # ════════════════════════════════════════════════════════════════════════
    def _on_team_change(self, *_):
        team = self._team_var.get()
        agents = AGENT_REGISTRY.get(team, ALL_AGENTS)
        self._agent_cb["values"] = agents
        self._agent_var.set(agents[0])

    def _redraw_pipe(self, *_):
        self.after(40, lambda: draw_pipeline(self._pipe_canvas, self._graph_var.get(), self._active_node))

    def _check_api(self):
        key = os.environ.get("OPENAI_API_KEY","")
        if key and key.startswith("sk-"):
            self._api_pill.config(text="● API: Connected", fg=SUCCESS)
        else:
            self._api_pill.config(text="● API: No key", fg=ERROR)

    def _save_key(self):
        key = self._key_var.get().strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
            self._check_api()
            if hasattr(self,"_api_status_full"): self._api_status_full.config(text="✓ Key saved for this session.", fg=SUCCESS)
            qlog("✓ API key saved.", SUCCESS)

    def _clear_log(self):
        self._log.config(state=tk.NORMAL); self._log.delete("1.0",tk.END); self._log.config(state=tk.DISABLED)

    def _copy_output(self):
        txt = self._output.get("1.0",tk.END).strip()
        self.clipboard_clear(); self.clipboard_append(txt)
        qlog("✓ Output copied.", SUCCESS)

    def _run_agent(self):
        if self._running: return
        if not LANGGRAPH_OK:
            messagebox.showerror("Missing","pip install langgraph langchain-openai"); return
        api_key = self._key_var.get().strip() or os.environ.get("OPENAI_API_KEY","")
        if not api_key or not api_key.startswith("sk-"):
            messagebox.showerror("API Key","Enter your OpenAI API key in Settings."); return
        os.environ["OPENAI_API_KEY"] = api_key
        agent=self._agent_var.get(); project=self._proj_var.get()
        task=self._task.get("1.0",tk.END).strip(); graph=self._graph_var.get(); max_rev=self._max_rev.get()
        ph = "Describe the task for this agent…"
        if not task or task == ph:
            messagebox.showwarning("No Task","Enter a task first."); return
        self._running=True; self._run_btn.config(state=tk.DISABLED); self._stop_btn.config(state=tk.NORMAL)
        self._score_pill.config(text="Score: …", fg=WARNING)
        self._clear_log()
        qlog(f"{'─'*60}", DIVIDER)
        qlog(f"  {GRAPH_ICONS.get(graph,'▶')}  {graph.upper()}  ·  {agent}  ·  {project}", ACCENT_LIGHT, bold=True)
        qlog(f"  Task: {task[:90]}{'…' if len(task)>90 else ''}", TEXT_BODY)
        qlog(f"{'─'*60}", DIVIDER)
        self._show_view("run")
        self._thread = threading.Thread(target=self._exec_thread, args=(agent,project,task,graph,max_rev), daemon=True)
        self._thread.start()

    def _exec_thread(self, agent, project, task, graph_type, max_rev):
        try:
            compiled = GRAPH_BUILDERS.get(graph_type, build_reflexion_graph)()
            state    = default_state(agent, project, task, graph_type, max_rev)
            last_chunk = {}
            for chunk in compiled.stream(state):
                node_name = list(chunk.keys())[0]
                self._active_node = node_name
                self.after(0, self._redraw_pipe)
                if node_name in ("act","legal_draft","wp_implement","synthesize"):
                    out = chunk[node_name].get("output","")
                    if out: self.after(0, lambda o=out: self._set_output(o))
                last_chunk = chunk
            final = list(last_chunk.values())[0] if last_chunk else {}
            self.after(0, lambda s=final.get("score",0.0), fs=final: self._on_complete(s, fs))
        except Exception as e:
            import traceback
            qlog(f"ERROR: {e}", ERROR, bold=True)
            qlog(traceback.format_exc(), ERROR)
            self.after(0, self._on_error)

    def _on_complete(self, score, final):
        self._running=False; self._run_btn.config(state=tk.NORMAL); self._stop_btn.config(state=tk.DISABLED)
        self._active_node=""; self._redraw_pipe()
        color = SUCCESS if score>=0.75 else (WARNING if score>=0.5 else ERROR)
        self._score_pill.config(text=f"Score: {score:.2f}", fg=color)
        qlog(f"\n{'─'*60}", DIVIDER)
        qlog(f"  ✓ COMPLETE  score={score:.2f}  revisions={final.get('revision_count',0)}  skill_v={final.get('skill_version',1)}", SUCCESS, bold=True)
        agent_name = final.get('agent_id','agent')
        self._push_notif(f"✓ {agent_name} — score {score:.2f}  ({final.get('revision_count',0)} revisions)", color)
        if final.get("critique"): qlog(f"  Critique: {final['critique'][:120]}", TEXT_MUTED)
        qlog(f"{'─'*60}", DIVIDER)
        self._set_output(final.get("output","(no output)"))
        self._run_count += 1
        self._last_agent = final.get("agent_id", "")
        self._last_score = score
        self._update_statusbar()

    def _on_error(self):
        self._running=False; self._run_btn.config(state=tk.NORMAL); self._stop_btn.config(state=tk.DISABLED)
        self._score_pill.config(text="Score: ERR", fg=ERROR)
        self._push_notif("⚠ Agent run failed — check Live Log for details.", ERROR)
        self._update_statusbar()

    def _stop_agent(self):
        qlog("⚠ Stop requested — will finish current node.", WARNING)
        self._running=False; self._run_btn.config(state=tk.NORMAL); self._stop_btn.config(state=tk.DISABLED)

    def _set_output(self, text):
        self._output.config(state=tk.NORMAL); self._output.delete("1.0",tk.END)
        self._output.insert("1.0",text); self._output.config(state=tk.DISABLED)


    # ════════════════════════════════════════════════════════════════════════
    # THEME TOGGLE
    # ════════════════════════════════════════════════════════════════════════
    def _toggle_theme(self):
        self._theme = "light" if self._theme == "dark" else "dark"
        palette = LIGHT if self._theme == "light" else DARK
        self._theme_btn.config(text="🌙" if self._theme == "light" else "☀")
        self._apply_theme_palette(palette)

    def _apply_theme_palette(self, p):
        """Recursively recolour all widgets that use our palette variables."""
        bg_map = {
            BG_CANVAS: p["BG_CANVAS"], BG_RAIL: p["BG_RAIL"],
            BG_PANEL:  p["BG_PANEL"],  BG_CARD: p["BG_CARD"],
            BG_INPUT:  p["BG_INPUT"],  BG_HOVER: p["BG_HOVER"],
            BG_SELECTED: p["BG_SELECTED"],
        }
        fg_map = {
            TEXT_PRIMARY: p["TEXT_PRIMARY"], TEXT_BODY: p["TEXT_BODY"],
            TEXT_MUTED:   p["TEXT_MUTED"],   TEXT_HINT: p["TEXT_HINT"],
        }
        def _recolour(widget):
            try:
                bg = str(widget.cget("bg"))
                if bg in bg_map: widget.config(bg=bg_map[bg])
                fg = str(widget.cget("fg"))
                if fg in fg_map: widget.config(fg=fg_map[fg])
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                _recolour(child)
        _recolour(self)
        self.configure(bg=p["BG_CANVAS"])
        # Update ttk styles
        style = ttk.Style()
        style.configure("Treeview", background=p["BG_PANEL"], foreground=p["TEXT_BODY"], fieldbackground=p["BG_PANEL"])
        style.configure("Treeview.Heading", background=p["BG_CARD"], foreground=p["TEXT_MUTED"])

    # ════════════════════════════════════════════════════════════════════════
    # NOTIFICATION PANEL
    # ════════════════════════════════════════════════════════════════════════
    def _push_notif(self, msg: str, color: str = None):
        """Add a notification. Called from _on_complete, errors, etc."""
        if color is None: color = SUCCESS
        ts = datetime.now().strftime("%H:%M")
        self._notifs.insert(0, {"msg": msg, "color": color, "ts": ts})
        if len(self._notifs) > 50: self._notifs = self._notifs[:50]
        self._notif_count.set(len(self._notifs))
        # Show badge
        self._badge_lbl.pack(side=tk.LEFT)
        # Refresh panel if open
        if self._notif_panel and self._notif_panel.winfo_exists():
            self._build_notif_contents()

    def _toggle_notif_panel(self):
        if self._notif_panel and self._notif_panel.winfo_exists():
            self._notif_panel.destroy()
            self._notif_panel = None
            return
        # Position panel under the bell
        bx = self._bell_frame.winfo_rootx()
        by = self._bell_frame.winfo_rooty() + self._bell_frame.winfo_height() + 2
        panel = tk.Toplevel(self)
        panel.overrideredirect(True)
        panel.geometry(f"360x480+{bx-300}+{by}")
        panel.configure(bg=BG_PANEL)
        # Shadow border
        panel.config(highlightbackground=DIVIDER, highlightthickness=1)
        self._notif_panel = panel
        self._notif_inner = panel
        self._build_notif_contents()
        # Close on focus-out
        panel.bind("<FocusOut>", lambda e: panel.destroy() if panel.winfo_exists() else None)
        panel.focus_set()

    def _build_notif_contents(self):
        for w in self._notif_inner.winfo_children(): w.destroy()

        # Header row
        hdr = tk.Frame(self._notif_inner, bg=BG_CARD)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🔔  Notifications", font=self.fH2,
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(side=tk.LEFT, padx=12, pady=8)
        if self._notifs:
            tk.Button(hdr, text="Clear all", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
                      relief=tk.FLAT, cursor="hand2",
                      command=self._clear_notifs).pack(side=tk.RIGHT, padx=10)
        tk.Frame(self._notif_inner, bg=DIVIDER, height=1).pack(fill=tk.X)

        # Scrollable list
        outer = tk.Frame(self._notif_inner, bg=BG_PANEL)
        outer.pack(fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas = tk.Canvas(outer, bg=BG_PANEL, highlightthickness=0, yscrollcommand=vsb.set)
        canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_PANEL)
        canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        if not self._notifs:
            tk.Label(inner, text="No notifications yet.", font=self.fSmall,
                     bg=BG_PANEL, fg=TEXT_MUTED).pack(pady=40)
        else:
            for n in self._notifs:
                row = tk.Frame(inner, bg=BG_PANEL,
                               highlightbackground=DIVIDER, highlightthickness=1)
                row.pack(fill=tk.X, padx=8, pady=3, ipady=4)
                # Colour strip on left
                tk.Frame(row, bg=n["color"], width=4).pack(side=tk.LEFT, fill=tk.Y)
                txt_f = tk.Frame(row, bg=BG_PANEL)
                txt_f.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
                tk.Label(txt_f, text=n["msg"], font=self.fSmall, bg=BG_PANEL,
                         fg=TEXT_BODY, wraplength=290, justify=tk.LEFT, anchor=tk.W).pack(anchor=tk.W)
                tk.Label(txt_f, text=n["ts"], font=tkfont.Font(family="Segoe UI",size=8),
                         bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor=tk.W)

    def _clear_notifs(self):
        self._notifs.clear()
        self._notif_count.set(0)
        self._badge_lbl.pack_forget()
        self._build_notif_contents()


    # ════════════════════════════════════════════════════════════════════════
    # STATUS BAR
    # ════════════════════════════════════════════════════════════════════════
    def _update_statusbar(self):
        view = self._active_view.get().capitalize()
        if self._running:
            left = f"  ⬡ AgentHarness  ·  ▶ Running {self._last_agent}…"
        elif self._last_agent:
            left = f"  ⬡ AgentHarness  ·  {view}  ·  Last: {self._last_agent}"
        else:
            left = f"  ⬡ AgentHarness  ·  {view}  ·  Ready"
        self._sb_left.config(text=left)

        parts = []
        if self._run_count:
            parts.append(f"Runs: {self._run_count}")
        if self._last_score is not None:
            col = SUCCESS if self._last_score>=0.75 else (WARNING if self._last_score>=0.5 else ERROR)
            self._sb_right.config(fg=col)
            parts.append(f"Score: {self._last_score:.2f}")
        parts.append("🌙 Dark" if self._theme=="dark" else "☀ Light")
        parts.append("Ctrl+K = Search")
        self._sb_right.config(text="  ·  ".join(parts) + "  ")

    # ════════════════════════════════════════════════════════════════════════
    # COMMAND PALETTE  (Ctrl+K)
    # ════════════════════════════════════════════════════════════════════════
    def _open_cmd_palette(self):
        if self._cmd_palette and self._cmd_palette.winfo_exists():
            self._cmd_palette.destroy(); self._cmd_palette = None; return

        # Build command list: nav views + all agents (quick-launch)
        commands = [
            ("📌", "Go to: Home",     lambda: (self._close_palette(), self._show_view("home"))),
            ("📌", "Go to: Run",      lambda: (self._close_palette(), self._show_view("run"))),
            ("📌", "Go to: History",  lambda: (self._close_palette(), self._show_view("history"))),
            ("📌", "Go to: Skills",   lambda: (self._close_palette(), self._show_view("skills"))),
            ("📌", "Go to: Settings", lambda: (self._close_palette(), self._show_view("settings"))),
            ("🌙", "Toggle Theme",    lambda: (self._close_palette(), self._toggle_theme())),
            ("🔔", "Open Notifications", lambda: (self._close_palette(), self._toggle_notif_panel())),
            ("🗑", "Clear Log",       lambda: (self._close_palette(), self._clear_log())),
        ]
        for team, agents in AGENT_REGISTRY.items():
            for a in agents:
                agent_copy = a; team_copy = team
                commands.append(("▶", f"Run: {a}  [{team}]",
                    lambda ac=agent_copy, tc=team_copy: (self._close_palette(), self._quick_launch(ac, tc))))

        # Palette window — centred
        pw, ph = 560, 420
        sx = self.winfo_x() + (self.winfo_width()  - pw) // 2
        sy = self.winfo_y() + max(40, (self.winfo_height() - ph) // 4)
        pal = tk.Toplevel(self)
        pal.overrideredirect(True)
        pal.geometry(f"{pw}x{ph}+{sx}+{sy}")
        pal.configure(bg=BG_PANEL, highlightbackground=ACCENT, highlightthickness=1)
        self._cmd_palette = pal

        # Search input
        search_f = tk.Frame(pal, bg=BG_PANEL)
        search_f.pack(fill=tk.X, padx=1, pady=1)
        tk.Label(search_f, text="🔍", font=self.fBody, bg=BG_INPUT, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=8)
        self._palette_var = tk.StringVar()
        entry = tk.Entry(search_f, textvariable=self._palette_var, font=self.fH1,
                         bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                         relief=tk.FLAT, bd=0)
        entry.pack(fill=tk.X, expand=True, ipady=10, padx=(0,8))
        tk.Frame(pal, bg=DIVIDER, height=1).pack(fill=tk.X)

        # Results list (canvas-scrollable)
        list_f = tk.Frame(pal, bg=BG_PANEL)
        list_f.pack(fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(list_f, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._pal_canvas = tk.Canvas(list_f, bg=BG_PANEL, highlightthickness=0, yscrollcommand=vsb.set)
        self._pal_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._pal_canvas.yview)
        self._pal_inner = tk.Frame(self._pal_canvas, bg=BG_PANEL)
        self._pal_canvas.create_window((0,0), window=self._pal_inner, anchor="nw", width=pw-20)
        self._pal_inner.bind("<Configure>", lambda e: self._pal_canvas.configure(scrollregion=self._pal_canvas.bbox("all")))

        # Footer hint
        tk.Frame(pal, bg=DIVIDER, height=1).pack(fill=tk.X)
        tk.Label(pal, text="  ↑↓ navigate   Enter select   Esc close",
                 font=tkfont.Font(family="Segoe UI",size=8), bg=BG_CARD, fg=TEXT_MUTED, anchor=tk.W
                 ).pack(fill=tk.X, ipady=4)

        self._pal_commands = commands
        self._pal_selection = 0
        self._render_palette(commands)

        # Bindings
        self._palette_var.trace_add("write", lambda *_: self._filter_palette())
        entry.bind("<Up>",      lambda e: self._palette_nav(-1))
        entry.bind("<Down>",    lambda e: self._palette_nav(+1))
        entry.bind("<Return>",  lambda e: self._palette_exec())
        entry.bind("<Escape>",  lambda e: self._close_palette())
        pal.bind("<FocusOut>",  lambda e: self._close_palette() if pal.winfo_exists() else None)
        entry.focus_set()

    def _render_palette(self, commands):
        for w in self._pal_inner.winfo_children(): w.destroy()
        self._pal_rows = []
        for i,(icon,label,cmd) in enumerate(commands[:40]):  # cap at 40 rows
            is_sel = (i == self._pal_selection)
            bg = BG_SELECTED if is_sel else BG_PANEL
            row = tk.Frame(self._pal_inner, bg=bg, cursor="hand2")
            row.pack(fill=tk.X, padx=2, pady=1)
            tk.Label(row, text=icon, font=self.fSmall, bg=bg, fg=ACCENT_LIGHT, width=3).pack(side=tk.LEFT, padx=6)
            # Highlight matched text
            lbl_w = tk.Label(row, text=label, font=self.fBody, bg=bg,
                             fg=TEXT_PRIMARY if is_sel else TEXT_BODY, anchor=tk.W)
            lbl_w.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
            cmd_copy = cmd; idx = i
            for w in [row, lbl_w]:
                w.bind("<Button-1>", lambda e, c=cmd_copy: c())
                w.bind("<Enter>",    lambda e, r=row, lw=lbl_w: (r.config(bg=BG_HOVER), lw.config(bg=BG_HOVER)))
                w.bind("<Leave>",    lambda e, r=row, lw=lbl_w, ii=idx: (
                    r.config(bg=BG_SELECTED if ii==self._pal_selection else BG_PANEL),
                    lw.config(bg=BG_SELECTED if ii==self._pal_selection else BG_PANEL)))
            self._pal_rows.append((row, lbl_w))

    def _filter_palette(self):
        query = self._palette_var.get().lower().strip()
        filtered = [(ic,lb,c) for ic,lb,c in self._pal_commands if not query or query in lb.lower()]
        self._pal_selection = 0
        self._render_palette(filtered)
        self._pal_filtered = filtered

    def _palette_nav(self, direction):
        rows = getattr(self,"_pal_filtered", self._pal_commands)
        n = min(len(rows), 40)
        if n == 0: return
        self._pal_selection = (self._pal_selection + direction) % n
        self._render_palette(rows)
        # Scroll into view
        if self._pal_rows:
            row_h = 34; self._pal_canvas.yview_moveto(self._pal_selection * row_h / max(n * row_h, 1))

    def _palette_exec(self):
        rows = getattr(self,"_pal_filtered", self._pal_commands)
        if rows and self._pal_selection < len(rows):
            rows[self._pal_selection][2]()

    def _close_palette(self):
        if self._cmd_palette and self._cmd_palette.winfo_exists():
            self._cmd_palette.destroy()
        self._cmd_palette = None

    def _quick_launch(self, agent_id, team):
        """Pre-fill Run view with agent + team, then switch to it."""
        self._team_var.set(team)
        self._on_team_change()
        self._agent_var.set(agent_id)
        self._show_view("run")
        self._update_statusbar()

    # ── Log poll ─────────────────────────────────────────────────────────────
    def _poll_log(self):
        while not log_queue.empty():
            item = log_queue.get_nowait()
            self._log.config(state=tk.NORMAL)
            tag = f"t{id(item)}"
            self._log.tag_configure(tag, foreground=item["color"],
                font=tkfont.Font(family="Consolas",size=9,weight="bold" if item.get("bold") else "normal"))
            self._log.insert(tk.END, item["text"]+"\n", tag)
            self._log.see(tk.END)
            self._log.config(state=tk.DISABLED)
        self.after(80, self._poll_log)


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = AgentHarnessM365()
    app.mainloop()

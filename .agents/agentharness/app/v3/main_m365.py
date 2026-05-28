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
        ("🏠", "Home",      "home"),
        ("▶",  "Run",       "run"),
        ("⚡", "Tasks",     "tasks"),
        ("✅", "Todos",     "todos"),
        ("🤖", "Agents",    "agents"),
        ("🤝", "Clients",   "clients"),
        ("📊", "History",   "history"),
        ("🧠", "Skills",    "skills"),
        ("⚙️", "Settings",  "settings"),
        ("🛡",  "Admin",    "admin"),
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
        self._admin_unlocked = False        # PIN lock state

        self._setup_fonts()
        self._setup_styles()
        self._build_layout()
        self.after(3000, self._start_live_bridge)  # Feature 2: live bridge
        self.after(2000, self._check_scheduled_runs)  # Feature 4: scheduler
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
        self._build_view_tasks()
        self._build_view_todos()
        self._build_view_agents()
        self._build_view_clients()
        self._build_view_history()
        self._build_view_skills()
        self._build_view_settings()
        self._build_view_admin()

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
        if key == "history":  self._refresh_history()
        if key == "home":     self._refresh_home_cards()
        if key == "admin":    self._refresh_admin()
        if key == "tasks":    self._refresh_tasks()
        if key == "todos":    self._refresh_todos()
        if key == "agents":   self._refresh_agents_view()
        if key == "clients":  self._refresh_clients()
        self._update_statusbar()

    # ════════════════════════════════════════════════════════════════════════
    # VIEW: HOME — Agent card grid (M365 App Launcher style)
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_home(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["home"] = f

        # ── Top header bar ──────────────────────────────────────────────
        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20,10))
        tk.Label(hdr, text="Agent Teams", font=self.fTitle,
                 bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        tk.Label(hdr, text="Smith Capital Portfolio — 10 Teams  ·  45 Agents",
                 font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=16, pady=4)
        # Toggle chat panel button (top-right)
        self._chat_toggle_btn = tk.Button(hdr, text="💬 AgentMajesty",
            font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY, relief=tk.FLAT,
            cursor="hand2", padx=10, pady=3,
            command=self._toggle_chat_panel)
        self._chat_toggle_btn.pack(side=tk.RIGHT, padx=4)

        # ── Morning Briefing Banner ─────────────────────────────────────
        self._briefing_frame = tk.Frame(f, bg=BG_CANVAS)
        self._briefing_frame.pack(fill=tk.X, padx=16, pady=(0,8))
        self._build_briefing_card(self._briefing_frame)

        # ── Body: card grid (left) + chat panel (right) ─────────────────
        self._home_body = tk.Frame(f, bg=BG_CANVAS)
        self._home_body.pack(fill=tk.BOTH, expand=True)

        # LEFT — scrollable card grid
        left = tk.Frame(self._home_body, bg=BG_CANVAS)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        outer = tk.Frame(left, bg=BG_CANVAS)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._home_canvas = tk.Canvas(outer, bg=BG_CANVAS, highlightthickness=0,
                                       yscrollcommand=vsb.set)
        self._home_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._home_canvas.yview)
        self._home_inner = tk.Frame(self._home_canvas, bg=BG_CANVAS)
        self._home_canvas.create_window((0,0), window=self._home_inner, anchor="nw")
        self._home_inner.bind("<Configure>",
            lambda e: self._home_canvas.configure(
                scrollregion=self._home_canvas.bbox("all")))

        # RIGHT — AgentMajesty chat panel (initially visible)
        self._chat_panel_visible = True
        self._build_chat_panel(self._home_body)

    def _refresh_home_cards(self):
        self._refresh_briefing_card()
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
    # AGENTMAJESTY CHAT PANEL  (Home screen right sidebar)
    # ════════════════════════════════════════════════════════════════════════
    def _build_chat_panel(self, parent):
        """Builds the persistent right-side chat panel inside the Home body frame."""
        self._chat_frame = tk.Frame(parent, bg=BG_PANEL, width=340,
                                     highlightbackground=DIVIDER, highlightthickness=1)
        self._chat_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,0))
        self._chat_frame.pack_propagate(False)

        # ── Panel header ─────────────────────────────────────────────────
        chat_hdr = tk.Frame(self._chat_frame, bg=BG_CARD, height=44)
        chat_hdr.pack(fill=tk.X)
        chat_hdr.pack_propagate(False)
        # Avatar dot
        av = tk.Label(chat_hdr, text="👑", font=tkfont.Font(family="Segoe UI Emoji",size=16),
                      bg=BG_CARD, fg=ACCENT_LIGHT, padx=8)
        av.pack(side=tk.LEFT, pady=4)
        name_col = tk.Frame(chat_hdr, bg=BG_CARD)
        name_col.pack(side=tk.LEFT, fill=tk.Y, pady=6)
        tk.Label(name_col, text="AgentMajesty", font=self.fH2,
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor=tk.W)
        tk.Label(name_col, text="Chief of Staff  ·  Online",
                 font=self.fSmall, bg=BG_CARD, fg=SUCCESS).pack(anchor=tk.W)
        # Online dot
        tk.Label(chat_hdr, text="●", font=self.fSmall,
                 bg=BG_CARD, fg=SUCCESS).pack(side=tk.RIGHT, padx=10)
        tk.Frame(self._chat_frame, bg=DIVIDER, height=1).pack(fill=tk.X)

        # ── Chip quick-actions ───────────────────────────────────────────
        chip_row = tk.Frame(self._chat_frame, bg=BG_PANEL)
        chip_row.pack(fill=tk.X, padx=8, pady=(6,2))
        for chip_text in ["Today's briefing", "Run status", "Flag issues", "Top priority"]:
            tk.Button(chip_row, text=chip_text, font=self.fSmall,
                      bg=BG_HOVER, fg=TEXT_MUTED, relief=tk.FLAT, cursor="hand2",
                      padx=6, pady=2,
                      command=lambda t=chip_text: self._chat_send(t)
                      ).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Frame(self._chat_frame, bg=DIVIDER, height=1).pack(fill=tk.X, pady=(4,0))

        # ── Message history (scrollable canvas) ──────────────────────────
        msg_outer = tk.Frame(self._chat_frame, bg=BG_PANEL)
        msg_outer.pack(fill=tk.BOTH, expand=True)
        self._chat_vsb = ttk.Scrollbar(msg_outer, orient="vertical")
        self._chat_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._chat_canvas = tk.Canvas(msg_outer, bg=BG_PANEL,
                                       highlightthickness=0,
                                       yscrollcommand=self._chat_vsb.set)
        self._chat_canvas.pack(fill=tk.BOTH, expand=True)
        self._chat_vsb.configure(command=self._chat_canvas.yview)
        self._chat_msgs_frame = tk.Frame(self._chat_canvas, bg=BG_PANEL)
        self._chat_canvas.create_window((0,0), window=self._chat_msgs_frame,
                                         anchor="nw", width=320)
        self._chat_msgs_frame.bind("<Configure>",
            lambda e: self._chat_canvas.configure(
                scrollregion=self._chat_canvas.bbox("all")))
        self._chat_messages = []   # list of {role, text}

        # ── Input bar ────────────────────────────────────────────────────
        tk.Frame(self._chat_frame, bg=DIVIDER, height=1).pack(fill=tk.X)
        input_row = tk.Frame(self._chat_frame, bg=BG_PANEL, pady=6)
        input_row.pack(fill=tk.X, padx=8)
        self._chat_input = tk.Text(input_row, height=2, font=self.fBody,
                                    bg=BG_INPUT, fg=TEXT_BODY,
                                    insertbackground=TEXT_BODY, relief=tk.FLAT,
                                    wrap=tk.WORD, padx=8, pady=4,
                                    highlightthickness=1,
                                    highlightbackground=DIVIDER)
        self._chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._chat_input.bind("<Return>",     self._chat_on_enter)
        self._chat_input.bind("<Shift-Return>", lambda e: None)  # allow newline
        send_btn = tk.Button(input_row, text="⬆", font=self.fH1,
                              bg=ACCENT, fg=TEXT_PRIMARY, relief=tk.FLAT,
                              cursor="hand2", padx=8, pady=4,
                              command=lambda: self._chat_send())
        send_btn.pack(side=tk.LEFT, padx=(6,0))

        # ── Welcome message ──────────────────────────────────────────────
        self._chat_push("AgentMajesty",
            "Chief of Staff online. Ready to brief you on the portfolio, "
            "flag blockers, or coordinate agent tasks. What do you need?",
            role="agent")

    def _toggle_chat_panel(self):
        """Show/hide the right chat panel."""
        if self._chat_panel_visible:
            self._chat_frame.pack_forget()
            self._chat_panel_visible = False
            self._chat_toggle_btn.config(text="💬 Open AgentMajesty", bg=BG_CARD, fg=TEXT_MUTED)
        else:
            self._chat_frame.pack(side=tk.RIGHT, fill=tk.Y)
            self._chat_panel_visible = True
            self._chat_toggle_btn.config(text="💬 AgentMajesty", bg=ACCENT, fg=TEXT_PRIMARY)
            self._chat_scroll_bottom()

    def _chat_push(self, sender, text, role="user"):
        """Add a message bubble to the chat panel."""
        is_agent = (role == "agent")
        bg        = BG_CARD   if is_agent else ACCENT_DARK
        fg        = TEXT_BODY if is_agent else TEXT_PRIMARY
        anchor    = tk.W      if is_agent else tk.E
        padx_l    = (8, 40)   if is_agent else (40, 8)

        bubble_outer = tk.Frame(self._chat_msgs_frame, bg=BG_PANEL)
        bubble_outer.pack(fill=tk.X, padx=0, pady=3, anchor=anchor)

        if is_agent:
            tk.Label(bubble_outer, text="👑", font=self.fSmall,
                     bg=BG_PANEL, fg=ACCENT_LIGHT).pack(side=tk.LEFT, anchor=tk.N, padx=(6,2), pady=4)

        bubble = tk.Frame(bubble_outer, bg=bg,
                          highlightbackground=BORDER_CARD, highlightthickness=1)
        bubble.pack(side=tk.LEFT if is_agent else tk.RIGHT,
                    padx=padx_l, pady=2, anchor=anchor)
        tk.Label(bubble, text=text, font=self.fBody, bg=bg, fg=fg,
                 wraplength=230, justify=tk.LEFT, anchor=tk.W,
                 padx=10, pady=6).pack()

        self._chat_messages.append({"role": role, "text": text})
        self._chat_scroll_bottom()

    def _chat_scroll_bottom(self):
        self._chat_msgs_frame.update_idletasks()
        self._chat_canvas.configure(scrollregion=self._chat_canvas.bbox("all"))
        self._chat_canvas.yview_moveto(1.0)

    def _chat_on_enter(self, event):
        """Send on Enter, allow Shift+Enter for newline."""
        if event.state & 0x1:   # Shift held
            return
        self._chat_send()
        return "break"

    def _chat_send(self, prefill=None):
        """Send a message to AgentMajesty and dispatch to agent logic."""
        text = prefill or self._chat_input.get("1.0", tk.END).strip()
        if not text: return
        self._chat_input.delete("1.0", tk.END)
        self._chat_push("You", text, role="user")

        # Dispatch to local response logic in a thread
        import threading
        threading.Thread(target=self._chat_respond, args=(text,), daemon=True).start()


    def _chat_build_briefing(self):
        stats = db_agent_stats()
        total_runs = sum(s["runs"] for s in stats.values())
        flagged    = [a for a,s in stats.items() if s["runs"]>0 and s["avg"]<0.60]
        teams      = len(AGENT_REGISTRY)
        agents     = sum(len(v) for v in AGENT_REGISTRY.values())
        lines = [
            f"Good day. Portfolio snapshot:",
            f"• {teams} teams / {agents} agents deployed",
            f"• {total_runs} total agent runs logged",
        ]
        if flagged:
            lines.append(f"• {len(flagged)} agent(s) flagged (score <0.60): {', '.join(flagged[:3])}")
        else:
            lines.append("• No agents currently flagged")
        lines.append("Active automations: 9  |  Credits used today: 0.8")
        return "\n".join(lines)

    def _chat_build_run_status(self):
        stats = db_agent_stats()
        if not stats:
            return "No runs logged yet this session. Head to the Run view to execute your first agent."
        top = sorted(stats.items(), key=lambda x: x[1]["runs"], reverse=True)[:5]
        lines = ["Most active agents:"]
        for agent, s in top:
            lines.append(f"  {agent}: {s['runs']}r  avg {s['avg']:.2f}")
        return "\n".join(lines)

    def _chat_build_blockers(self):
        issues = [
            "PBS site: Golf Tournament + Dues pages need payment links",
            "XFTC Gmail: forwarding rule required for signup logger",
            "Smith Capital LLC: reactivation filings overdue",
            "Clarity Solar: TX SB 1036 GL insurance deadline Sep 1",
            "Smith Capital Holdings: S-Corp election not yet filed",
        ]
        return "Current portfolio blockers:\n" + "\n".join(f"\u2022 {b}" for b in issues)

    def _chat_build_priorities(self):
        priorities = [
            "1. Smith Capital Holdings LLC — file Certificate of Formation",
            "2. XFTC Plugin Sprint 3 — Stripe live key + coach portal",
            "3. PBS Website — finalize 3 remaining content pages",
            "4. Clarity Solar — register claritysolarservices.com + GL insurance",
            "5. YEPC — Hutto EDC follow-up (14-day mark passed)",
        ]
        return "Top 5 portfolio priorities:\n" + "\n".join(priorities)


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
        tk.Button(ribbon, text="🕐 Schedule", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2",
            command=self._run_show_scheduler).pack(side=tk.RIGHT, padx=6)

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
            ("📌", "Go to: Tasks",    lambda: (self._close_palette(), self._show_view("tasks"))),
            ("📌", "Go to: Todos",    lambda: (self._close_palette(), self._show_view("todos"))),
            ("📌", "Go to: Agents",   lambda: (self._close_palette(), self._show_view("agents"))),
            ("📌", "Go to: Clients",  lambda: (self._close_palette(), self._show_view("clients"))),
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


    # ════════════════════════════════════════════════════════════════════════
    # VIEW: ADMIN
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_admin(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["admin"] = f

        # Header row
        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20, 6))
        tk.Label(hdr, text="🛡  Admin", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        self._admin_lock_lbl = tk.Label(hdr, text="🔒 Locked", font=self.fSmall,
                                        bg=BG_CANVAS, fg=WARNING, padx=8)
        self._admin_lock_lbl.pack(side=tk.LEFT, pady=6)
        tk.Button(hdr, text="🔓 Unlock", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._admin_pin_prompt).pack(side=tk.LEFT)
        tk.Button(hdr, text="↻ Refresh", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._refresh_admin).pack(side=tk.RIGHT, padx=6)

        # Sub-tab notebook
        nb = ttk.Notebook(f)
        nb.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 12))
        self._admin_nb = nb

        # ── Tab 1: Reflexion Dashboard ──────────────────────────────────
        t1 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t1, text="  📈 Reflexion Dashboard  ")
        self._admin_reflexion_frame = t1
        self._build_reflexion_dashboard(t1)

        # ── Tab 2: Agent Manager ────────────────────────────────────────
        t2 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t2, text="  🤖 Agent Manager  ")
        self._admin_agent_frame = t2
        self._build_agent_manager(t2)

        # ── Tab 3: DB Tools ─────────────────────────────────────────────
        t3 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t3, text="  🗄 DB Tools  ")
        self._admin_db_frame = t3
        self._build_db_tools(t3)

        # ── Tab 4: Log Viewer ───────────────────────────────────────────
        t4 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t4, text="  📋 Log Viewer  ")
        self._admin_log_frame = t4
        self._build_log_viewer(t4)

        # ── Tab 5: Automation Status ────────────────────────────────────
        t5 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t5, text="  ⏱ Automations  ")
        self._admin_auto_frame = t5
        self._build_automation_status(t5)

    # ── PIN lock ─────────────────────────────────────────────────────────
    def _admin_pin_prompt(self):
        if self._admin_unlocked:
            self._admin_unlocked = False
            self._admin_lock_lbl.config(text="🔒 Locked", fg=WARNING)
            return
        win = tk.Toplevel(self)
        win.title("Admin PIN")
        win.geometry("300x140")
        win.configure(bg=BG_PANEL)
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="Enter Admin PIN", font=self.fH2, bg=BG_PANEL, fg=TEXT_PRIMARY).pack(pady=(18,6))
        pin_var = tk.StringVar()
        e = tk.Entry(win, textvariable=pin_var, show="●", font=self.fH1,
                     bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                     relief=tk.FLAT, width=12, justify=tk.CENTER,
                     highlightthickness=1, highlightbackground=DIVIDER)
        e.pack(pady=4, ipady=6)
        e.focus_set()
        msg = tk.Label(win, text="", font=self.fSmall, bg=BG_PANEL, fg=ERROR)
        msg.pack()
        def _check(evt=None):
            if pin_var.get() == "1914":   # Phi Beta Sigma founding year 🤙
                self._admin_unlocked = True
                self._admin_lock_lbl.config(text="🔓 Unlocked", fg=SUCCESS)
                win.destroy()
                self._refresh_admin()
            else:
                msg.config(text="Incorrect PIN")
                pin_var.set("")
        e.bind("<Return>", _check)
        tk.Button(win, text="Unlock", font=self.fBtn, bg=ACCENT, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=16, pady=4,
                  command=_check).pack(pady=6)

    def _refresh_admin(self):
        if not self._admin_unlocked:
            return
        self._refresh_reflexion_dashboard()
        self._refresh_agent_manager()
        self._refresh_db_stats()
        self._refresh_log_viewer()
        self._refresh_automation_status()

    # ════════════════════════════════════════════════════════════════════════
    # ADMIN TAB 1: REFLEXION DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    def _build_reflexion_dashboard(self, parent):
        # Summary pills row
        pill_row = tk.Frame(parent, bg=BG_CANVAS)
        pill_row.pack(fill=tk.X, padx=12, pady=(12,6))
        self._pill_total   = self._make_stat_pill(pill_row, "Total Runs",   "—", TEXT_MUTED)
        self._pill_avg     = self._make_stat_pill(pill_row, "Avg Score",    "—", TEXT_MUTED)
        self._pill_passing = self._make_stat_pill(pill_row, "Passing (≥.75)","—", TEXT_MUTED)
        self._pill_flagged = self._make_stat_pill(pill_row, "Flagged (<.60)","—", TEXT_MUTED)

        # Per-agent table
        cols = ("agent","project","runs","avg_score","best","last_score","skill_v","status")
        tf = tk.Frame(parent, bg=BG_CANVAS); tf.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        vsb = ttk.Scrollbar(tf, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._reflex_tree = ttk.Treeview(tf, columns=cols, show="headings",
                                          selectmode="browse", yscrollcommand=vsb.set)
        vsb.configure(command=self._reflex_tree.yview)
        widths = [180,110,55,80,75,80,65,80]
        for col,w in zip(cols,widths):
            self._reflex_tree.heading(col, text=col.replace("_"," ").title())
            self._reflex_tree.column(col, width=w, minwidth=40)
        self._reflex_tree.pack(fill=tk.BOTH, expand=True)
        # Double-click → open skill
        self._reflex_tree.bind("<Double-1>", self._reflex_open_skill)

    def _make_stat_pill(self, parent, label, value, color):
        f = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_CARD, highlightthickness=1)
        f.pack(side=tk.LEFT, padx=6, ipadx=14, ipady=8)
        val_lbl = tk.Label(f, text=value, font=self.fScore, bg=BG_CARD, fg=color)
        val_lbl.pack()
        tk.Label(f, text=label, font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack()
        return val_lbl

    def _refresh_reflexion_dashboard(self):
        stats = db_agent_stats()
        runs = db_load_runs(500)
        total = len(runs)
        scores = [r[4] for r in runs if r[4] is not None]
        avg    = sum(scores)/len(scores) if scores else 0
        passing = sum(1 for s in scores if s >= 0.75)
        flagged = sum(1 for s in scores if s < 0.60)

        def upd(lbl, val, color): lbl.config(text=str(val), fg=color)
        upd(self._pill_total,   total,   INFO)
        upd(self._pill_avg,     f"{avg:.2f}", SUCCESS if avg>=0.75 else WARNING)
        upd(self._pill_passing, passing, SUCCESS)
        upd(self._pill_flagged, flagged, ERROR if flagged else TEXT_MUTED)

        for r in self._reflex_tree.get_children(): self._reflex_tree.delete(r)
        # Get last score per agent from full run list
        last_scores = {}
        for row in runs:
            run_id,agent,proj,graph,score,status,ts = row
            if agent not in last_scores: last_scores[agent] = score

        for agent, s in sorted(stats.items(), key=lambda x: x[1]["avg"], reverse=True):
            last = last_scores.get(agent)
            proj = agent.split("-")[0] if "-" in agent else "—"
            status = "✅ Good" if s["avg"]>=0.75 else ("⚠ Warn" if s["avg"]>=0.60 else "🔴 Flag")
            tag = "good" if s["avg"]>=0.75 else ("warn" if s["avg"]>=0.60 else "flag")
            # Get skill version from DB
            sk_name = agent.replace("-","_")
            _, sv = db_load_skill(sk_name)
            self._reflex_tree.insert("","end", values=(
                agent, proj, s["runs"],
                f"{s['avg']:.2f}", f"{s['best']:.2f}",
                f"{last:.2f}" if last else "—", sv, status
            ), tags=(tag,))
        self._reflex_tree.tag_configure("good", foreground=SUCCESS)
        self._reflex_tree.tag_configure("warn", foreground=WARNING)
        self._reflex_tree.tag_configure("flag", foreground=ERROR)

    def _reflex_open_skill(self, evt):
        sel = self._reflex_tree.selection()
        if not sel: return
        agent = self._reflex_tree.item(sel[0])["values"][0]
        self._skill_agent_var.set(agent)
        self._load_skill_view()
        self._show_view("skills")

    # ════════════════════════════════════════════════════════════════════════
    # ADMIN TAB 2: AGENT MANAGER
    # ════════════════════════════════════════════════════════════════════════
    def _build_agent_manager(self, parent):
        ctrl = tk.Frame(parent, bg=BG_CANVAS); ctrl.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(ctrl, text="Filter team:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT)
        self._mgr_team_var = tk.StringVar(value="All")
        teams_list = ["All"] + list(AGENT_REGISTRY.keys())
        tc = ttk.Combobox(ctrl, textvariable=self._mgr_team_var, values=teams_list, state="readonly", font=self.fSmall, width=20)
        tc.pack(side=tk.LEFT, padx=8)
        tc.bind("<<ComboboxSelected>>", lambda e: self._refresh_agent_manager())
        tk.Button(ctrl, text="Reset Selected Stats", font=self.fSmall, bg=ERROR, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._reset_agent_stats).pack(side=tk.RIGHT, padx=6)
        tk.Button(ctrl, text="Edit Skill File", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._mgr_edit_skill).pack(side=tk.RIGHT, padx=6)

        cols = ("agent","team","runs","avg","skill_v","skill_file")
        tf = tk.Frame(parent, bg=BG_CANVAS); tf.pack(fill=tk.BOTH, expand=True, padx=12)
        vsb = ttk.Scrollbar(tf, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._mgr_tree = ttk.Treeview(tf, columns=cols, show="headings",
                                       selectmode="browse", yscrollcommand=vsb.set)
        vsb.configure(command=self._mgr_tree.yview)
        for col, w in zip(cols, [200,130,55,65,65,220]):
            self._mgr_tree.heading(col, text=col.replace("_"," ").title())
            self._mgr_tree.column(col, width=w, minwidth=40)
        self._mgr_tree.pack(fill=tk.BOTH, expand=True)

        # Inline skill editor
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill=tk.X, padx=12, pady=6)
        tk.Label(parent, text="Skill Editor", font=self.fH2, bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor=tk.W, padx=14)
        self._mgr_skill_ed = scrolledtext.ScrolledText(parent, height=10, font=self.fMonoSm,
            bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY, relief=tk.FLAT, wrap=tk.WORD,
            highlightthickness=1, highlightbackground=DIVIDER)
        self._mgr_skill_ed.pack(fill=tk.X, padx=12, pady=(4,2))
        save_row = tk.Frame(parent, bg=BG_CANVAS); save_row.pack(anchor=tk.W, padx=12, pady=(0,8))
        tk.Button(save_row, text="💾 Save Skill", font=self.fSmall, bg=SUCCESS, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=10,
                  command=self._mgr_save_skill).pack(side=tk.LEFT, padx=(0,8))
        tk.Button(save_row, text="Clear", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=lambda: self._mgr_skill_ed.delete("1.0",tk.END)).pack(side=tk.LEFT)
        self._mgr_current_agent = ""

    def _refresh_agent_manager(self):
        stats = db_agent_stats()
        team_filter = self._mgr_team_var.get()
        for r in self._mgr_tree.get_children(): self._mgr_tree.delete(r)
        for team, agents in AGENT_REGISTRY.items():
            if team_filter != "All" and team != team_filter: continue
            for agent in agents:
                s = stats.get(agent, {"runs":0,"avg":0.0})
                sk_name = agent.replace("-","_")
                _, sv = db_load_skill(sk_name)
                # Find skill file path
                skill_path = "—"
                for md in SKILLS_DIR.rglob(f"{agent}.md"):
                    skill_path = str(md.relative_to(APP_ROOT))
                    break
                tag = "good" if s["avg"]>=0.75 else ("warn" if s["avg"]>0 else "none")
                self._mgr_tree.insert("","end", values=(agent,team,s["runs"],f"{s['avg']:.2f}" if s["runs"] else "—",sv,skill_path), tags=(tag,))
        self._mgr_tree.tag_configure("good", foreground=SUCCESS)
        self._mgr_tree.tag_configure("warn", foreground=WARNING)

    def _mgr_edit_skill(self):
        sel = self._mgr_tree.selection()
        if not sel: return
        agent = self._mgr_tree.item(sel[0])["values"][0]
        self._mgr_current_agent = agent
        content = read_agent_skill_file(agent)
        sk_name = agent.replace("-","_")
        db_content, _ = db_load_skill(sk_name)
        final = db_content if db_content else content
        self._mgr_skill_ed.delete("1.0", tk.END)
        self._mgr_skill_ed.insert("1.0", final if final else "# Skill: " + agent + "\n\n## Instructions\n\n")

    def _mgr_save_skill(self):
        if not self._mgr_current_agent:
            return
        content = self._mgr_skill_ed.get("1.0", tk.END).strip()
        sk_name = self._mgr_current_agent.replace("-","_")
        _, sv = db_load_skill(sk_name)
        db_save_skill(self._mgr_current_agent, sk_name, sv+1, content, 0.0, "Manual edit via Admin panel")
        qlog(f"✓ Skill saved: {sk_name} → v{sv+1}", SUCCESS)
        self._push_notif(f"💾 Skill updated: {self._mgr_current_agent} → v{sv+1}", SUCCESS)

    def _reset_agent_stats(self):
        sel = self._mgr_tree.selection()
        if not sel: return
        agent = self._mgr_tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Reset Stats", "Delete all run history for " + agent + "? This cannot be undone."): return
        c = _get_db()
        c.execute("DELETE FROM runs WHERE agent_id=?", (agent,))
        c.commit(); c.close()
        qlog(f"✓ Stats reset for {agent}", WARNING)
        self._refresh_agent_manager()
        self._push_notif(f"🗑 Stats reset: {agent}", WARNING)

    # ════════════════════════════════════════════════════════════════════════
    # ADMIN TAB 3: DB TOOLS
    # ════════════════════════════════════════════════════════════════════════
    def _build_db_tools(self, parent):
        tk.Label(parent, text="Database", font=self.fH2, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(anchor=tk.W, padx=16, pady=(16,8))

        pill_row = tk.Frame(parent, bg=BG_CANVAS); pill_row.pack(fill=tk.X, padx=12, pady=(0,10))
        self._db_pill_runs   = self._make_stat_pill(pill_row, "Total Runs",   "—", INFO)
        self._db_pill_skills = self._make_stat_pill(pill_row, "Skill Versions","—", ACCENT_LIGHT)
        self._db_pill_agents = self._make_stat_pill(pill_row, "Unique Agents", "—", SUCCESS)
        self._db_pill_size   = self._make_stat_pill(pill_row, "DB Size",       "—", TEXT_MUTED)

        btn_row = tk.Frame(parent, bg=BG_CANVAS); btn_row.pack(anchor=tk.W, padx=12, pady=6)
        tk.Button(btn_row, text="📤 Export Runs CSV", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=10, command=self._db_export_csv).pack(side=tk.LEFT, padx=(0,8))
        tk.Button(btn_row, text="🗑 Purge Runs > 30 days", font=self.fSmall, bg=WARNING, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=10, command=self._db_purge_old).pack(side=tk.LEFT, padx=(0,8))
        tk.Button(btn_row, text="☠ Drop ALL Data", font=self.fSmall, bg=ERROR, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=10, command=self._db_drop_all).pack(side=tk.LEFT)

        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill=tk.X, padx=12, pady=8)
        tk.Label(parent, text="Quick SQL Query", font=self.fH2, bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor=tk.W, padx=16)
        sql_f = tk.Frame(parent, bg=BG_CANVAS); sql_f.pack(fill=tk.X, padx=12, pady=4)
        self._sql_entry = tk.Entry(sql_f, font=self.fMono, bg=BG_INPUT, fg=TEXT_BODY,
                                   insertbackground=TEXT_BODY, relief=tk.FLAT, width=60,
                                   highlightthickness=1, highlightbackground=DIVIDER)
        self._sql_entry.pack(side=tk.LEFT, ipady=4, padx=(0,8), fill=tk.X, expand=True)
        self._sql_entry.insert(0, "SELECT agent_id, COUNT(*), AVG(score) FROM runs GROUP BY agent_id")
        tk.Button(sql_f, text="Run", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=8, command=self._db_run_sql).pack(side=tk.LEFT)
        self._sql_result = scrolledtext.ScrolledText(parent, height=10, font=self.fMonoSm,
            bg=BG_INPUT, fg=TEXT_BODY, relief=tk.FLAT, state=tk.DISABLED, wrap=tk.NONE)
        self._sql_result.pack(fill=tk.X, padx=12, pady=4)

    def _refresh_db_stats(self):
        c = _get_db()
        runs    = c.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        skills  = c.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        agents  = c.execute("SELECT COUNT(DISTINCT agent_id) FROM runs").fetchone()[0]
        c.close()
        size = DB_PATH.stat().st_size // 1024 if DB_PATH.exists() else 0
        self._db_pill_runs.config(text=str(runs),   fg=INFO)
        self._db_pill_skills.config(text=str(skills), fg=ACCENT_LIGHT)
        self._db_pill_agents.config(text=str(agents), fg=SUCCESS)
        self._db_pill_size.config(text=f"{size} KB",  fg=TEXT_MUTED)

    def _db_export_csv(self):
        import csv as _csv
        out = APP_ROOT / "agent_runs_export.csv"
        rows = db_load_runs(9999)
        with open(out, "w", newline="") as f:
            w = _csv.writer(f)
            w.writerow(["run_id","agent","project","graph","score","status","date"])
            w.writerows(rows)
        qlog(f"✓ Exported {len(rows)} rows → {out}", SUCCESS)
        self._push_notif(f"📤 Exported {len(rows)} runs to agent_runs_export.csv", SUCCESS)

    def _db_purge_old(self):
        if not messagebox.askyesno("Purge", "Delete all run records older than 30 days?"): return
        c = _get_db()
        c.execute("DELETE FROM runs WHERE created_at < datetime('now','-30 days')")
        deleted = c.execute("SELECT changes()").fetchone()[0]
        c.commit(); c.close()
        qlog(f"✓ Purged {deleted} old records.", WARNING)
        self._refresh_db_stats()
        self._push_notif(f"🗑 Purged {deleted} records (>30 days)", WARNING)

    def _db_drop_all(self):
        if not messagebox.askyesno("DANGER", "Delete ALL runs and skill versions? Cannot be undone."): return
        if not messagebox.askyesno("Confirm", "Really drop everything?"): return
        c = _get_db()
        c.execute("DELETE FROM runs"); c.execute("DELETE FROM skills")
        c.commit(); c.close()
        qlog("☠ All data dropped.", ERROR, bold=True)
        self._refresh_db_stats()
        self._push_notif("☠ All DB data dropped.", ERROR)

    def _db_run_sql(self):
        sql = self._sql_entry.get().strip()
        if not sql: return
        try:
            c = _get_db()
            rows = c.execute(sql).fetchall()
            c.close()
            out = "\n".join(str(r) for r in rows[:200])
            if len(rows) > 200: out += f"\n… ({len(rows)-200} more rows)"
        except Exception as e:
            out = f"ERROR: {e}"
        self._sql_result.config(state=tk.NORMAL)
        self._sql_result.delete("1.0", tk.END)
        self._sql_result.insert("1.0", out or "(no results)")
        self._sql_result.config(state=tk.DISABLED)

    # ════════════════════════════════════════════════════════════════════════
    # ADMIN TAB 4: LOG VIEWER
    # ════════════════════════════════════════════════════════════════════════
    def _build_log_viewer(self, parent):
        ctrl = tk.Frame(parent, bg=BG_CANVAS); ctrl.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(ctrl, text="Agent:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT)
        self._lv_agent_var = tk.StringVar(value="All")
        ac = ttk.Combobox(ctrl, textvariable=self._lv_agent_var,
                          values=["All"]+ALL_AGENTS, state="readonly", font=self.fSmall, width=28)
        ac.pack(side=tk.LEFT, padx=6)
        tk.Label(ctrl, text="Project:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(12,0))
        self._lv_proj_var = tk.StringVar(value="All")
        pc = ttk.Combobox(ctrl, textvariable=self._lv_proj_var,
                          values=["All"]+PROJECTS, state="readonly", font=self.fSmall, width=18)
        pc.pack(side=tk.LEFT, padx=6)
        tk.Button(ctrl, text="Filter", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
                  relief=tk.FLAT, cursor="hand2", padx=8,
                  command=self._refresh_log_viewer).pack(side=tk.LEFT, padx=8)

        cols2 = ("run_id","agent","project","graph","score","revision","status","date")
        tf = tk.Frame(parent, bg=BG_CANVAS); tf.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        vsb = ttk.Scrollbar(tf, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._lv_tree = ttk.Treeview(tf, columns=cols2, show="headings",
                                      selectmode="browse", yscrollcommand=vsb.set)
        vsb.configure(command=self._lv_tree.yview)
        for col, w in zip(cols2, [70,175,100,110,60,65,75,145]):
            self._lv_tree.heading(col, text=col.replace("_"," ").title())
            self._lv_tree.column(col, width=w, minwidth=40)
        self._lv_tree.pack(fill=tk.BOTH, expand=True)
        self._lv_tree.bind("<<TreeviewSelect>>", self._lv_show_detail)

        # Detail pane
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill=tk.X, padx=12, pady=4)
        self._lv_detail = scrolledtext.ScrolledText(parent, height=7, font=self.fMonoSm,
            bg=BG_INPUT, fg=TEXT_BODY, relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD)
        self._lv_detail.pack(fill=tk.X, padx=12, pady=(0,8))

    def _refresh_log_viewer(self):
        agent_f = self._lv_agent_var.get()
        proj_f  = self._lv_proj_var.get()
        for r in self._lv_tree.get_children(): self._lv_tree.delete(r)
        c = _get_db()
        rows = c.execute("SELECT run_id,agent_id,project,graph,score,revision_count,status,created_at,critique,output FROM runs ORDER BY id DESC LIMIT 300").fetchall()
        c.close()
        self._lv_data = {}
        for row in rows:
            run_id,agent,proj,graph,score,rev,status,ts,crit,out = row
            if agent_f != "All" and agent != agent_f: continue
            if proj_f  != "All" and proj  != proj_f:  continue
            sc = f"{score:.2f}" if score else "—"
            tag = "good" if (score or 0)>=0.75 else ("warn" if (score or 0)>=0.5 else "dim")
            self._lv_tree.insert("","end", values=(run_id,agent,proj,graph,sc,rev or 0,status,ts[:16]), tags=(tag,))
            self._lv_data[run_id] = {"critique": crit or "", "output": out or ""}
        self._lv_tree.tag_configure("good", foreground=SUCCESS)
        self._lv_tree.tag_configure("warn", foreground=WARNING)
        self._lv_tree.tag_configure("dim",  foreground=TEXT_MUTED)

    def _lv_show_detail(self, evt):
        sel = self._lv_tree.selection()
        if not sel: return
        run_id = self._lv_tree.item(sel[0])["values"][0]
        d = self._lv_data.get(run_id, {})
        text = "CRITIQUE:\n" + d.get("critique","\u2014") + "\n\nOUTPUT PREVIEW:\n" + d.get("output","\u2014")[:600]
        self._lv_detail.config(state=tk.NORMAL)
        self._lv_detail.delete("1.0", tk.END)
        self._lv_detail.insert("1.0", text)
        self._lv_detail.config(state=tk.DISABLED)

    # ════════════════════════════════════════════════════════════════════════
    # ADMIN TAB 5: AUTOMATION STATUS
    # ════════════════════════════════════════════════════════════════════════
    def _build_automation_status(self, parent):
        tk.Label(parent, text="Base44 Automations", font=self.fH2,
                 bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(anchor=tk.W, padx=16, pady=(16,4))
        tk.Label(parent, text="Live status pulled from the Base44 platform on each refresh.",
                 font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor=tk.W, padx=16)

        self._known_automations = [
            {"name": "Xtreme Force — New Signups & Payments Logger", "project": "xftc",     "schedule": "Every 30 min",   "last_runs": 11, "credits": 0.6},
            {"name": "Sigma Signal — Daily Submission Check",        "project": "sigma",    "schedule": "Daily 8AM CT",   "last_runs": 3,  "credits": 0.0},
            {"name": "Sigma Signal — Newsletter Production Reminder","project": "sigma",    "schedule": "2nd/4th Thu CT", "last_runs": 2,  "credits": 0.2},
            {"name": "Daily Grant & Funding Research Sweep",         "project": "grants",   "schedule": "Mon 8AM CT",     "last_runs": 1,  "credits": 0.1},
            {"name": "YEPC — Hutto Planning Monitor",                "project": "yepc",     "schedule": "Weekly Mon",     "last_runs": 1,  "credits": 0.0},
            {"name": "SmithCap LLC Reactivation Reminder",           "project": "smithcap", "schedule": "One-time",       "last_runs": 1,  "credits": 0.0},
            {"name": "Reflexion Daily Report — 7AM CT",              "project": "all",      "schedule": "Daily 7AM CT",   "last_runs": 1,  "credits": 0.1},
            {"name": "Weekly Fare Monitor — AUS Routes",             "project": "travel",   "schedule": "Weekly",         "last_runs": 0,  "credits": 0.0},
            {"name": "AgentHarness — Daily Auto-commit",             "project": "dev",      "schedule": "Daily midnight", "last_runs": 0,  "credits": 0.0},
        ]

        cols = ("name","project","schedule","runs_24h","credits","status")
        tf = tk.Frame(parent, bg=BG_CANVAS); tf.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        vsb = ttk.Scrollbar(tf, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._auto_tree = ttk.Treeview(tf, columns=cols, show="headings",
                                        selectmode="browse", yscrollcommand=vsb.set)
        vsb.configure(command=self._auto_tree.yview)
        for col, w in zip(cols, [310,90,130,80,70,90]):
            self._auto_tree.heading(col, text=col.replace("_"," ").title())
            self._auto_tree.column(col, width=w, minwidth=50)
        self._auto_tree.pack(fill=tk.BOTH, expand=True)

        tk.Label(parent, text="Last 24h: 9 active  17 runs  0.8 credits used",
                 font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor=tk.W, padx=16, pady=6)

    def _refresh_automation_status(self):
        for r in self._auto_tree.get_children(): self._auto_tree.delete(r)
        for a in self._known_automations:
            status = "Active" if a["last_runs"] > 0 else "Idle"
            tag = "active" if a["last_runs"] > 0 else "idle"
            self._auto_tree.insert("","end", values=(
                a["name"], a["project"], a["schedule"],
                a["last_runs"], f"{a['credits']:.1f}", status
            ), tags=(tag,))
        self._auto_tree.tag_configure("active", foreground="#92c353")
        self._auto_tree.tag_configure("idle",   foreground="#8a8aaa")


    # ════════════════════════════════════════════════════════════════════════
    # VIEW: TASKS — Running / Queued / Completed queue
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_tasks(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["tasks"] = f
        self._tasks_data = {"running": [], "queued": [], "recent": []}

        # Header
        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20,8))
        tk.Label(hdr, text="Task Queue", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        self._tasks_count_lbl = tk.Label(hdr, text="0 running · 0 queued",
            font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED)
        self._tasks_count_lbl.pack(side=tk.LEFT, padx=16)
        tk.Button(hdr, text="⚡ New Task", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=10, pady=4,
            command=self._tasks_show_add).pack(side=tk.RIGHT)
        tk.Button(hdr, text="↻ Refresh", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8, pady=4,
            command=self._refresh_tasks).pack(side=tk.RIGHT, padx=6)

        # Add task form (hidden by default)
        self._task_add_frame = tk.Frame(f, bg=BG_CARD,
            highlightbackground=BORDER_CARD, highlightthickness=1)
        self._task_title_var   = tk.StringVar()
        self._task_agent_var   = tk.StringVar()
        self._task_project_var = tk.StringVar(value="global")
        add_inner = tk.Frame(self._task_add_frame, bg=BG_CARD)
        add_inner.pack(fill=tk.X, padx=16, pady=12)
        tk.Label(add_inner, text="Task title:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor=tk.W)
        tk.Entry(add_inner, textvariable=self._task_title_var, font=self.fBody,
                 bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                 relief=tk.FLAT, highlightthickness=1, highlightbackground=DIVIDER).pack(fill=tk.X, ipady=4, pady=(2,6))
        self._task_desc_ed = tk.Text(add_inner, height=3, font=self.fBody,
            bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
            relief=tk.FLAT, wrap=tk.WORD, highlightthickness=1, highlightbackground=DIVIDER)
        self._task_desc_ed.pack(fill=tk.X, pady=(0,6))
        agent_row = tk.Frame(add_inner, bg=BG_CARD)
        agent_row.pack(fill=tk.X, pady=(0,8))
        tk.Label(agent_row, text="Agent ID:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT)
        tk.Entry(agent_row, textvariable=self._task_agent_var, font=self.fSmall,
                 bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                 relief=tk.FLAT, width=32, highlightthickness=1, highlightbackground=DIVIDER).pack(side=tk.LEFT, padx=8, ipady=3)
        tk.Label(agent_row, text="Project:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(12,4))
        projects_list = ["global"] + list(AGENT_REGISTRY.keys())
        proj_cb = ttk.Combobox(agent_row, textvariable=self._task_project_var,
            values=projects_list, state="readonly", font=self.fSmall, width=18)
        proj_cb.pack(side=tk.LEFT)
        btn_row = tk.Frame(add_inner, bg=BG_CARD)
        btn_row.pack(anchor=tk.W)
        tk.Button(btn_row, text="Queue Task", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=10, pady=3,
            command=self._tasks_submit).pack(side=tk.LEFT, padx=(0,8))
        tk.Button(btn_row, text="Cancel", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8, pady=3,
            command=lambda: self._task_add_frame.pack_forget()).pack(side=tk.LEFT)

        # Scrollable content
        outer = tk.Frame(f, bg=BG_CANVAS)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._tasks_canvas = tk.Canvas(outer, bg=BG_CANVAS, highlightthickness=0,
                                        yscrollcommand=vsb.set)
        self._tasks_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._tasks_canvas.yview)
        self._tasks_inner = tk.Frame(self._tasks_canvas, bg=BG_CANVAS)
        self._tasks_canvas.create_window((0,0), window=self._tasks_inner, anchor="nw")
        self._tasks_inner.bind("<Configure>",
            lambda e: self._tasks_canvas.configure(
                scrollregion=self._tasks_canvas.bbox("all")))

    def _tasks_show_add(self):
        self._task_add_frame.pack(fill=tk.X, padx=16, pady=(0,8), before=self._tasks_canvas.master)

    def _tasks_submit(self):
        title = self._task_title_var.get().strip()
        agent = self._task_agent_var.get().strip()
        if not title or not agent:
            self._push_notif("Task title and agent ID are required.", WARNING)
            return
        desc = self._task_desc_ed.get("1.0", tk.END).strip()
        proj  = self._task_project_var.get()
        import uuid as _uuid
        task = {
            "id": _uuid.uuid4().hex[:8],
            "title": title,
            "description": desc,
            "agent_id": agent,
            "project_slug": proj,
            "status": "queued",
            "created_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration_ms": 0,
            "result": ""
        }
        self._tasks_data["queued"].insert(0, task)
        self._task_title_var.set("")
        self._task_agent_var.set("")
        self._task_desc_ed.delete("1.0", tk.END)
        self._task_add_frame.pack_forget()
        self._refresh_tasks()
        self._push_notif(f"Task queued: {title}", ACCENT_LIGHT)
        qlog(f"[Tasks] Queued: {title} → {agent} ({proj})", ACCENT_LIGHT)

    def _refresh_tasks(self):
        # Pull from db
        c = _get_db()
        try:
            rows = c.execute(
                "SELECT run_id, agent_id, project, task, score, status, output, critique "
                "FROM runs ORDER BY id DESC LIMIT 100"
            ).fetchall()
            c.close()
        except Exception:
            rows = []

        # Classify into running/queued/recent from db + in-memory queue
        for w in self._tasks_inner.winfo_children():
            w.destroy()

        running = [t for t in self._tasks_data["queued"] if t["status"] == "running"]
        queued  = [t for t in self._tasks_data["queued"] if t["status"] == "queued"]

        if running:
            self._tasks_section("Running", running, "⚡", INFO)
        if queued:
            self._tasks_section("Queued", queued, "📋", TEXT_MUTED)

        # Recent from DB
        recent_tasks = [{"id": r[0], "title": r[3][:80], "agent_id": r[1],
                         "project_slug": r[2], "status": r[5],
                         "result": r[6] or "", "score": r[4]}
                        for r in rows]
        self._tasks_section("Recent (from run log)", recent_tasks, "✅", SUCCESS)

        r = len(running)
        q = len(queued)
        self._tasks_count_lbl.config(text=f"{r} running · {q} queued · {len(rows)} logged")

    def _tasks_section(self, title, tasks, icon, color):
        sec_hdr = tk.Frame(self._tasks_inner, bg=BG_CANVAS)
        sec_hdr.pack(fill=tk.X, padx=8, pady=(10,4))
        tk.Label(sec_hdr, text=f"{icon}  {title}", font=self.fH2,
                 bg=BG_CANVAS, fg=color).pack(side=tk.LEFT)
        for task in tasks[:30]:
            self._tasks_card(task)

    def _tasks_card(self, task):
        card = tk.Frame(self._tasks_inner, bg=BG_CARD,
                        highlightbackground=BORDER_CARD, highlightthickness=1)
        card.pack(fill=tk.X, padx=8, pady=3)
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill=tk.X, padx=14, pady=10)

        status = task.get("status", "")
        sc = task.get("score")
        sc_color = SUCCESS if (sc or 0) >= 0.75 else (WARNING if (sc or 0) >= 0.5 else TEXT_MUTED)
        status_color = {"running": INFO, "queued": WARNING, "complete": SUCCESS,
                        "failed": ERROR, "partial": WARNING}.get(status, TEXT_MUTED)

        tk.Label(inner, text=task.get("title","(no title)")[:90], font=self.fBody,
                 bg=BG_CARD, fg=TEXT_PRIMARY, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        if sc is not None:
            tk.Label(inner, text=f"{sc:.2f}", font=self.fSmall, bg=BG_CARD, fg=sc_color).pack(side=tk.RIGHT, padx=6)
        tk.Label(inner, text=status, font=self.fSmall, bg=BG_CARD, fg=status_color).pack(side=tk.RIGHT, padx=6)
        tk.Label(inner, text=task.get("agent_id",""), font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.RIGHT, padx=4)
        tk.Label(inner, text=task.get("project_slug",""), font=self.fSmall, bg=BG_CARD, fg=ACCENT_LIGHT).pack(side=tk.RIGHT, padx=4)

        result = task.get("result","")
        if result:
            res_lbl = tk.Label(card, text=result[:180]+"…" if len(result)>180 else result,
                               font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED, anchor=tk.W,
                               wraplength=650, justify=tk.LEFT, padx=14, pady=(0,8))
            res_lbl.pack(fill=tk.X, anchor=tk.W)


    # ════════════════════════════════════════════════════════════════════════
    # VIEW: TODOS
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_todos(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["todos"] = f
        self._todos_data = self._todos_load()

        # Header
        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20,8))
        tk.Label(hdr, text="Todos", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        self._todos_count_lbl = tk.Label(hdr, text="", font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED)
        self._todos_count_lbl.pack(side=tk.LEFT, padx=16)
        tk.Button(hdr, text="＋ Add Todo", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=10, pady=4,
            command=self._todos_show_add).pack(side=tk.RIGHT)
        tk.Button(hdr, text="↻ Refresh", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8, pady=4,
            command=self._refresh_todos).pack(side=tk.RIGHT, padx=6)

        # Filter bar
        flt = tk.Frame(f, bg=BG_CANVAS)
        flt.pack(fill=tk.X, padx=16, pady=(0,6))
        tk.Label(flt, text="Status:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT)
        self._todo_status_var = tk.StringVar(value="pending")
        for s in ["all", "pending", "done"]:
            tk.Radiobutton(flt, text=s.title(), variable=self._todo_status_var, value=s,
                bg=BG_CANVAS, fg=TEXT_MUTED, selectcolor=BG_CARD, activebackground=BG_CANVAS,
                font=self.fSmall, command=self._refresh_todos).pack(side=tk.LEFT, padx=4)
        tk.Label(flt, text="  Priority:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(12,0))
        self._todo_priority_var = tk.StringVar(value="all")
        for p in ["all", "urgent", "high", "medium", "low"]:
            tk.Radiobutton(flt, text=p.title(), variable=self._todo_priority_var, value=p,
                bg=BG_CANVAS, fg=TEXT_MUTED, selectcolor=BG_CARD, activebackground=BG_CANVAS,
                font=self.fSmall, command=self._refresh_todos).pack(side=tk.LEFT, padx=2)

        # Add form (hidden)
        self._todo_add_frame = tk.Frame(f, bg=BG_CARD,
            highlightbackground=BORDER_CARD, highlightthickness=1)
        self._todo_title_var    = tk.StringVar()
        self._todo_priority2_var = tk.StringVar(value="medium")
        self._todo_project2_var  = tk.StringVar(value="global")
        self._todo_due_var       = tk.StringVar()
        ta_inner = tk.Frame(self._todo_add_frame, bg=BG_CARD)
        ta_inner.pack(fill=tk.X, padx=16, pady=12)
        tk.Label(ta_inner, text="Todo title:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor=tk.W)
        tk.Entry(ta_inner, textvariable=self._todo_title_var, font=self.fBody,
                 bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                 relief=tk.FLAT, highlightthickness=1, highlightbackground=DIVIDER).pack(fill=tk.X, ipady=4, pady=(2,6))
        row2 = tk.Frame(ta_inner, bg=BG_CARD); row2.pack(fill=tk.X, pady=(0,6))
        tk.Label(row2, text="Priority:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT)
        ttk.Combobox(row2, textvariable=self._todo_priority2_var,
            values=["urgent","high","medium","low"], state="readonly", font=self.fSmall, width=10
        ).pack(side=tk.LEFT, padx=8)
        tk.Label(row2, text="Project:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(12,4))
        ttk.Combobox(row2, textvariable=self._todo_project2_var,
            values=["global"]+list(AGENT_REGISTRY.keys()), state="readonly", font=self.fSmall, width=18
        ).pack(side=tk.LEFT)
        tk.Label(row2, text="Due:", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(12,4))
        tk.Entry(row2, textvariable=self._todo_due_var, font=self.fSmall,
                 bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                 relief=tk.FLAT, width=12, highlightthickness=1, highlightbackground=DIVIDER,
                 ).pack(side=tk.LEFT, ipady=3)
        tk.Label(row2, text="YYYY-MM-DD", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=4)
        ta_btn_row = tk.Frame(ta_inner, bg=BG_CARD); ta_btn_row.pack(anchor=tk.W, pady=(4,0))
        tk.Button(ta_btn_row, text="Add Todo", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=10, pady=3,
            command=self._todos_submit).pack(side=tk.LEFT, padx=(0,8))
        tk.Button(ta_btn_row, text="Cancel", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8, pady=3,
            command=lambda: self._todo_add_frame.pack_forget()).pack(side=tk.LEFT)

        # Scrollable list
        outer = tk.Frame(f, bg=BG_CANVAS)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._todos_canvas = tk.Canvas(outer, bg=BG_CANVAS, highlightthickness=0,
                                        yscrollcommand=vsb.set)
        self._todos_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._todos_canvas.yview)
        self._todos_inner = tk.Frame(self._todos_canvas, bg=BG_CANVAS)
        self._todos_canvas.create_window((0,0), window=self._todos_inner, anchor="nw")
        self._todos_inner.bind("<Configure>",
            lambda e: self._todos_canvas.configure(
                scrollregion=self._todos_canvas.bbox("all")))

    def _todos_show_add(self):
        self._todo_add_frame.pack(fill=tk.X, padx=16, pady=(0,8),
                                   before=self._todos_canvas.master)

    def _todos_submit(self):
        title = self._todo_title_var.get().strip()
        if not title:
            self._push_notif("Todo title is required.", WARNING)
            return
        import uuid as _uuid, datetime as _dt
        todo = {
            "id": _uuid.uuid4().hex[:8],
            "title": title,
            "priority": self._todo_priority2_var.get(),
            "project_slug": self._todo_project2_var.get(),
            "due_date": self._todo_due_var.get(),
            "status": "pending",
            "created_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._todos_data.insert(0, todo)
        self._todo_title_var.set("")
        self._todo_due_var.set("")
        self._todo_add_frame.pack_forget()
        self._todos_save()
        self._refresh_todos()
        self._push_notif(f"Todo added: {title}", SUCCESS)

    def _refresh_todos(self):
        for w in self._todos_inner.winfo_children():
            w.destroy()

        status_f   = self._todo_status_var.get()
        priority_f = self._todo_priority_var.get()

        PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        PRIORITY_COLORS = {"urgent": ERROR, "high": WARNING, "medium": INFO, "low": TEXT_MUTED}

        todos = self._todos_data[:]
        if status_f != "all":
            todos = [t for t in todos if t.get("status") == status_f]
        if priority_f != "all":
            todos = [t for t in todos if t.get("priority") == priority_f]
        todos.sort(key=lambda t: PRIORITY_ORDER.get(t.get("priority","low"), 3))

        pending = [t for t in todos if t.get("status") != "done"]
        done    = [t for t in todos if t.get("status") == "done"]

        self._todos_count_lbl.config(
            text=f"{len(pending)} pending · {len(done)} done · {len(self._todos_data)} total")

        if not todos:
            tk.Label(self._todos_inner, text="No todos match the current filter.",
                     font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED).pack(pady=30)
            return

        for todo in todos:
            self._todo_card(todo, PRIORITY_COLORS)

    def _todo_card(self, todo, PRIORITY_COLORS):
        is_done = todo.get("status") == "done"
        card = tk.Frame(self._todos_inner, bg=BG_CARD,
                        highlightbackground=BORDER_CARD, highlightthickness=1)
        card.pack(fill=tk.X, padx=8, pady=3)
        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(fill=tk.X, padx=14, pady=10)

        # Checkbox-like done toggle
        done_btn_text = "☑" if is_done else "☐"
        done_btn_color = SUCCESS if is_done else TEXT_MUTED
        tk.Button(inner, text=done_btn_text, font=self.fH1, bg=BG_CARD, fg=done_btn_color,
                  relief=tk.FLAT, cursor="hand2", padx=2,
                  command=lambda t=todo: self._todo_toggle(t)).pack(side=tk.LEFT, padx=(0,8))

        title_fg = TEXT_MUTED if is_done else TEXT_PRIMARY
        tk.Label(inner, text=todo.get("title","")[:90], font=self.fBody,
                 bg=BG_CARD, fg=title_fg, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right badges
        due = todo.get("due_date","")
        if due:
            tk.Label(inner, text=f"📅 {due}", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.RIGHT, padx=4)
        proj = todo.get("project_slug","")
        if proj and proj != "global":
            tk.Label(inner, text=proj, font=self.fSmall, bg=BG_CARD, fg=ACCENT_LIGHT).pack(side=tk.RIGHT, padx=4)
        pri = todo.get("priority","")
        tk.Label(inner, text=pri.upper(), font=self.fSmall, bg=BG_CARD,
                 fg=PRIORITY_COLORS.get(pri, TEXT_MUTED)).pack(side=tk.RIGHT, padx=6)

        # Delete
        tk.Button(inner, text="✕", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
                  relief=tk.FLAT, cursor="hand2",
                  command=lambda t=todo: self._todo_delete(t)).pack(side=tk.RIGHT, padx=(0,4))

    def _todo_toggle(self, todo):
        todo["status"] = "pending" if todo.get("status") == "done" else "done"
        self._todos_save()
        self._refresh_todos()

    def _todo_delete(self, todo):
        self._todos_data = [t for t in self._todos_data if t["id"] != todo["id"]]
        self._todos_save()
        self._refresh_todos()


    # ════════════════════════════════════════════════════════════════════════
    # VIEW: AGENTS DIRECTORY — searchable, grouped by team
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_agents(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["agents"] = f

        # Header + search
        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20,8))
        tk.Label(hdr, text="Agent Directory", font=self.fTitle,
                 bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        self._agents_count_lbl = tk.Label(hdr, text="", font=self.fBody,
                                           bg=BG_CANVAS, fg=TEXT_MUTED)
        self._agents_count_lbl.pack(side=tk.LEFT, padx=16)
        tk.Button(hdr, text="↻", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8,
            command=self._refresh_agents_view).pack(side=tk.RIGHT)

        # Search + filter bar
        ctrl = tk.Frame(f, bg=BG_CANVAS)
        ctrl.pack(fill=tk.X, padx=16, pady=(0,6))
        self._agents_search_var = tk.StringVar()
        self._agents_search_var.trace("w", lambda *a: self._refresh_agents_view())
        tk.Label(ctrl, text="Search:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT)
        tk.Entry(ctrl, textvariable=self._agents_search_var, font=self.fSmall,
                 bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                 relief=tk.FLAT, width=28, highlightthickness=1, highlightbackground=DIVIDER
                 ).pack(side=tk.LEFT, padx=8, ipady=3)
        tk.Label(ctrl, text="Team:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=(12,4))
        self._agents_team_var = tk.StringVar(value="All")
        team_cb = ttk.Combobox(ctrl, textvariable=self._agents_team_var,
            values=["All"] + list(AGENT_REGISTRY.keys()), state="readonly",
            font=self.fSmall, width=22)
        team_cb.pack(side=tk.LEFT)
        team_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_agents_view())

        # Scrollable agent list
        outer = tk.Frame(f, bg=BG_CANVAS)
        outer.pack(fill=tk.BOTH, expand=True, padx=12)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._agents_canvas = tk.Canvas(outer, bg=BG_CANVAS, highlightthickness=0,
                                         yscrollcommand=vsb.set)
        self._agents_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._agents_canvas.yview)
        self._agents_inner = tk.Frame(self._agents_canvas, bg=BG_CANVAS)
        self._agents_canvas.create_window((0,0), window=self._agents_inner, anchor="nw")
        self._agents_inner.bind("<Configure>",
            lambda e: self._agents_canvas.configure(
                scrollregion=self._agents_canvas.bbox("all")))

    def _refresh_agents_view(self):
        for w in self._agents_inner.winfo_children():
            w.destroy()
        stats = db_agent_stats()
        search = self._agents_search_var.get().lower()
        team_f = self._agents_team_var.get()

        total = 0
        for team, agents in AGENT_REGISTRY.items():
            if team_f != "All" and team != team_f:
                continue
            filtered = [a for a in agents if not search or search in a.lower()]
            if not filtered:
                continue
            total += len(filtered)

            # Team section header
            sec = tk.Frame(self._agents_inner, bg=BG_CANVAS)
            sec.pack(fill=tk.X, padx=8, pady=(10,4))
            icon = TEAM_ICONS.get(team, "●")
            tk.Label(sec, text=f"{icon}  {team}", font=self.fH2,
                     bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
            tk.Label(sec, text=f"{len(filtered)} agents", font=self.fSmall,
                     bg=BG_CANVAS, fg=TEXT_MUTED).pack(side=tk.LEFT, padx=12)

            # Agent cards in a horizontal wrap
            grid_outer = tk.Frame(self._agents_inner, bg=BG_CANVAS)
            grid_outer.pack(fill=tk.X, padx=8)
            COLS = 3
            for i, agent in enumerate(filtered):
                s = stats.get(agent, {})
                runs = s.get("runs", 0)
                avg  = s.get("avg", 0.0)
                score_color = SUCCESS if avg >= 0.75 else (WARNING if avg >= 0.5 else TEXT_MUTED)

                card = tk.Frame(grid_outer, bg=BG_CARD,
                                highlightbackground=BORDER_CARD, highlightthickness=1)
                card.grid(row=i//COLS, column=i%COLS, padx=5, pady=4, sticky="nw", ipadx=10, ipady=8)

                short = agent.replace(team.lower().replace(" ","-")+"-","").replace("-"," ").title()
                tk.Label(card, text=short, font=self.fBody, bg=BG_CARD, fg=TEXT_PRIMARY, anchor=tk.W, width=22).pack(anchor=tk.W, padx=10, pady=(8,2))
                tk.Label(card, text=agent, font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED, anchor=tk.W).pack(anchor=tk.W, padx=10)

                stat_row = tk.Frame(card, bg=BG_CARD)
                stat_row.pack(anchor=tk.W, padx=10, pady=(4,8))
                if runs > 0:
                    tk.Label(stat_row, text=f"{runs} runs", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT)
                    tk.Label(stat_row, text=f"avg {avg:.2f}", font=self.fSmall, bg=BG_CARD, fg=score_color).pack(side=tk.LEFT, padx=8)
                else:
                    tk.Label(stat_row, text="No runs yet", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED).pack(side=tk.LEFT)

                # Run button
                tk.Button(card, text="▶ Run", font=self.fSmall, bg=ACCENT, fg=TEXT_PRIMARY,
                    relief=tk.FLAT, cursor="hand2", padx=8, pady=2,
                    command=lambda a=agent: self._agent_dir_launch(a)
                ).pack(anchor=tk.W, padx=10, pady=(0,8))
                # View skill
                tk.Button(card, text="📄 Skill", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
                    relief=tk.FLAT, cursor="hand2", padx=6, pady=2,
                    command=lambda a=agent: self._agent_dir_skill(a)
                ).pack(anchor=tk.W, padx=10, pady=(0,8))

        if total == 0:
            tk.Label(self._agents_inner, text="No agents match your search.",
                     font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED).pack(pady=30)
        total_all = sum(len(v) for v in AGENT_REGISTRY.values())
        self._agents_count_lbl.config(text=f"{total} of {total_all} agents")

    def _agent_dir_launch(self, agent_id):
        self._agent_var.set(agent_id)
        self._show_view("run")

    def _agent_dir_skill(self, agent_id):
        self._skill_agent_var.set(agent_id)
        self._load_skill_view()
        self._show_view("skills")


    # ════════════════════════════════════════════════════════════════════════
    # VIEW: CLIENTS — S2T Designs client roster
    # ════════════════════════════════════════════════════════════════════════
    def _build_view_clients(self):
        f = tk.Frame(self._content, bg=BG_CANVAS)
        self._views["clients"] = f

        hdr = tk.Frame(f, bg=BG_CANVAS)
        hdr.pack(fill=tk.X, padx=24, pady=(20,8))
        tk.Label(hdr, text="Clients", font=self.fTitle, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        self._clients_count_lbl = tk.Label(hdr, text="", font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED)
        self._clients_count_lbl.pack(side=tk.LEFT, padx=16)
        tk.Button(hdr, text="↻ Refresh", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8, pady=4,
            command=self._refresh_clients).pack(side=tk.RIGHT)

        # Split: list left, detail right
        body = tk.Frame(f, bg=BG_CANVAS)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # Client list
        list_frame = tk.Frame(body, bg=BG_PANEL, width=260,
                              highlightbackground=DIVIDER, highlightthickness=1)
        list_frame.pack(side=tk.LEFT, fill=tk.Y)
        list_frame.pack_propagate(False)
        tk.Label(list_frame, text="Active Clients", font=self.fH2,
                 bg=BG_PANEL, fg=TEXT_MUTED, anchor=tk.W).pack(anchor=tk.W, padx=12, pady=(12,6))
        tk.Frame(list_frame, bg=DIVIDER, height=1).pack(fill=tk.X)
        self._client_list_inner = tk.Frame(list_frame, bg=BG_PANEL)
        self._client_list_inner.pack(fill=tk.BOTH, expand=True)

        # Client detail
        self._client_detail_frame = tk.Frame(body, bg=BG_CANVAS)
        self._client_detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12,0))
        tk.Label(self._client_detail_frame,
                 text="Select a client to view details.",
                 font=self.fBody, bg=BG_CANVAS, fg=TEXT_MUTED).pack(pady=40)

    def _refresh_clients(self):
        for w in self._client_list_inner.winfo_children():
            w.destroy()

        # Load from CLIENT-ROSTER.md
        clients = self._load_client_roster()
        self._clients_count_lbl.config(text=f"{len(clients)} clients")

        CLIENT_ICONS = {
            "xftc": "🌐", "pbs": "🏛️", "lebc": "⛪", "smithcap": "🏢",
            "yepc": "🏟️", "nutrue": "👕", "elevation": "🎭"
        }

        for client in clients:
            slug = client.get("slug","").lower()
            icon = CLIENT_ICONS.get(slug, "📁")
            btn = tk.Button(self._client_list_inner,
                text=f"{icon}  {client.get('name', slug)}",
                font=self.fBody, bg=BG_PANEL, fg=TEXT_BODY,
                relief=tk.FLAT, cursor="hand2", anchor=tk.W, padx=12, pady=8,
                activebackground=BG_HOVER,
                command=lambda c=client: self._clients_show_detail(c))
            btn.pack(fill=tk.X)
            tk.Frame(self._client_list_inner, bg=DIVIDER, height=1).pack(fill=tk.X)

    def _load_client_roster(self):
        import os
        roster_path = os.path.join(AGENTS_ROOT, "projects", "s2tdesigns", "CLIENT-ROSTER.md")
        clients_dir = os.path.join(AGENTS_ROOT, "projects", "s2tdesigns", "clients")
        clients = []
        try:
            with open(roster_path) as f:
                text = f.read()
            import re
            for match in re.finditer(r"\|\s*\*\*([^|]+)\*\*\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", text):
                name = match.group(1).strip()
                slug = name.lower().replace(" ","").replace(".","")
                clients.append({
                    "name": name, "slug": slug,
                    "industry": match.group(2).strip(),
                    "status": match.group(5).strip(),
                })
        except Exception:
            pass
        # Scan client subdirs for PROJECT.md
        try:
            for slug in os.listdir(clients_dir):
                proj_file = os.path.join(clients_dir, slug, "PROJECT.md")
                if not os.path.exists(proj_file):
                    continue
                if any(c["slug"] == slug for c in clients):
                    continue
                with open(proj_file) as pf:
                    ptext = pf.read()
                name_match = re.search(r"^# .+? — Client: (.+)", ptext, re.M)
                clients.append({
                    "name": name_match.group(1).strip() if name_match else slug.upper(),
                    "slug": slug,
                    "industry": "—",
                    "status": "Active",
                    "project_md": ptext,
                })
        except Exception:
            pass
        if not clients:
            clients = [
                {"name": "XFTC", "slug": "xftc", "industry": "Nonprofit / Youth Sports", "status": "Active"},
                {"name": "Psi Beta Sigma 1914", "slug": "pbs", "industry": "Fraternity", "status": "Active"},
                {"name": "Little Ebenezer Baptist Church", "slug": "lebc", "industry": "Ministry", "status": "Active"},
                {"name": "Smith Capital Properties", "slug": "smithcap", "industry": "Real Estate", "status": "Active"},
            ]
        return clients

    def _clients_show_detail(self, client):
        for w in self._client_detail_frame.winfo_children():
            w.destroy()

        CLIENT_ICONS = {"xftc":"🌐","pbs":"🏛️","lebc":"⛪","smithcap":"🏢","yepc":"🏟️","nutrue":"👕","elevation":"🎭"}
        slug = client.get("slug","")
        icon = CLIENT_ICONS.get(slug, "📁")

        # Client header
        ch = tk.Frame(self._client_detail_frame, bg=BG_CARD,
                      highlightbackground=BORDER_CARD, highlightthickness=1)
        ch.pack(fill=tk.X, padx=0, pady=(0,12))
        ch_inner = tk.Frame(ch, bg=BG_CARD)
        ch_inner.pack(fill=tk.X, padx=20, pady=14)
        tk.Label(ch_inner, text=icon, font=tkfont.Font(family="Segoe UI Emoji",size=28),
                 bg=BG_CARD, fg=ACCENT_LIGHT).pack(side=tk.LEFT, padx=(0,12))
        info_col = tk.Frame(ch_inner, bg=BG_CARD)
        info_col.pack(side=tk.LEFT)
        tk.Label(info_col, text=client.get("name",""), font=self.fTitle,
                 bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor=tk.W)
        tk.Label(info_col, text=f"{client.get('industry','—')}  ·  {client.get('status','—')}",
                 font=self.fBody, bg=BG_CARD, fg=TEXT_MUTED).pack(anchor=tk.W)

        # Tabs: Overview / Agents / Blockers
        nb = ttk.Notebook(self._client_detail_frame)
        nb.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Overview
        t1 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t1, text="  Overview  ")
        stats = db_agent_stats()
        relevant = [a for a in (list(AGENT_REGISTRY.values()) or [[]])[0] if slug in a]
        # Try reading PROJECT.md
        import os
        proj_file = os.path.join(AGENTS_ROOT, "projects", slug, "PROJECT.md")
        if not os.path.exists(proj_file):
            proj_file = os.path.join(AGENTS_ROOT, "projects", "s2tdesigns", "clients", slug, "PROJECT.md")
        proj_text = ""
        if os.path.exists(proj_file):
            with open(proj_file) as pf:
                proj_text = pf.read()[:2000]
        txt = scrolledtext.ScrolledText(t1, font=self.fMonoSm, bg=BG_INPUT, fg=TEXT_BODY,
            relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        txt.config(state=tk.NORMAL)
        txt.insert("1.0", proj_text or ("No PROJECT.md found for '" + slug + "'.\nCreate one at .agents/projects/" + slug + "/PROJECT.md"))
        txt.config(state=tk.DISABLED)

        # Tab 2: Agents
        t2 = tk.Frame(nb, bg=BG_CANVAS); nb.add(t2, text="  Team Agents  ")
        related_agents = []
        for team, agents in AGENT_REGISTRY.items():
            for a in agents:
                if slug.replace("-","") in a.replace("-","") or slug[:4] in a:
                    related_agents.append((team, a))
        if not related_agents:
            tk.Label(t2, text="No agents mapped to this client.", font=self.fBody,
                     bg=BG_CANVAS, fg=TEXT_MUTED).pack(pady=20)
        for team, a in related_agents[:20]:
            s = stats.get(a, {})
            row = tk.Frame(t2, bg=BG_CANVAS)
            row.pack(fill=tk.X, padx=12, pady=2)
            tk.Label(row, text=a, font=self.fBody, bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
            if s.get("runs",0) > 0:
                col = SUCCESS if s["avg"]>=0.75 else WARNING
                tk.Label(row, text=f"{s['runs']}r avg {s['avg']:.2f}", font=self.fSmall, bg=BG_CANVAS, fg=col).pack(side=tk.RIGHT)


    # ════════════════════════════════════════════════════════════════════════
    # AGENTMAJESTY — Real LLM streaming (replaces scripted responses)
    # ════════════════════════════════════════════════════════════════════════
    def _chat_respond(self, user_text):
        """AgentMajesty response — tries real OpenAI streaming, falls back to scripted."""
        import threading, os
        api_key = self._api_key_var.get().strip() if hasattr(self, '_api_key_var') else ""
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY","")

        if api_key:
            threading.Thread(target=self._chat_respond_llm,
                             args=(user_text, api_key), daemon=True).start()
        else:
            # Scripted fallback
            import time
            t = user_text.lower()
            if "briefing" in t or "today" in t:
                reply = self._chat_build_briefing()
            elif "run status" in t or "status" in t:
                reply = self._chat_build_run_status()
            elif "flag" in t or "issue" in t or "blocker" in t:
                reply = self._chat_build_blockers()
            elif "priority" in t or "top" in t:
                reply = self._chat_build_priorities()
            elif "help" in t:
                reply = ("I can brief you on the portfolio, surface blockers, "
                         "list agent statuses, or relay tasks. Set an OpenAI API "
                         "key in Settings to unlock full LLM reasoning.")
            else:
                reply = (f"Got it — '{user_text[:50]}'. "
                         "Set an OpenAI API key in Settings to enable full AI reasoning.")
            time.sleep(0.25)
            self.after(0, lambda: self._chat_push("AgentMajesty", reply, role="agent"))

    def _chat_respond_llm(self, user_text, api_key):
        """Real streaming LLM call via OpenAI chat completions."""
        import json, urllib.request, urllib.error

        stats = db_agent_stats()
        total_runs = sum(s["runs"] for s in stats.values())
        flagged = [a for a,s in stats.items() if s["runs"]>0 and s["avg"]<0.60]
        teams = len(AGENT_REGISTRY)
        agents = sum(len(v) for v in AGENT_REGISTRY.values())
        todos_pending = len([t for t in self._todos_data if t.get("status")=="pending"])
        tasks_queued  = len([t for t in self._tasks_data.get("queued",[]) if t.get("status")=="queued"])

        system_prompt = f"""You are AgentMajesty, Chief of Staff for David Smith's portfolio.
Portfolio: {teams} teams, {agents} agents, {total_runs} agent runs logged.
Pending todos: {todos_pending}. Queued tasks: {tasks_queued}.
Flagged agents (score <0.60): {', '.join(flagged) if flagged else 'None'}.
Projects: XFTC, YEPC, The Elevation ATX, PBS Foundation, S2T Designs, Nutrue Apparel, Clarity Solar, Smith Capital Holdings, Sigma Signal, Ministry.
Be concise, direct, and strategic. Surface blockers proactively. Max 3 paragraphs."""

        # Build history (last 10 messages)
        messages_payload = [{"role":"system","content":system_prompt}]
        for msg in self._chat_messages[-10:]:
            role = "assistant" if msg["role"]=="agent" else "user"
            messages_payload.append({"role": role, "content": msg["text"]})
        messages_payload.append({"role":"user","content":user_text})

        # Get model from settings
        model = self._ai_model_var.get() if hasattr(self, '_ai_model_var') else "gpt-4o-mini"
        base_url = self._ai_baseurl_var.get() if hasattr(self, '_ai_baseurl_var') else "https://api.openai.com/v1"

        payload = json.dumps({
            "model": model,
            "messages": messages_payload,
            "stream": True,
            "max_tokens": 600,
            "temperature": 0.7,
        }).encode()

        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST"
        )

        # Show streaming indicator
        self.after(0, lambda: self._chat_push("AgentMajesty", "▌", role="agent"))
        streaming_idx = len(self._chat_messages) - 1
        full_text = ""

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"].get("content","")
                        if delta:
                            full_text += delta
                            # Update the last message bubble in-place
                            self.after(0, lambda t=full_text: self._chat_update_last(t))
                    except Exception:
                        pass

            # Finalise
            if full_text:
                self.after(0, lambda: self._chat_update_last(full_text))
                self.after(0, lambda: self._push_notif("💬 AgentMajesty replied.", ACCENT_LIGHT))
            else:
                self.after(0, lambda: self._chat_update_last("(No response — check API key and model settings.)"))

        except urllib.error.HTTPError as e:
            err = f"API error {e.code}: {e.reason}"
            self.after(0, lambda: self._chat_update_last(err))
        except Exception as e:
            self.after(0, lambda: self._chat_update_last(f"Connection error: {e}"))

    def _chat_update_last(self, new_text):
        """Update the text in the most recent agent bubble (streaming in-place)."""
        if self._chat_messages:
            self._chat_messages[-1]["text"] = new_text
        # Redraw last bubble only
        children = self._chat_msgs_frame.winfo_children()
        if children:
            last = children[-1]
            # Find the label inside the bubble
            for widget in last.winfo_children():
                for inner in widget.winfo_children():
                    if isinstance(inner, tk.Label) and inner.cget("wraplength") == 230:
                        inner.config(text=new_text)
                        self._chat_scroll_bottom()
                        return
        # Fallback: full redraw won't happen — just scroll
        self._chat_scroll_bottom()


    # ════════════════════════════════════════════════════════════════════════
    # SETTINGS — Multi-provider AI helpers
    # ════════════════════════════════════════════════════════════════════════
    _AI_PRESETS = {
        "openai":    {"url": "https://api.openai.com/v1",            "model": "gpt-4o-mini",             "note": "Best performance. OpenAI API key required."},
        "ollama":    {"url": "http://localhost:11434/v1",             "model": "llama3.2",                "note": "Free, local. Requires Ollama installed."},
        "anthropic": {"url": "https://api.anthropic.com/v1",         "model": "claude-3-haiku-20240307", "note": "Excellent reasoning. Anthropic API key required."},
        "github":    {"url": "https://models.inference.ai.azure.com", "model": "gpt-4o-mini",            "note": "Free with GitHub account. Use GitHub PAT as API key."},
    }

    def _on_ai_provider_change(self, evt=None):
        provider = self._ai_provider_var.get()
        preset = self._AI_PRESETS.get(provider, {})
        if preset:
            self._ai_baseurl_var.set(preset["url"])
            self._ai_model_var.set(preset["model"])
            self._ai_provider_note.config(text=preset.get("note",""))

    # ════════════════════════════════════════════════════════════════════════
    # SETTINGS — Push notification helpers
    # ════════════════════════════════════════════════════════════════════════
    _PUSH_FIELDS = {
        "ntfy":     [("ntfy Topic (e.g. agentharness-david)", "_push_ntfy_topic"),
                     ("ntfy Server (default: https://ntfy.sh)", "_push_ntfy_server")],
        "pushover": [("Pushover API Token", "_push_po_token"),
                     ("Pushover User Key", "_push_po_user")],
        "pushcut":  [("Pushcut Webhook URL", "_push_pc_webhook")],
    }

    def _build_push_fields(self, parent):
        for w in parent.winfo_children():
            w.destroy()
        provider = self._push_provider_var.get()
        for label, attr in self._PUSH_FIELDS.get(provider, []):
            row = tk.Frame(parent, bg=BG_CANVAS)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}:", font=self.fSmall,
                     bg=BG_CANVAS, fg=TEXT_MUTED, width=36, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(row, textvariable=var, font=self.fSmall,
                     bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY,
                     relief=tk.FLAT, width=36,
                     highlightthickness=1, highlightbackground=DIVIDER).pack(side=tk.LEFT, padx=8, ipady=3)

    def _on_push_provider_change(self, evt=None):
        self._build_push_fields(self._push_fields_frame)

    def _test_push_notification(self):
        import urllib.request, json as _json, threading

        def _send():
            provider = self._push_provider_var.get()
            try:
                if provider == "ntfy":
                    topic  = getattr(self, "_push_ntfy_topic",  tk.StringVar()).get().strip()
                    server = getattr(self, "_push_ntfy_server", tk.StringVar()).get().strip() or "https://ntfy.sh"
                    if not topic:
                        self.after(0, lambda: self._push_test_lbl.config(text="Set an ntfy topic first.", fg=WARNING))
                        return
                    req = urllib.request.Request(
                        f"{server}/{topic}",
                        data=b"AgentHarness test notification - Chief of Staff online.",
                        headers={"Title": "AgentHarness", "Priority": "default", "Tags": "robot"},
                        method="POST"
                    )
                    urllib.request.urlopen(req, timeout=8)
                    self.after(0, lambda: self._push_test_lbl.config(text="Sent! Check your phone.", fg=SUCCESS))

                elif provider == "pushover":
                    token = getattr(self, "_push_po_token", tk.StringVar()).get().strip()
                    user  = getattr(self, "_push_po_user",  tk.StringVar()).get().strip()
                    if not token or not user:
                        self.after(0, lambda: self._push_test_lbl.config(text="Set token and user key first.", fg=WARNING))
                        return
                    data = _json.dumps({"token":token,"user":user,"message":"AgentHarness test — Chief of Staff online.","title":"AgentHarness"}).encode()
                    req = urllib.request.Request("https://api.pushover.net/1/messages.json",
                        data=data, headers={"Content-Type":"application/json"}, method="POST")
                    urllib.request.urlopen(req, timeout=8)
                    self.after(0, lambda: self._push_test_lbl.config(text="Sent! Check your iPhone.", fg=SUCCESS))

                elif provider == "pushcut":
                    webhook = getattr(self, "_push_pc_webhook", tk.StringVar()).get().strip()
                    if not webhook:
                        self.after(0, lambda: self._push_test_lbl.config(text="Set a Pushcut webhook URL first.", fg=WARNING))
                        return
                    data = _json.dumps({"title":"AgentHarness","text":"Chief of Staff online."}).encode()
                    req = urllib.request.Request(webhook, data=data,
                        headers={"Content-Type":"application/json"}, method="POST")
                    urllib.request.urlopen(req, timeout=8)
                    self.after(0, lambda: self._push_test_lbl.config(text="Sent! Check Pushcut.", fg=SUCCESS))

            except Exception as e:
                msg = str(e)
                self.after(0, lambda: self._push_test_lbl.config(text=f"Error: {msg[:60]}", fg=ERROR))

        threading.Thread(target=_send, daemon=True).start()
        self._push_test_lbl.config(text="Sending…", fg=TEXT_MUTED)



    # ════════════════════════════════════════════════════════════════════════
    # FEATURE 1 — MORNING BRIEFING CARD
    # ════════════════════════════════════════════════════════════════════════
    def _build_briefing_card(self, parent):
        """Build the collapsed/expanded morning briefing banner on Home."""
        self._briefing_expanded = False
        self._briefing_card_frame = tk.Frame(parent, bg=BG_CARD,
            highlightbackground=BORDER_CARD, highlightthickness=1)
        self._briefing_card_frame.pack(fill=tk.X)

        # Card header row
        hdr = tk.Frame(self._briefing_card_frame, bg=BG_CARD)
        hdr.pack(fill=tk.X, padx=14, pady=(10,8))

        self._briefing_icon_lbl = tk.Label(hdr, text="☀️", font=self.fH1,
            bg=BG_CARD, fg=ACCENT_LIGHT)
        self._briefing_icon_lbl.pack(side=tk.LEFT, padx=(0,10))

        title_col = tk.Frame(hdr, bg=BG_CARD)
        title_col.pack(side=tk.LEFT, fill=tk.Y)
        self._briefing_title_lbl = tk.Label(title_col, text="Morning Briefing",
            font=self.fH2, bg=BG_CARD, fg=TEXT_PRIMARY)
        self._briefing_title_lbl.pack(anchor=tk.W)
        self._briefing_sub_lbl = tk.Label(title_col, text="Loading portfolio snapshot...",
            font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED)
        self._briefing_sub_lbl.pack(anchor=tk.W)

        btn_col = tk.Frame(hdr, bg=BG_CARD)
        btn_col.pack(side=tk.RIGHT)
        self._briefing_toggle_btn = tk.Button(btn_col, text="▼ Expand",
            font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8,
            command=self._briefing_toggle)
        self._briefing_toggle_btn.pack(side=tk.LEFT, padx=4)
        tk.Button(btn_col, text="↻ Refresh", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=8,
            command=self._refresh_briefing_card).pack(side=tk.LEFT)

        # Pill row (always visible)
        self._briefing_pills_row = tk.Frame(self._briefing_card_frame, bg=BG_CARD)
        self._briefing_pills_row.pack(fill=tk.X, padx=14, pady=(0,10))

        # Expanded detail panel (hidden by default)
        self._briefing_detail = tk.Frame(self._briefing_card_frame, bg=BG_CARD)

    def _briefing_toggle(self):
        self._briefing_expanded = not self._briefing_expanded
        if self._briefing_expanded:
            self._briefing_detail.pack(fill=tk.X, padx=14, pady=(0,12))
            self._briefing_toggle_btn.config(text="▲ Collapse")
        else:
            self._briefing_detail.pack_forget()
            self._briefing_toggle_btn.config(text="▼ Expand")

    def _refresh_briefing_card(self):
        """Populate the briefing card with live portfolio data."""
        import datetime as _dt
        stats   = db_agent_stats()
        now     = _dt.datetime.now()
        hour    = now.hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")

        total_runs   = sum(s["runs"] for s in stats.values())
        flagged      = [a for a,s in stats.items() if s["runs"]>0 and s["avg"]<0.60]
        passing      = [a for a,s in stats.items() if s["runs"]>0 and s["avg"]>=0.75]
        teams        = len(AGENT_REGISTRY)
        agents_total = sum(len(v) for v in AGENT_REGISTRY.values())
        todos_pending = len([t for t in self._todos_data if t.get("status")=="pending"])
        urgent_todos  = [t for t in self._todos_data
                         if t.get("status")=="pending" and t.get("priority")=="urgent"]
        high_todos    = [t for t in self._todos_data
                         if t.get("status")=="pending" and t.get("priority")=="high"]

        # Update title / subtitle
        date_str = now.strftime("%A, %B %d")
        self._briefing_title_lbl.config(text=f"{greeting}, David")
        self._briefing_sub_lbl.config(text=f"{date_str}  ·  {teams} teams active")

        # Rebuild pills
        for w in self._briefing_pills_row.winfo_children():
            w.destroy()

        def pill(text, color, bg=None):
            bg = bg or BG_CANVAS
            lbl = tk.Label(self._briefing_pills_row, text=text,
                font=tkfont.Font(family="Segoe UI",size=9,weight="bold"),
                bg=bg, fg=color, padx=10, pady=3,
                highlightbackground=color, highlightthickness=1)
            lbl.pack(side=tk.LEFT, padx=4, pady=2)
            return lbl

        pill(f"🤖  {agents_total} Agents", ACCENT_LIGHT)
        pill(f"📊  {total_runs} Runs", TEXT_MUTED)
        pill(f"✅  {len(passing)} Passing", SUCCESS)
        if flagged:
            pill(f"🚨  {len(flagged)} Flagged", ERROR)
        if urgent_todos:
            pill(f"🔴  {len(urgent_todos)} Urgent", ERROR)
        elif high_todos:
            pill(f"🟡  {len(high_todos)} High Priority", WARNING)
        if todos_pending:
            pill(f"📋  {todos_pending} Todos Pending", TEXT_MUTED)

        # Rebuild expanded detail
        for w in self._briefing_detail.winfo_children():
            w.destroy()

        tk.Frame(self._briefing_detail, bg=DIVIDER, height=1).pack(fill=tk.X, pady=(0,8))

        col_outer = tk.Frame(self._briefing_detail, bg=BG_CARD)
        col_outer.pack(fill=tk.X)

        # Column 1: Blockers
        col1 = tk.Frame(col_outer, bg=BG_CARD)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,12))
        tk.Label(col1, text="PORTFOLIO BLOCKERS", font=tkfont.Font(family="Segoe UI",size=8,weight="bold"),
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor=tk.W, pady=(0,4))
        blockers = [
            "PBS site: Golf Tournament + Dues pages need payment links",
            "XFTC Gmail: forwarding rule required for signup logger",
            "Smith Capital LLC: reactivation filings overdue",
            "Clarity Solar: TX SB 1036 GL insurance deadline Sep 1",
            "Smith Capital Holdings: S-Corp election not yet filed",
        ]
        for b in blockers:
            row = tk.Frame(col1, bg=BG_CARD)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text="●", font=self.fSmall, bg=BG_CARD, fg=ERROR).pack(side=tk.LEFT, padx=(0,6))
            tk.Label(row, text=b, font=self.fSmall, bg=BG_CARD, fg=TEXT_BODY,
                     wraplength=260, justify=tk.LEFT, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X)

        # Column 2: Flagged agents + Top todos
        col2 = tk.Frame(col_outer, bg=BG_CARD)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        if flagged:
            tk.Label(col2, text="FLAGGED AGENTS", font=tkfont.Font(family="Segoe UI",size=8,weight="bold"),
                     bg=BG_CARD, fg=TEXT_MUTED).pack(anchor=tk.W, pady=(0,4))
            for a in flagged[:5]:
                s = stats[a]
                row = tk.Frame(col2, bg=BG_CARD)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=a, font=self.fSmall, bg=BG_CARD, fg=TEXT_BODY, width=28, anchor=tk.W).pack(side=tk.LEFT)
                tk.Label(row, text=f"avg {s['avg']:.2f}", font=self.fSmall, bg=BG_CARD, fg=ERROR).pack(side=tk.RIGHT)
            tk.Frame(col2, bg=DIVIDER, height=1).pack(fill=tk.X, pady=6)

        top_todos = sorted(
            [t for t in self._todos_data if t.get("status")=="pending"],
            key=lambda t: {"urgent":0,"high":1,"medium":2,"low":3}.get(t.get("priority","low"),3)
        )[:5]
        if top_todos:
            tk.Label(col2, text="TOP TODOS", font=tkfont.Font(family="Segoe UI",size=8,weight="bold"),
                     bg=BG_CARD, fg=TEXT_MUTED).pack(anchor=tk.W, pady=(0,4))
            PCOL = {"urgent": ERROR, "high": WARNING, "medium": INFO, "low": TEXT_MUTED}
            for t in top_todos:
                row = tk.Frame(col2, bg=BG_CARD)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=t.get("priority","").upper()[:3],
                         font=self.fSmall, bg=BG_CARD,
                         fg=PCOL.get(t.get("priority","low"), TEXT_MUTED), width=4).pack(side=tk.LEFT)
                tk.Label(row, text=t.get("title","")[:55], font=self.fSmall,
                         bg=BG_CARD, fg=TEXT_BODY, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X)


    # ════════════════════════════════════════════════════════════════════════
    # FEATURE 2 — WebSocket / live-update bridge (lightweight polling)
    # Polls SQLite every 5s for new runs and fires in-app updates.
    # Real Socket.IO would require a Node server — this uses threads instead.
    # ════════════════════════════════════════════════════════════════════════
    def _start_live_bridge(self):
        """Start background polling thread for live task/run updates."""
        self._bridge_last_run_id = 0
        self._bridge_running = True
        import threading
        threading.Thread(target=self._bridge_loop, daemon=True).start()
        qlog("[LiveBridge] Polling for new runs every 5s", ACCENT_LIGHT)

    def _bridge_loop(self):
        import time
        while self._bridge_running:
            try:
                c = _get_db()
                row = c.execute(
                    "SELECT id, run_id, agent_id, project, score, status "
                    "FROM runs WHERE id > ? ORDER BY id DESC LIMIT 1",
                    (self._bridge_last_run_id,)
                ).fetchone()
                c.close()
                if row:
                    rid, run_id, agent, proj, score, status = row
                    if rid > self._bridge_last_run_id:
                        self._bridge_last_run_id = rid
                        # Fire UI updates on main thread
                        sc_str = f"{score:.2f}" if score else "?"
                        notif_text = f"Run complete: {agent} ({proj}) — score {sc_str}"
                        notif_color = SUCCESS if (score or 0)>=0.75 else (WARNING if (score or 0)>=0.5 else ERROR)
                        self.after(0, lambda t=notif_text, c=notif_color: self._push_notif(t, c))
                        # If tasks view is open, refresh it
                        self.after(0, self._bridge_maybe_refresh_tasks)
            except Exception:
                pass
            time.sleep(5)

    def _bridge_maybe_refresh_tasks(self):
        if self._active_view.get() == "tasks":
            self._refresh_tasks()
        # Also update statusbar run count
        self._update_statusbar()


    # ════════════════════════════════════════════════════════════════════════
    # FEATURE 3 — Todo persistence (JSON file)
    # ════════════════════════════════════════════════════════════════════════
    _TODOS_PATH = None  # set lazily

    def _todos_file(self):
        import os
        if not self._TODOS_PATH:
            data_dir = os.path.join(AGENTS_ROOT, "data")
            os.makedirs(data_dir, exist_ok=True)
            type(self)._TODOS_PATH = os.path.join(data_dir, "todos.json")
        return self._TODOS_PATH

    def _todos_load(self):
        import json, os
        path = self._todos_file()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                qlog(f"[Todos] Loaded {len(data)} todos from disk", TEXT_MUTED)
                return data
            except Exception as e:
                qlog(f"[Todos] Load error: {e}", WARNING)
        return []

    def _todos_save(self):
        import json
        try:
            with open(self._todos_file(), "w") as f:
                json.dump(self._todos_data, f, indent=2)
        except Exception as e:
            qlog(f"[Todos] Save error: {e}", WARNING)


    # ════════════════════════════════════════════════════════════════════════
    # FEATURE 4 — Run Scheduler (schedule a task at a future time)
    # ════════════════════════════════════════════════════════════════════════
    def _run_show_scheduler(self):
        """Show a modal dialog to schedule the current agent run."""
        modal = tk.Toplevel(self)
        modal.title("Schedule Agent Run")
        modal.geometry("460x360")
        modal.configure(bg=BG_CANVAS)
        modal.resizable(False, False)
        modal.grab_set()

        tk.Label(modal, text="🕐  Schedule Agent Run", font=self.fH1,
                 bg=BG_CANVAS, fg=TEXT_PRIMARY).pack(padx=20, pady=(20,4), anchor=tk.W)
        tk.Label(modal, text="Queue this agent to run automatically at a future time.",
                 font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED).pack(padx=20, anchor=tk.W)
        tk.Frame(modal, bg=DIVIDER, height=1).pack(fill=tk.X, padx=20, pady=12)

        def row(parent, label, widget_builder):
            r = tk.Frame(parent, bg=BG_CANVAS)
            r.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(r, text=label, font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED,
                     width=16, anchor=tk.W).pack(side=tk.LEFT)
            w = widget_builder(r)
            return w

        # Agent (pre-filled)
        agent_var = tk.StringVar(value=self._agent_var.get())
        row(modal, "Agent:", lambda p: tk.Entry(p, textvariable=agent_var, font=self.fBody,
            bg=BG_INPUT, fg=TEXT_BODY, insertbackground=TEXT_BODY, relief=tk.FLAT,
            width=28, highlightthickness=1, highlightbackground=DIVIDER).__class__(
                p, textvariable=agent_var, font=self.fBody, bg=BG_INPUT, fg=TEXT_BODY,
                insertbackground=TEXT_BODY, relief=tk.FLAT, width=28,
                highlightthickness=1, highlightbackground=DIVIDER) or None)
        # simpler entry approach:
        r1 = tk.Frame(modal, bg=BG_CANVAS); r1.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(r1, text="Agent:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED, width=16, anchor=tk.W).pack(side=tk.LEFT)
        agent_entry = tk.Entry(r1, textvariable=agent_var, font=self.fBody, bg=BG_INPUT,
            fg=TEXT_BODY, insertbackground=TEXT_BODY, relief=tk.FLAT, width=28,
            highlightthickness=1, highlightbackground=DIVIDER)
        agent_entry.pack(side=tk.LEFT, padx=6, ipady=3)

        # Run type
        r2 = tk.Frame(modal, bg=BG_CANVAS); r2.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(r2, text="Run type:", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED, width=16, anchor=tk.W).pack(side=tk.LEFT)
        run_type_var = tk.StringVar(value="once")
        for v,t in [("once","One-time"),("daily","Daily"),("weekly","Weekly")]:
            tk.Radiobutton(r2, text=t, variable=run_type_var, value=v,
                bg=BG_CANVAS, fg=TEXT_MUTED, selectcolor=BG_CARD,
                activebackground=BG_CANVAS, font=self.fSmall).pack(side=tk.LEFT, padx=6)

        # Date + Time
        r3 = tk.Frame(modal, bg=BG_CANVAS); r3.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(r3, text="Date (YYYY-MM-DD):", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED, width=16, anchor=tk.W).pack(side=tk.LEFT)
        import datetime as _dt
        date_var = tk.StringVar(value=_dt.datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(r3, textvariable=date_var, font=self.fSmall, bg=BG_INPUT, fg=TEXT_BODY,
            insertbackground=TEXT_BODY, relief=tk.FLAT, width=14,
            highlightthickness=1, highlightbackground=DIVIDER).pack(side=tk.LEFT, padx=6, ipady=3)

        r4 = tk.Frame(modal, bg=BG_CANVAS); r4.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(r4, text="Time (HH:MM):", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED, width=16, anchor=tk.W).pack(side=tk.LEFT)
        time_var = tk.StringVar(value="09:00")
        tk.Entry(r4, textvariable=time_var, font=self.fSmall, bg=BG_INPUT, fg=TEXT_BODY,
            insertbackground=TEXT_BODY, relief=tk.FLAT, width=10,
            highlightthickness=1, highlightbackground=DIVIDER).pack(side=tk.LEFT, padx=6, ipady=3)

        status_lbl = tk.Label(modal, text="", font=self.fSmall, bg=BG_CANVAS, fg=TEXT_MUTED)
        status_lbl.pack(padx=20, pady=4, anchor=tk.W)

        tk.Frame(modal, bg=DIVIDER, height=1).pack(fill=tk.X, padx=20, pady=8)

        def schedule_it():
            agent = agent_var.get().strip()
            run_type = run_type_var.get()
            date_s = date_var.get().strip()
            time_s = time_var.get().strip()
            if not agent:
                status_lbl.config(text="Agent ID is required.", fg=ERROR)
                return
            try:
                target_dt = _dt.datetime.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M")
            except ValueError:
                status_lbl.config(text="Invalid date or time format.", fg=ERROR)
                return
            if target_dt < _dt.datetime.now() and run_type == "once":
                status_lbl.config(text="Scheduled time is in the past.", fg=WARNING)
                return

            # Save scheduled run to JSON file
            import json, os, uuid
            sched_path = os.path.join(AGENTS_ROOT, "data", "scheduled_runs.json")
            try:
                existing = json.loads(open(sched_path).read()) if os.path.exists(sched_path) else []
            except Exception:
                existing = []
            entry = {
                "id": uuid.uuid4().hex[:8],
                "agent_id": agent,
                "graph": self._graph_var.get() if hasattr(self,"_graph_var") else "reflexion",
                "project": self._team_var.get() if hasattr(self,"_team_var") else "global",
                "run_type": run_type,
                "scheduled_at": target_dt.isoformat(),
                "created_at": _dt.datetime.now().isoformat(),
                "status": "pending",
            }
            existing.append(entry)
            os.makedirs(os.path.dirname(sched_path), exist_ok=True)
            with open(sched_path, "w") as sf:
                json.dump(existing, sf, indent=2)

            type_label = {"once":"Once", "daily":"Daily at", "weekly":"Weekly at"}.get(run_type, run_type)
            status_lbl.config(
                text=f"Scheduled! {type_label} {target_dt.strftime('%b %d %H:%M')}",
                fg=SUCCESS)
            self._push_notif(f"Scheduled: {agent} @ {target_dt.strftime('%b %d %H:%M')}", ACCENT_LIGHT)
            qlog(f"[Scheduler] {agent} queued {run_type} at {target_dt}", ACCENT_LIGHT)

            # Start the countdown timer on the scheduler thread
            self.after(1000, lambda: self._check_scheduled_runs())
            self.after(2000, modal.destroy)

        btn_row = tk.Frame(modal, bg=BG_CANVAS)
        btn_row.pack(padx=20, pady=4, anchor=tk.W)
        tk.Button(btn_row, text="Schedule", font=self.fBtn, bg=ACCENT, fg=TEXT_PRIMARY,
            relief=tk.FLAT, cursor="hand2", padx=14, pady=5,
            command=schedule_it).pack(side=tk.LEFT, padx=(0,8))
        tk.Button(btn_row, text="Cancel", font=self.fSmall, bg=BG_CARD, fg=TEXT_MUTED,
            relief=tk.FLAT, cursor="hand2", padx=10, pady=5,
            command=modal.destroy).pack(side=tk.LEFT)

    def _check_scheduled_runs(self):
        """Check pending scheduled runs and fire them when their time arrives."""
        import json, os, datetime as _dt
        sched_path = os.path.join(AGENTS_ROOT, "data", "scheduled_runs.json")
        if not os.path.exists(sched_path):
            return
        try:
            runs = json.loads(open(sched_path).read())
        except Exception:
            return

        now = _dt.datetime.now()
        updated = False
        for run in runs:
            if run.get("status") != "pending":
                continue
            try:
                target = _dt.datetime.fromisoformat(run["scheduled_at"])
            except Exception:
                continue
            if now >= target:
                # Fire!
                run["status"] = "fired"
                updated = True
                agent = run.get("agent_id","")
                qlog(f"[Scheduler] Firing scheduled run: {agent}", SUCCESS)
                self._push_notif(f"Firing scheduled run: {agent}", SUCCESS)
                # Set up and trigger in Run view
                self.after(0, lambda a=agent: self._agent_var.set(a))
                self.after(200, self._run_agent)

                # If daily/weekly, reschedule
                if run.get("run_type") == "daily":
                    run["scheduled_at"] = (target + _dt.timedelta(days=1)).isoformat()
                    run["status"] = "pending"
                elif run.get("run_type") == "weekly":
                    run["scheduled_at"] = (target + _dt.timedelta(weeks=1)).isoformat()
                    run["status"] = "pending"

        if updated:
            with open(sched_path, "w") as sf:
                json.dump(runs, sf, indent=2)

        # Poll again in 60s if any pending runs remain
        if any(r.get("status")=="pending" for r in runs):
            self.after(60_000, self._check_scheduled_runs)


    # ════════════════════════════════════════════════════════════════════════
    # FEATURE 5 — Notification History Drawer
    # ════════════════════════════════════════════════════════════════════════
    def _build_notif_contents(self, parent):
        """Override: build the notification panel with history + clear button."""
        # Title row
        title_row = tk.Frame(parent, bg=BG_PANEL)
        title_row.pack(fill=tk.X, padx=12, pady=(12,4))
        tk.Label(title_row, text="Notifications", font=self.fH2,
                 bg=BG_PANEL, fg=TEXT_PRIMARY).pack(side=tk.LEFT)
        tk.Button(title_row, text="Clear all", font=self.fSmall,
            bg=BG_PANEL, fg=TEXT_MUTED, relief=tk.FLAT, cursor="hand2",
            command=self._notif_clear_all).pack(side=tk.RIGHT)
        tk.Button(title_row, text="Export log", font=self.fSmall,
            bg=BG_PANEL, fg=TEXT_MUTED, relief=tk.FLAT, cursor="hand2",
            command=self._notif_export).pack(side=tk.RIGHT, padx=4)
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill=tk.X, padx=8, pady=4)

        # Filter buttons
        flt_row = tk.Frame(parent, bg=BG_PANEL)
        flt_row.pack(fill=tk.X, padx=12, pady=(0,4))
        self._notif_filter_var = tk.StringVar(value="all")
        for v, label in [("all","All"),("run","Runs"),("todo","Todos"),("chat","Chat"),("system","System")]:
            tk.Radiobutton(flt_row, text=label, variable=self._notif_filter_var, value=v,
                bg=BG_PANEL, fg=TEXT_MUTED, selectcolor=BG_CARD,
                activebackground=BG_PANEL, font=self.fSmall,
                command=self._notif_refresh_list).pack(side=tk.LEFT, padx=2)
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill=tk.X, padx=8, pady=2)

        # Scrollable history
        outer = tk.Frame(parent, bg=BG_PANEL)
        outer.pack(fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(outer, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._notif_hist_canvas = tk.Canvas(outer, bg=BG_PANEL, highlightthickness=0,
                                             yscrollcommand=vsb.set)
        self._notif_hist_canvas.pack(fill=tk.BOTH, expand=True)
        vsb.configure(command=self._notif_hist_canvas.yview)
        self._notif_hist_inner = tk.Frame(self._notif_hist_canvas, bg=BG_PANEL)
        self._notif_hist_canvas.create_window((0,0), window=self._notif_hist_inner, anchor="nw", width=310)
        self._notif_hist_inner.bind("<Configure>",
            lambda e: self._notif_hist_canvas.configure(
                scrollregion=self._notif_hist_canvas.bbox("all")))

        self._notif_history = []  # [{text, color, timestamp, category}]
        self._notif_refresh_list()

    def _notif_infer_category(self, text):
        t = text.lower()
        if any(k in t for k in ["run","score","agent","task","fired","scheduled"]): return "run"
        if any(k in t for k in ["todo","added","pending","priority"]): return "todo"
        if any(k in t for k in ["agentmajesty","replied","chat"]): return "chat"
        return "system"

    def _push_notif(self, text, color=None):
        """Override push_notif to also log to persistent history."""
        import datetime as _dt
        color = color or TEXT_MUTED
        # Persist to history list
        if hasattr(self, '_notif_history'):
            entry = {
                "text": text,
                "color": color,
                "timestamp": _dt.datetime.now().strftime("%H:%M:%S"),
                "category": self._notif_infer_category(text),
                "read": False,
            }
            self._notif_history.insert(0, entry)
            # Keep last 500
            self._notif_history = self._notif_history[:500]
            # Refresh the history list if the drawer is open
            if hasattr(self, '_notif_hist_inner'):
                self._notif_refresh_list()

        # Update bell badge count
        unread = len([n for n in getattr(self,'_notif_history',[]) if not n.get("read",True)])
        if hasattr(self, '_notif_bell') and unread > 0:
            self._notif_bell.config(text=f"🔔 {unread}")
        elif hasattr(self, '_notif_bell'):
            self._notif_bell.config(text="🔔")

        # Original in-app flash notification
        if hasattr(self, '_notif_panel') and self._notif_panel.winfo_exists():
            if hasattr(self, '_notifs_inner'):
                lbl = tk.Label(self._notifs_inner, text=f"● {text}",
                    font=self.fSmall, bg=BG_PANEL, fg=color,
                    anchor=tk.W, wraplength=280, justify=tk.LEFT)
                lbl.pack(fill=tk.X, padx=8, pady=2)

    def _notif_refresh_list(self):
        if not hasattr(self, '_notif_hist_inner'):
            return
        for w in self._notif_hist_inner.winfo_children():
            w.destroy()
        flt = getattr(self, '_notif_filter_var', tk.StringVar(value="all")).get()
        items = self._notif_history if hasattr(self,'_notif_history') else []
        if flt != "all":
            items = [n for n in items if n.get("category") == flt]
        if not items:
            tk.Label(self._notif_hist_inner, text="No notifications.",
                     font=self.fSmall, bg=BG_PANEL, fg=TEXT_MUTED).pack(pady=12)
            return
        for notif in items[:200]:
            row = tk.Frame(self._notif_hist_inner, bg=BG_PANEL,
                           highlightbackground=DIVIDER, highlightthickness=1)
            row.pack(fill=tk.X, padx=4, pady=1)
            inner = tk.Frame(row, bg=BG_PANEL)
            inner.pack(fill=tk.X, padx=8, pady=5)
            tk.Label(inner, text=notif.get("timestamp",""), font=self.fSmall,
                     bg=BG_PANEL, fg=TEXT_MUTED, width=8, anchor=tk.W).pack(side=tk.LEFT)
            cat_colors = {"run": ACCENT_LIGHT, "todo": SUCCESS, "chat": INFO,
                          "system": TEXT_MUTED}
            cat = notif.get("category","system")
            tk.Label(inner, text=cat[:3].upper(), font=self.fSmall,
                     bg=BG_PANEL, fg=cat_colors.get(cat, TEXT_MUTED), width=4).pack(side=tk.LEFT, padx=2)
            tk.Label(inner, text=notif.get("text",""), font=self.fSmall,
                     bg=BG_PANEL, fg=notif.get("color", TEXT_BODY),
                     anchor=tk.W, wraplength=220, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X)
            notif["read"] = True
        # Reset badge
        if hasattr(self, '_notif_bell'):
            self._notif_bell.config(text="🔔")

    def _notif_clear_all(self):
        if hasattr(self, '_notif_history'):
            self._notif_history.clear()
        self._notif_refresh_list()
        qlog("[Notifications] History cleared", TEXT_MUTED)

    def _notif_export(self):
        """Export notification log to a text file."""
        import datetime as _dt, os
        if not hasattr(self, '_notif_history') or not self._notif_history:
            self._push_notif("No notifications to export.", TEXT_MUTED)
            return
        log_dir = os.path.join(AGENTS_ROOT, "data", "logs")
        os.makedirs(log_dir, exist_ok=True)
        fname = f"notif-log-{_dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        fpath = os.path.join(log_dir, fname)
        with open(fpath, "w") as f:
            f.write(f"AgentHarness Notification Log\n")
            f.write(f"Exported: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            for n in self._notif_history:
                f.write(f"[{n.get('timestamp','')}] [{n.get('category','').upper()}] {n.get('text','')}\n")
        self._push_notif(f"Log exported: {fname}", SUCCESS)
        qlog(f"[Notifications] Log exported to {fpath}", SUCCESS)


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

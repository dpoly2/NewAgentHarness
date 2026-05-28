"""
AgentHarness v2 — Desktop GUI
Tkinter-based app wrapping the full LangGraph reflexion engine.
Run: python app/main.py  (from inside .agents/agentharness/)
"""

import sys
import os
import threading
import queue
import json
import uuid
from datetime import datetime
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────────
HERE   = Path(__file__).parent.parent          # .agents/agentharness/
PARENT = HERE.parent                            # .agents/
if str(PARENT) not in sys.path:
    sys.path.append(str(PARENT))
if str(HERE.parent.parent) not in sys.path:
    sys.path.append(str(HERE.parent.parent))    # /app

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font as tkfont

# ── Colour palette ──────────────────────────────────────────────────────────
BG          = "#0f1117"   # near-black background
PANEL       = "#1a1d27"   # card / panel background
BORDER      = "#2a2d3e"   # subtle border
ACCENT      = "#5b5ff5"   # blue-violet primary
ACCENT2     = "#7c3aed"   # purple secondary
SUCCESS     = "#22c55e"   # green
WARNING     = "#f59e0b"   # amber
ERROR       = "#ef4444"   # red
TEXT        = "#e2e8f0"   # main text
TEXT_DIM    = "#64748b"   # muted text
HIGHLIGHT   = "#1e2235"   # selected / hover bg

NODE_COLORS = {
    "load_memory":  "#0ea5e9",   # sky blue
    "act":          "#8b5cf6",   # violet
    "evaluate":     "#f59e0b",   # amber
    "revise":       "#ef4444",   # red
    "save_memory":  "#22c55e",   # green
    "plan":         "#06b6d4",   # cyan
    "search":       "#3b82f6",   # blue
    "synthesize":   "#a855f7",   # purple
    "wp_plan":      "#06b6d4",
    "wp_implement": "#8b5cf6",
    "wp_verify":    "#22c55e",
    "END":          "#475569",   # slate
}

# ── Known agents ─────────────────────────────────────────────────────────────
AGENTS = [
    # XFTC
    "xftc-project-lead",
    "xftc-plugin-dev",
    "xftc-frontend-dev",
    "xftc-payments-agent",
    "xftc-qa-agent",
    # Grants / YEPC
    "grants-research-agent",
    "grant-writer-agent",
    "yepc-grant-writer-agent",
    "yepc-real-estate-research-agent",
    # S2T / Web
    "web-dev-agent",
    "s2t-project-lead",
    # SmithCap Finance
    "finance-cfo",
    "finance-advisor",
    "finance-tax-strategist",
    # Ministry
    "ministry-project-lead",
    "ministry-sermon-writer",
    # Social Media
    "social-media-project-lead",
    "social-content-agent",
    # Solar
    "solar-project-lead",
    "solar-marketing-agent",
    # Sigma Signal
    "sigma-signal-editor",
    "sigma-signal-historian",
]

GRAPHS = ["reflexion", "research", "wordpress"]
PROJECTS = [
    "xftc", "yepc", "pbs-foundation", "s2tdesigns",
    "smithcap", "smithcap-finance", "ministry",
    "social-media", "solar-repair", "sigma-signal",
    "nutrue", "the-elevation", "travel",
]


# ════════════════════════════════════════════════════════════════════════════
# Log queue — background thread writes here, UI polls it
# ════════════════════════════════════════════════════════════════════════════
log_queue: queue.Queue = queue.Queue()

def q(msg: str, color: str = TEXT, bold: bool = False):
    """Push a log line onto the queue."""
    log_queue.put({"text": msg, "color": color, "bold": bold})


# ════════════════════════════════════════════════════════════════════════════
# Monkey-patch print so LangGraph node prints appear in the GUI log
# ════════════════════════════════════════════════════════════════════════════
_original_print = print

def _patched_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    _original_print(msg, **kwargs)  # still goes to terminal

    # Route node-specific prints to colored log entries
    color = TEXT_DIM
    if "[ActNode]"       in msg: color = NODE_COLORS["act"]
    elif "[EvaluateNode]" in msg: color = NODE_COLORS["evaluate"]
    elif "[MemoryNode]"   in msg: color = NODE_COLORS["load_memory"]
    elif "REVISE"         in msg: color = NODE_COLORS["revise"]
    elif "SAVE"           in msg: color = NODE_COLORS["save_memory"]
    elif "[ResearchGraph" in msg: color = NODE_COLORS["search"]
    elif "[WPGraph"       in msg: color = NODE_COLORS["wp_plan"]
    elif "REFLEXION RUN"  in msg: color = ACCENT
    elif "COMPLETE"       in msg: color = SUCCESS
    elif "ERROR"          in msg: color = ERROR

    log_queue.put({"text": msg, "color": color, "bold": False})

import builtins
builtins.print = _patched_print


# ════════════════════════════════════════════════════════════════════════════
# Run history store (in-memory + JSON)
# ════════════════════════════════════════════════════════════════════════════
HISTORY_FILE = HERE / "memory" / "run_history.json"

def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            pass
    return []

def save_history(history: list):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


# ════════════════════════════════════════════════════════════════════════════
# Main Application
# ════════════════════════════════════════════════════════════════════════════
class AgentHarnessApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("AgentHarness v2")
        self.geometry("1280x820")
        self.minsize(900, 600)
        self.configure(bg=BG)

        self._running   = False
        self._run_thread = None
        self.history    = load_history()
        self._setup_fonts()
        self._build_ui()
        self._poll_log()

    # ── Fonts ────────────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.f_heading  = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.f_label    = tkfont.Font(family="Segoe UI", size=10)
        self.f_mono     = tkfont.Font(family="Consolas",  size=10)
        self.f_mono_sm  = tkfont.Font(family="Consolas",  size=9)
        self.f_btn      = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.f_score    = tkfont.Font(family="Segoe UI", size=22, weight="bold")

    # ── Top-level layout ─────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header bar ──
        header = tk.Frame(self, bg=PANEL, height=54)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(header, text="⬡  AgentHarness", font=self.f_heading,
                 bg=PANEL, fg=ACCENT).pack(side=tk.LEFT, padx=18, pady=12)
        tk.Label(header, text="v2  ·  LangGraph Reflexion Engine",
                 font=self.f_label, bg=PANEL, fg=TEXT_DIM).pack(side=tk.LEFT, pady=12)

        self._api_status_lbl = tk.Label(header, text="● API: checking…",
                                        font=self.f_label, bg=PANEL, fg=WARNING)
        self._api_status_lbl.pack(side=tk.RIGHT, padx=18)
        self.after(200, self._check_api_key)

        # ── Main paned window ──
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               bg=BG, sashwidth=4, sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Left panel: controls
        left = tk.Frame(paned, bg=PANEL, width=340)
        left.pack_propagate(False)
        paned.add(left, minsize=280)
        self._build_controls(left)

        # Right panel: tabs (log + output + history)
        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=400)
        self._build_right(right)

    # ── Controls panel ───────────────────────────────────────────────────────
    def _build_controls(self, parent):
        # Section helper
        def section(p, title):
            tk.Label(p, text=title.upper(), font=tkfont.Font(family="Segoe UI", size=8, weight="bold"),
                     bg=PANEL, fg=TEXT_DIM).pack(anchor=tk.W, padx=16, pady=(14, 2))

        # ── Graph selector ──
        section(parent, "Graph Type")
        self._graph_var = tk.StringVar(value="reflexion")
        graph_frame = tk.Frame(parent, bg=PANEL)
        graph_frame.pack(fill=tk.X, padx=14, pady=(0, 8))
        for g in GRAPHS:
            rb = tk.Radiobutton(graph_frame, text=g.capitalize(), variable=self._graph_var,
                                value=g, bg=PANEL, fg=TEXT, selectcolor=ACCENT,
                                activebackground=PANEL, activeforeground=TEXT,
                                font=self.f_label, cursor="hand2")
            rb.pack(side=tk.LEFT, padx=(0, 10))

        # ── Agent ──
        section(parent, "Agent")
        self._agent_var = tk.StringVar(value=AGENTS[0])
        agent_combo = ttk.Combobox(parent, textvariable=self._agent_var,
                                   values=AGENTS, state="readonly", font=self.f_label)
        agent_combo.pack(fill=tk.X, padx=14, pady=(0, 8))
        self._style_combo(agent_combo)

        # ── Project ──
        section(parent, "Project")
        self._project_var = tk.StringVar(value=PROJECTS[0])
        proj_combo = ttk.Combobox(parent, textvariable=self._project_var,
                                  values=PROJECTS, state="readonly", font=self.f_label)
        proj_combo.pack(fill=tk.X, padx=14, pady=(0, 8))
        self._style_combo(proj_combo)

        # ── Task ──
        section(parent, "Task")
        self._task_text = tk.Text(parent, height=6, font=self.f_mono_sm,
                                  bg=HIGHLIGHT, fg=TEXT, insertbackground=TEXT,
                                  relief=tk.FLAT, padx=8, pady=6,
                                  wrap=tk.WORD)
        self._task_text.pack(fill=tk.X, padx=14, pady=(0, 4))
        self._task_text.insert("1.0", "Describe the task for this agent…")
        self._task_text.bind("<FocusIn>",  self._task_placeholder_clear)
        self._task_text.bind("<FocusOut>", self._task_placeholder_restore)

        # ── Max revisions ──
        rev_row = tk.Frame(parent, bg=PANEL)
        rev_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(rev_row, text="Max revisions:", font=self.f_label,
                 bg=PANEL, fg=TEXT_DIM).pack(side=tk.LEFT)
        self._max_rev_var = tk.IntVar(value=3)
        for n in [1, 2, 3]:
            tk.Radiobutton(rev_row, text=str(n), variable=self._max_rev_var,
                           value=n, bg=PANEL, fg=TEXT, selectcolor=ACCENT,
                           activebackground=PANEL, font=self.f_label,
                           cursor="hand2").pack(side=tk.LEFT, padx=6)

        # ── Run button ──
        self._run_btn = tk.Button(parent, text="▶  RUN AGENT",
                                  font=self.f_btn, bg=ACCENT, fg="white",
                                  relief=tk.FLAT, padx=12, pady=10,
                                  cursor="hand2", command=self._start_run,
                                  activebackground=ACCENT2, activeforeground="white")
        self._run_btn.pack(fill=tk.X, padx=14, pady=(6, 4))

        self._stop_btn = tk.Button(parent, text="■  STOP",
                                   font=self.f_btn, bg=BORDER, fg=TEXT_DIM,
                                   relief=tk.FLAT, padx=12, pady=8,
                                   cursor="hand2", command=self._stop_run,
                                   state=tk.DISABLED)
        self._stop_btn.pack(fill=tk.X, padx=14, pady=(0, 8))

        # ── Score card ──
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X, padx=14, pady=4)
        section(parent, "Last Run Score")
        score_frame = tk.Frame(parent, bg=PANEL)
        score_frame.pack(fill=tk.X, padx=14, pady=(0, 4))

        self._score_lbl = tk.Label(score_frame, text="—",
                                   font=self.f_score, bg=PANEL, fg=TEXT_DIM)
        self._score_lbl.pack(side=tk.LEFT)

        meta_frame = tk.Frame(score_frame, bg=PANEL)
        meta_frame.pack(side=tk.LEFT, padx=12)
        self._rev_lbl  = tk.Label(meta_frame, text="revisions: —",
                                  font=self.f_label, bg=PANEL, fg=TEXT_DIM)
        self._rev_lbl.pack(anchor=tk.W)
        self._time_lbl = tk.Label(meta_frame, text="run id: —",
                                  font=self.f_label, bg=PANEL, fg=TEXT_DIM)
        self._time_lbl.pack(anchor=tk.W)

        # ── Skill version ──
        section(parent, "Skill Version")
        self._skill_lbl = tk.Label(parent, text="—",
                                   font=self.f_label, bg=PANEL, fg=TEXT_DIM)
        self._skill_lbl.pack(anchor=tk.W, padx=16, pady=(0, 12))

    # ── Right panel (tabs) ───────────────────────────────────────────────────
    def _build_right(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.TNotebook",         background=BG, borderwidth=0)
        style.configure("Custom.TNotebook.Tab",     background=PANEL, foreground=TEXT_DIM,
                        padding=[14, 6], font=("Segoe UI", 10))
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", BG)],
                  foreground=[("selected", TEXT)])

        self._notebook = ttk.Notebook(parent, style="Custom.TNotebook")
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Tab 1 — Execution Log
        log_frame = tk.Frame(self._notebook, bg=BG)
        self._notebook.add(log_frame, text="  Execution Log  ")
        self._log_text = scrolledtext.ScrolledText(
            log_frame, font=self.f_mono_sm, bg=BG, fg=TEXT,
            insertbackground=TEXT, relief=tk.FLAT,
            padx=12, pady=8, state=tk.DISABLED, wrap=tk.WORD
        )
        self._log_text.pack(fill=tk.BOTH, expand=True)

        # Configure color tags
        for name, color in NODE_COLORS.items():
            self._log_text.tag_config(name, foreground=color)
        self._log_text.tag_config("default",  foreground=TEXT)
        self._log_text.tag_config("dim",      foreground=TEXT_DIM)
        self._log_text.tag_config("success",  foreground=SUCCESS)
        self._log_text.tag_config("error",    foreground=ERROR)
        self._log_text.tag_config("warning",  foreground=WARNING)
        self._log_text.tag_config("accent",   foreground=ACCENT)
        self._log_text.tag_config("bold",     font=tkfont.Font(family="Consolas", size=10, weight="bold"))

        # Log toolbar
        log_toolbar = tk.Frame(log_frame, bg=PANEL)
        log_toolbar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(log_toolbar, text="Clear Log", font=self.f_label,
                  bg=PANEL, fg=TEXT_DIM, relief=tk.FLAT, cursor="hand2",
                  command=self._clear_log).pack(side=tk.RIGHT, padx=8, pady=4)

        # Tab 2 — Output
        out_frame = tk.Frame(self._notebook, bg=BG)
        self._notebook.add(out_frame, text="  Output  ")
        self._output_text = scrolledtext.ScrolledText(
            out_frame, font=self.f_mono, bg=BG, fg=TEXT,
            insertbackground=TEXT, relief=tk.FLAT,
            padx=14, pady=10, state=tk.DISABLED, wrap=tk.WORD
        )
        self._output_text.pack(fill=tk.BOTH, expand=True)

        out_toolbar = tk.Frame(out_frame, bg=PANEL)
        out_toolbar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Button(out_toolbar, text="Copy Output", font=self.f_label,
                  bg=PANEL, fg=TEXT_DIM, relief=tk.FLAT, cursor="hand2",
                  command=self._copy_output).pack(side=tk.RIGHT, padx=8, pady=4)

        # Tab 3 — Run History
        hist_frame = tk.Frame(self._notebook, bg=BG)
        self._notebook.add(hist_frame, text="  History  ")
        self._build_history_tab(hist_frame)

        # Tab 4 — Skill Viewer
        skill_frame = tk.Frame(self._notebook, bg=BG)
        self._notebook.add(skill_frame, text="  Skill Files  ")
        self._build_skill_tab(skill_frame)

    # ── History tab ──────────────────────────────────────────────────────────
    def _build_history_tab(self, parent):
        cols = ("run_id", "agent", "project", "score", "revisions", "time")
        self._hist_tree = ttk.Treeview(parent, columns=cols, show="headings",
                                       selectmode="browse")
        style = ttk.Style()
        style.configure("Treeview",
                        background=PANEL, foreground=TEXT,
                        fieldbackground=PANEL, rowheight=26,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=BORDER, foreground=TEXT_DIM,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", HIGHLIGHT)])

        widths = {"run_id": 80, "agent": 200, "project": 100,
                  "score": 70, "revisions": 80, "time": 150}
        for col in cols:
            self._hist_tree.heading(col, text=col.replace("_", " ").title())
            self._hist_tree.column(col, width=widths.get(col, 100), anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                  command=self._hist_tree.yview)
        self._hist_tree.configure(yscrollcommand=scrollbar.set)
        self._hist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._hist_tree.bind("<<TreeviewSelect>>", self._on_history_select)
        self._refresh_history_tree()

    # ── Skill tab ─────────────────────────────────────────────────────────────
    def _build_skill_tab(self, parent):
        top = tk.Frame(parent, bg=PANEL)
        top.pack(fill=tk.X)
        tk.Label(top, text="Agent:", font=self.f_label,
                 bg=PANEL, fg=TEXT_DIM).pack(side=tk.LEFT, padx=10, pady=6)
        self._skill_agent_var = tk.StringVar(value=AGENTS[0])
        sk_combo = ttk.Combobox(top, textvariable=self._skill_agent_var,
                                values=AGENTS, state="readonly",
                                font=self.f_label, width=30)
        sk_combo.pack(side=tk.LEFT, padx=4)
        self._style_combo(sk_combo)
        tk.Button(top, text="Load Skill", font=self.f_label,
                  bg=ACCENT, fg="white", relief=tk.FLAT, cursor="hand2",
                  command=self._load_skill_view).pack(side=tk.LEFT, padx=8)

        self._skill_text = scrolledtext.ScrolledText(
            parent, font=self.f_mono_sm, bg=BG, fg=TEXT,
            insertbackground=TEXT, relief=tk.FLAT, padx=12, pady=8,
            wrap=tk.WORD
        )
        self._skill_text.pack(fill=tk.BOTH, expand=True)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _style_combo(self, combo):
        style = ttk.Style()
        style.configure("TCombobox",
                        fieldbackground=HIGHLIGHT, background=HIGHLIGHT,
                        foreground=TEXT, selectbackground=ACCENT,
                        selectforeground="white")

    def _task_placeholder_clear(self, _):
        if self._task_text.get("1.0", tk.END).strip() == "Describe the task for this agent…":
            self._task_text.delete("1.0", tk.END)
            self._task_text.config(fg=TEXT)

    def _task_placeholder_restore(self, _):
        if not self._task_text.get("1.0", tk.END).strip():
            self._task_text.insert("1.0", "Describe the task for this agent…")
            self._task_text.config(fg=TEXT_DIM)

    def _check_api_key(self):
        key = os.environ.get("OPENAI_API_KEY", "")
        env_file = HERE / ".env"
        if not key and env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
                    key = os.environ["OPENAI_API_KEY"]
        if key:
            self._api_status_lbl.config(text="● API: connected", fg=SUCCESS)
        else:
            self._api_status_lbl.config(text="● API: key missing", fg=ERROR)

    # ── Log polling ──────────────────────────────────────────────────────────
    def _poll_log(self):
        try:
            while True:
                item = log_queue.get_nowait()
                self._append_log(item["text"], item["color"], item.get("bold", False))
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    def _append_log(self, text: str, color: str = TEXT, bold: bool = False):
        self._log_text.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.insert(tk.END, f"[{ts}] ", "dim")
        tag = "default"
        # Map color string back to a named tag
        color_to_tag = {v: k for k, v in NODE_COLORS.items()}
        color_to_tag.update({
            SUCCESS: "success", ERROR: "error",
            WARNING: "warning", ACCENT: "accent", TEXT_DIM: "dim"
        })
        tag = color_to_tag.get(color, "default")
        self._log_text.insert(tk.END, text + "\n", tag)
        self._log_text.config(state=tk.DISABLED)
        self._log_text.see(tk.END)

    def _clear_log(self):
        self._log_text.config(state=tk.NORMAL)
        self._log_text.delete("1.0", tk.END)
        self._log_text.config(state=tk.DISABLED)

    # ── Run agent ────────────────────────────────────────────────────────────
    def _start_run(self):
        task = self._task_text.get("1.0", tk.END).strip()
        if not task or task == "Describe the task for this agent…":
            messagebox.showwarning("No Task", "Please enter a task before running.")
            return
        if not os.environ.get("OPENAI_API_KEY"):
            messagebox.showerror("API Key Missing",
                                 "Set OPENAI_API_KEY before running.\n\n"
                                 "Create a .env file in .agents/agentharness/ with:\n"
                                 "OPENAI_API_KEY=sk-...")
            return
        if self._running:
            return

        self._running = True
        self._run_btn.config(state=tk.DISABLED, bg=BORDER, text="⏳  Running…")
        self._stop_btn.config(state=tk.NORMAL)
        self._notebook.select(0)

        agent   = self._agent_var.get()
        project = self._project_var.get()
        graph   = self._graph_var.get()
        max_rev = self._max_rev_var.get()

        q(f"{'='*56}", BORDER)
        q(f"  AGENT:   {agent}", ACCENT, bold=True)
        q(f"  PROJECT: {project}")
        q(f"  GRAPH:   {graph.upper()}")
        q(f"  TASK:    {task[:80]}{'…' if len(task)>80 else ''}")
        q(f"{'='*56}", BORDER)

        self._run_thread = threading.Thread(
            target=self._run_agent_thread,
            args=(agent, project, task, graph, max_rev),
            daemon=True,
        )
        self._run_thread.start()

    def _run_agent_thread(self, agent, project, task, graph, max_rev):
        try:
            from agentharness.adapters.local_adapter import LocalAdapter
            adapter = LocalAdapter()

            # Patch max_revisions into default_state
            from agentharness.state.agent_state import default_state

            if graph == "reflexion":
                from agentharness.graphs.reflexion_loop import build_reflexion_graph
                compiled = build_reflexion_graph(adapter)
                state = default_state(agent, project, task, "local")
                state["max_revisions"] = max_rev
                result = compiled.invoke(state)

            elif graph == "research":
                from agentharness.graphs.research_graph import build_research_graph
                compiled = build_research_graph(adapter)
                state = default_state(agent, project, task, "local")
                state["max_revisions"] = max_rev
                result = compiled.invoke(state)

            elif graph == "wordpress":
                from agentharness.graphs.wordpress_graph import build_wordpress_graph
                compiled = build_wordpress_graph(adapter)
                state = default_state(agent, project, task, "local")
                state["max_revisions"] = max_rev
                result = compiled.invoke(state)

            else:
                result = {"output": "Unknown graph type.", "score": 0.0,
                          "revision_count": 0, "run_id": "?", "skill_version": 1}

            self.after(0, self._on_run_complete, result)

        except Exception as e:
            import traceback
            q(f"ERROR: {e}", ERROR)
            q(traceback.format_exc(), ERROR)
            self.after(0, self._on_run_error, str(e))

    def _on_run_complete(self, result):
        self._running = False
        self._run_btn.config(state=tk.NORMAL, bg=ACCENT, text="▶  RUN AGENT")
        self._stop_btn.config(state=tk.DISABLED)

        score    = result.get("score", 0.0)
        revs     = result.get("revision_count", 0)
        run_id   = result.get("run_id", "?")
        skill_v  = result.get("skill_version", 1)
        output   = result.get("output", "")

        # Score label colour
        s_color = SUCCESS if score >= 0.75 else WARNING if score >= 0.5 else ERROR
        self._score_lbl.config(text=f"{score:.2f}", fg=s_color)
        self._rev_lbl.config(text=f"revisions: {revs}")
        self._time_lbl.config(text=f"run id: {run_id}")
        self._skill_lbl.config(text=f"skill v{skill_v}  ·  agent: {self._agent_var.get()}")

        # Write output tab
        self._output_text.config(state=tk.NORMAL)
        self._output_text.delete("1.0", tk.END)
        self._output_text.insert("1.0", output)
        self._output_text.config(state=tk.DISABLED)

        # Switch to output tab
        self._notebook.select(1)

        # Log summary
        q(f"{'='*56}", BORDER)
        q(f"  DONE — score: {score:.2f}  revisions: {revs}  run: {run_id}", SUCCESS, bold=True)
        q(f"{'='*56}", BORDER)

        # Save to history
        self.history.append({
            "run_id":    run_id,
            "agent":     self._agent_var.get(),
            "project":   self._project_var.get(),
            "graph":     self._graph_var.get(),
            "task":      self._task_text.get("1.0", tk.END).strip()[:120],
            "score":     score,
            "revisions": revs,
            "skill_v":   skill_v,
            "output":    output[:500],
            "time":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        save_history(self.history)
        self._refresh_history_tree()

    def _on_run_error(self, error_msg: str):
        self._running = False
        self._run_btn.config(state=tk.NORMAL, bg=ACCENT, text="▶  RUN AGENT")
        self._stop_btn.config(state=tk.DISABLED)
        messagebox.showerror("Run Failed", f"Agent run failed:\n\n{error_msg}")

    def _stop_run(self):
        # Best-effort: we can't truly kill a thread but we flag it
        q("  ⚠ Stop requested — current node will finish then halt.", WARNING)
        self._running = False
        self._run_btn.config(state=tk.NORMAL, bg=ACCENT, text="▶  RUN AGENT")
        self._stop_btn.config(state=tk.DISABLED)

    # ── History interactions ─────────────────────────────────────────────────
    def _refresh_history_tree(self):
        for row in self._hist_tree.get_children():
            self._hist_tree.delete(row)
        for h in reversed(self.history[-100:]):
            score = h.get("score", 0)
            tag = "good" if score >= 0.75 else "warn" if score >= 0.5 else "bad"
            self._hist_tree.insert("", tk.END, values=(
                h.get("run_id", "?"),
                h.get("agent", "?"),
                h.get("project", "?"),
                f"{score:.2f}",
                h.get("revisions", 0),
                h.get("time", "?"),
            ), tags=(tag,))

        self._hist_tree.tag_configure("good", foreground=SUCCESS)
        self._hist_tree.tag_configure("warn", foreground=WARNING)
        self._hist_tree.tag_configure("bad",  foreground=ERROR)

    def _on_history_select(self, _):
        sel = self._hist_tree.selection()
        if not sel:
            return
        idx = self._hist_tree.index(sel[0])
        if idx < len(self.history):
            h = list(reversed(self.history[-100:]))[idx]
            self._output_text.config(state=tk.NORMAL)
            self._output_text.delete("1.0", tk.END)
            self._output_text.insert("1.0",
                f"── RUN: {h.get('run_id')} ─────────────────────────────\n"
                f"Agent:   {h.get('agent')}\n"
                f"Project: {h.get('project')}\n"
                f"Score:   {h.get('score', 0):.2f}   Revisions: {h.get('revisions')}\n"
                f"Time:    {h.get('time')}\n"
                f"Task:    {h.get('task')}\n"
                f"──────────────────────────────────────────────────\n\n"
                + h.get("output", "(output not stored)")
            )
            self._output_text.config(state=tk.DISABLED)
            self._notebook.select(1)

    # ── Skill viewer ─────────────────────────────────────────────────────────
    def _load_skill_view(self):
        agent_id   = self._skill_agent_var.get()
        skill_name = agent_id.replace("-", "_")
        SKILLS_DIR = HERE.parent / "skills"
        skill_file = SKILLS_DIR / f"{skill_name}.md"

        self._skill_text.config(state=tk.NORMAL)
        self._skill_text.delete("1.0", tk.END)

        if skill_file.exists():
            self._skill_text.insert("1.0", skill_file.read_text())
        else:
            self._skill_text.insert("1.0",
                f"No skill file found for '{agent_id}'.\n\n"
                f"Expected: {skill_file}\n\n"
                "Run this agent at least once — the Reflexion engine will\n"
                "create and evolve the skill file automatically."
            )

    # ── Copy output ──────────────────────────────────────────────────────────
    def _copy_output(self):
        text = self._output_text.get("1.0", tk.END).strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        q("Output copied to clipboard.", TEXT_DIM)


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = AgentHarnessApp()
    app.mainloop()

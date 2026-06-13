import sys, os
# Windows Unicode safety
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

from pathlib import Path
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
APP_ROOT = AGENTS_DIR.parent

for p in [str(HERE), str(AGENTS_DIR), str(APP_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv(AGENTS_DIR / ".env")

import getpass
import json
import queue
import socket
import subprocess
import threading
import uuid
import webbrowser
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

try:
    from hub_client import HubClient, LLM_TIMEOUT as _HUB_LLM_TIMEOUT
except Exception:
    HubClient = None
    _HUB_LLM_TIMEOUT = 180.0

import hub_db
from ah_logging import LOG_DIR
from hub_nodes import LANGGRAPH_OK, run_graph
from hub_scheduler import BUILT_IN_JOB_IDS, BUILT_IN_JOBS, TIMEZONE_NAME


BG_CANVAS   = "#0B0F17"
BG_RAIL     = "#080C13"
BG_PANEL    = "#111827"
BG_CARD     = "#0A1F44"
BG_INPUT    = "#0d1520"
BG_HOVER    = "#0e2444"
BG_SELECTED = "#0f2d57"
ACCENT      = "#00B8FF"
ACCENT_LIGHT= "#2DD4FF"
ACCENT_DARK = "#0090cc"
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
ERROR       = "#ef4444"
TEXT_PRIMARY= "#D9E3F0"
TEXT_BODY   = "#a0b4cc"
TEXT_MUTED  = "#4a6080"
DIVIDER     = "#0A1F44"
BORDER_CARD = "#0e2a55"

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
    "Markets":         ["markets-project-lead","markets-cio","markets-cro","markets-options-strategist","markets-quant","markets-intelligence-desk","markets-equity-analyst","markets-macro-analyst","markets-tactical-alpha","markets-technical-analyst"],
    "Nutrue":          ["nutrue-project-lead","nutrue-brand-agent","nutrue-ecommerce-agent","nutrue-finance-agent","nutrue-inbro-retrofit-agent","nutrue-legal-agent","nutrue-marketing-agent"],
    "Night King":      ["nightking-project-lead","nightking-brand-agent","nightking-design-agent","nightking-media-agent"],
    "PBS Foundation":  ["pbs-project-lead","pbs-board-agent","pbs-communications-agent","pbs-fundraising-agent","pbs-legal-agent","pbs-programs-agent"],
    "Elevation":       ["elevation-project-lead","elevation-brand-agent","elevation-events-agent","elevation-funding-agent","elevation-legal-agent","elevation-marketing-agent"],
}

PROJECTS = ["xftc","yepc","pbs-foundation","s2tdesigns","smithcap","smithcap-finance",
            "ministry","business-law","social-media","solar-repair","sigma-signal",
            "nutrue","the-elevation","travel","holdings","markets","nightking"]

NC = {
    "load_memory": "#00bcf2", "act": "#8b5cf6", "evaluate": "#f8b400",
    "revise": "#e74856", "save_memory": "#92c353", "plan": "#06b6d4",
    "search": "#3b82f6", "synthesize": "#a855f7", "wp_plan": "#06b6d4",
    "wp_implement": "#8b5cf6", "wp_verify": "#92c353", "legal_analyze": "#f97316",
    "legal_draft": "#ec4899", "legal_review": "#14b8a6", "END": "#475569"
}

TEAM_EMOJI = {
    "Business Law": "⚖️",
    "XFTC": "🏃",
    "Grants / YEPC": "🧾",
    "S2T Designs": "🎨",
    "SmithCap Finance": "💼",
    "Ministry": "✝️",
    "Social Media": "📣",
    "Solar": "☀️",
    "Sigma Signal": "📡",
    "Holdings": "🏢",
    "Markets": "📈",
    "Nutrue": "🧬",
    "Night King": "🌙",
    "PBS Foundation": "🏛️",
    "Elevation": "⛰️",
}

GRAPH_NAMES = ["reflexion", "research", "wordpress", "business-law"]
STATUS_COLORS = {
    "running": ACCENT,
    "queued": WARNING,
    "complete": SUCCESS,
    "completed": SUCCESS,
    "done": SUCCESS,
    "pending": TEXT_BODY,
    "in_progress": ACCENT_LIGHT,
    "failed": ERROR,
    "cancelled": ERROR,
    "offline": ERROR,
    "online": SUCCESS,
    "active": SUCCESS,
    "paused": WARNING,
}
PRIORITY_COLORS = {
    "urgent": ERROR,
    "high": WARNING,
    "medium": ACCENT,
    "normal": ACCENT,
    "low": SUCCESS,
}
NAV_ITEMS = [
    ("🏠", "Home",     "show_home"),
    ("▶",  "Runs",     "show_runs"),
    ("✓",  "Todos",    "show_todos"),
    ("📰", "Digest",   "show_digest"),
    ("📊", "Reports",  "show_reports"),
    ("📅", "Schedule", "show_schedule"),
    ("👥", "Clients",  "show_clients"),
    ("✈",  "Travel",   "show_travel"),
    ("📈", "Markets",  "show_markets"),
    ("🏢", "Org",      "show_org"),
    ("⚡", "Connect",  "show_connectors"),
    ("👑", "Inez",     "show_inez"),
    ("🔑", "Admin",    "show_admin"),
]
GRAPH_LAYOUTS = {
    "reflexion": ["load_memory", "act", "evaluate", "revise", "save_memory", "END"],
    "research": ["plan", "search", "synthesize", "save_memory", "END"],
    "wordpress": ["wp_plan", "wp_implement", "wp_verify", "save_memory", "END"],
    "business-law": ["legal_analyze", "legal_draft", "legal_review", "save_memory", "END"],
}


class LocalHubClient:
    def __init__(self):
        self.online = False
        self._events = queue.Queue()

    def start(self):
        return None

    def stop(self):
        return None

    def poll_events(self):
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                break
        return events

    def get_health(self):
        return {"status": "offline", "mode": "local"}

    def submit_run(self, **kwargs):
        return None

    def post_json(self, path, data):
        return None

    def list_runs(self, limit=100, agent_id=None, project=None, status=None):
        return hub_db.load_runs(limit=limit, agent_id=agent_id, project=project, status=status)

    def cancel_run(self, run_id):
        return False

    def run_stats(self):
        return hub_db.agent_stats()

    def list_todos(self, status=None, project=None):
        return hub_db.list_todos(status=status, project=project)

    def create_todo(self, title, description="", priority="medium", project="", due_date="", tags=None):
        return hub_db.create_todo(title=title, description=description, priority=priority, project=project, due_date=due_date, tags=tags or [])

    def update_todo(self, id, **kwargs):
        return hub_db.update_todo(id, **kwargs)

    def delete_todo(self, id):
        return hub_db.delete_todo(id)

    def list_trips(self):
        return hub_db.list_trips()

    def create_trip(self, name, destination, depart_date="", return_date="", status="planning", budget=0, notes=""):
        return hub_db.create_trip(name=name, destination=destination, depart_date=depart_date, return_date=return_date, status=status, budget=budget, notes=notes)

    def update_trip(self, id, **kwargs):
        return hub_db.update_trip(id, **kwargs)

    def delete_trip(self, id):
        return hub_db.delete_trip(id)

    def list_connectors(self):
        return hub_db.list_connectors()

    def create_connector(self, data):
        return hub_db.create_connector(
            label=data.get("label", ""),
            email_address=data.get("email_address", ""),
            provider=data.get("provider", "imap"),
            imap_host=data.get("imap_host"),
            imap_port=int(data.get("imap_port") or 993),
            smtp_host=data.get("smtp_host"),
            smtp_port=int(data.get("smtp_port") or 587),
            username=data.get("username"),
            credentials={"password": data.get("password", "")},
        )

    def update_connector(self, id, **kwargs):
        return hub_db.update_connector(id, **kwargs)

    def delete_connector(self, id):
        return hub_db.delete_connector(id)

    def test_connector(self, id):
        return None

    def list_notifications(self, unread_only=False):
        return hub_db.list_notifications(unread_only=unread_only)

    def clear_notifications(self):
        hub_db.clear_notifications()

    def list_scheduler_jobs(self):
        return hub_db.list_scheduled_jobs()

    def trigger_job(self, id):
        return False

    def get_briefing(self):
        return hub_db.get_briefing_cache()

    def get_config(self):
        data = hub_db.get_config()
        return data if isinstance(data, dict) else {}

    def update_config(self, data):
        hub_db.update_config(data)
        return True

    def list_projects(self):
        return hub_db.list_projects()

    def create_project(self, data):
        return hub_db.create_project(**data)

    def list_clients(self):
        return hub_db.list_clients()

    def create_client(self, data):
        return hub_db.create_client(**data)

    def list_users(self):
        return hub_db.list_users()


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 54
        y = self.widget.winfo_rooty() + 12
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=self.text,
            bg=BG_PANEL,
            fg=TEXT_PRIMARY,
            bd=1,
            relief="solid",
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
        )
        label.pack()

    def hide(self, _event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ArchonHubApp:
    def __init__(self):
        hub_db.init_schema()
        self.root = tk.Tk()
        self.root.title("ArchonHub")
        self.root.geometry("1400x900")
        self.root.configure(bg=BG_CANVAS)
        self.root.minsize(1200, 780)

        # Branding — set window icon from branding/desktop/app-icon.ico
        _BRANDING_DIR = APP_ROOT / "branding"
        _ico = _BRANDING_DIR / "desktop" / "app-icon.ico"
        if _ico.exists():
            try:
                self.root.iconbitmap(str(_ico))
            except Exception:
                pass

        self.username = getpass.getuser()
        self._ui_queue = queue.Queue()
        self.run_logs = {}
        self.run_state = {}
        self.local_run_configs = {}
        self.cancel_flags = {}
        self.nav_buttons = {}
        self.current_view = ""
        self.selected_run_id = None
        self.selected_todo_id = None
        self.selected_job_id = None
        self.selected_connector_id = None
        self._connector_selected_id = None
        self._connector_lookup = {}
        self.selected_user_id = None
        self.admin_unlocked = False
        self.hub_process = None
        self.toast_label = None
        self._markets_tab = None   # MarketsTab instance (if live feed is running)

        # Chat state
        self._chat_messages = []          # list of {role, content, agent_id, run_id, ts}
        self._chat_run_frames = {}        # run_id -> thinking_frame widget
        self._chat_run_step_labels = {}   # run_id -> list of step label widgets
        self._chat_run_status_label = {}  # run_id -> status label widget
        self._chat_dot_state = {}         # run_id -> int (animation tick)
        self._chat_canvas = None          # scrollable canvas for bubbles
        self._chat_bubbles_frame = None   # inner frame holding all bubbles

        # Inez state
        self._inez_history = []           # list of {role, content} for LLM context
        self._inez_conv_id = None         # current conversation_id (for Hub persistence)

        self.quick_team_var = tk.StringVar(value=list(AGENT_REGISTRY.keys())[0])
        self.quick_agent_var = tk.StringVar(value=AGENT_REGISTRY[self.quick_team_var.get()][0])
        self.quick_project_var = tk.StringVar(value=PROJECTS[0])
        self.quick_graph_var = tk.StringVar(value="reflexion")
        self.quick_max_rev_var = tk.IntVar(value=2)
        self.run_filter_agent_var = tk.StringVar(value="all")
        self.run_filter_project_var = tk.StringVar(value="all")
        self.run_filter_status_var = tk.StringVar(value="all")
        self.todo_filter_status_var = tk.StringVar(value="all")
        self.todo_filter_project_var = tk.StringVar(value="all")
        self.digest_text_var = tk.StringVar(value="")
        self.log_file_var = tk.StringVar(value="")

        self._configure_styles()
        self._build_shell()

        hub_cls = HubClient if HubClient is not None else LocalHubClient
        try:
            self.hub = hub_cls()
        except Exception:
            self.hub = LocalHubClient()
        try:
            self.hub.start()
        except Exception:
            self.hub = LocalHubClient()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self._poll_queue)
        self.root.after(500, self._poll_hub_events)
        self.root.after(1000, self._update_clock)
        self.show_home()

    def _configure_styles(self):
        default_font = ("Segoe UI", 10) if sys.platform == "win32" else ("Arial", 10)
        self.root.option_add("*Font", default_font)
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure(".", background=BG_PANEL, foreground=TEXT_BODY, fieldbackground=BG_INPUT)
        self.style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_INPUT, foreground=TEXT_PRIMARY, arrowcolor=TEXT_BODY)
        self.style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)], foreground=[("readonly", TEXT_PRIMARY)])
        self.style.configure("Treeview", background=BG_PANEL, foreground=TEXT_BODY, fieldbackground=BG_PANEL, bordercolor=BORDER_CARD, rowheight=28)
        self.style.map("Treeview", background=[("selected", BG_SELECTED)], foreground=[("selected", TEXT_PRIMARY)])
        self.style.configure("Treeview.Heading", background=BG_CARD, foreground=TEXT_PRIMARY, relief="flat")
        self.style.configure("Vertical.TScrollbar", background=BG_PANEL, troughcolor=BG_CANVAS, bordercolor=BG_CANVAS, arrowcolor=TEXT_BODY)
        self.style.configure("Horizontal.TScrollbar", background=BG_PANEL, troughcolor=BG_CANVAS, bordercolor=BG_CANVAS, arrowcolor=TEXT_BODY)
        self.style.configure("Accent.Horizontal.TProgressbar", troughcolor=BG_INPUT, bordercolor=BORDER_CARD, background=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT)

    def _build_shell(self):
        # Status bar must be packed FIRST so it anchors to the bottom
        # before the shell claims all remaining space with expand=True
        self.status_bar = tk.Frame(self.root, bg=BG_PANEL, height=32,
                                   highlightbackground=BORDER_CARD, highlightthickness=1)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        self.status_canvas = tk.Canvas(self.status_bar, width=18, height=18,
                                       bg=BG_PANEL, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(10, 0), pady=6)
        self.status_dot = self.status_canvas.create_oval(4, 4, 14, 14, fill=ERROR, outline="")
        self.status_label = tk.Label(self.status_bar, text="Hub offline",
                                     fg=TEXT_BODY, bg=BG_PANEL)
        self.status_label.pack(side="left", padx=8)
        self.user_label = tk.Label(self.status_bar, text=f"User: {self.username}",
                                   fg=TEXT_MUTED, bg=BG_PANEL)
        self.user_label.pack(side="left", padx=12)
        langgraph_text = "LangGraph ready" if LANGGRAPH_OK else "LangGraph offline"
        self.langgraph_label = tk.Label(self.status_bar, text=langgraph_text,
                                        fg=TEXT_MUTED, bg=BG_PANEL)
        self.langgraph_label.pack(side="left", padx=12)
        self.llm_label = tk.Label(self.status_bar, text="⬡ …", fg=ACCENT,
                                  bg=BG_PANEL, font=("Segoe UI", 9))
        self.llm_label.pack(side="left", padx=12)
        self.clock_label = tk.Label(self.status_bar, text="", fg=TEXT_MUTED, bg=BG_PANEL)
        self.clock_label.pack(side="right", padx=10)

        # Main shell — expands into remaining space above the status bar
        self.shell = tk.Frame(self.root, bg=BG_CANVAS)
        self.shell.pack(fill="both", expand=True)

        self.rail = tk.Frame(self.shell, width=60, bg=BG_RAIL)
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)

        rail_top = tk.Frame(self.rail, bg=BG_RAIL)
        rail_top.pack(fill="x", pady=(10, 4))
        _logo_shown = False
        _brandmark = APP_ROOT / "branding" / "master" / "archonhub-brandmark.png"
        if _brandmark.exists():
            try:
                from PIL import Image as _PIL, ImageTk as _PILTk
                _pil = _PIL.open(_brandmark).convert("RGBA").resize((44, 44), _PIL.LANCZOS)
                self._rail_logo = _PILTk.PhotoImage(_pil)
                tk.Label(rail_top, image=self._rail_logo, bg=BG_RAIL).pack(pady=(4, 2))
                _logo_shown = True
            except Exception:
                pass
        if not _logo_shown:
            tk.Label(rail_top, text="⬡", fg=ACCENT, bg=BG_RAIL, font=("Segoe UI", 20, "bold")).pack()

        for icon, label, method_name in NAV_ITEMS:
            btn = tk.Label(
                self.rail,
                text=icon,
                bg=BG_RAIL,
                fg=TEXT_BODY,
                width=3,
                pady=12,
                cursor="hand2",
                font=("Segoe UI Emoji", 16),
            )
            btn.pack(fill="x", padx=6, pady=2)
            btn.bind("<Button-1>", lambda _e, name=method_name: getattr(self, name)())
            btn.bind("<Enter>", lambda _e, widget=btn: widget.configure(bg=BG_HOVER))
            btn.bind("<Leave>", lambda _e, widget=btn, nav=label: self._reset_nav_bg(widget, nav))
            ToolTip(btn, label)
            self.nav_buttons[label] = btn

        tk.Label(self.rail, text="v1", fg=TEXT_MUTED, bg=BG_RAIL).pack(side="bottom", pady=8)

        self.content = tk.Frame(self.shell, bg=BG_CANVAS)
        self.content.pack(side="left", fill="both", expand=True)

    def _update_clock(self):
        self.clock_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self._update_status_bar()
        self.root.after(1000, self._update_clock)

    def _update_status_bar(self):
        try:
            if not self.status_canvas.winfo_exists():
                return
        except Exception:
            return
        online = bool(getattr(self.hub, "online", False))
        color = SUCCESS if online else ERROR
        try:
            self.status_canvas.itemconfigure(self.status_dot, fill=color)
            self.status_label.configure(text="Hub online" if online else "Hub offline", fg=TEXT_PRIMARY if online else TEXT_BODY)
        except Exception:
            return
        # Refresh LLM model pill
        try:
            from hub_nodes import _load_ai_config
            cfg = _load_ai_config()
            db_cfg = hub_db.get_config() or {}
            provider = db_cfg.get("llm_provider") or cfg.get("provider", "openai")
            model    = db_cfg.get("llm_model")    or cfg.get("model",    "gpt-4o-mini")
            self.llm_label.configure(text=f"⬡ {provider}/{model}")
        except Exception:
            pass

    def _reset_nav_bg(self, widget, label):
        if self.current_view == label:
            widget.configure(bg=ACCENT, fg=BG_RAIL)
        else:
            widget.configure(bg=BG_RAIL, fg=TEXT_BODY)

    def _set_active_nav(self, label):
        self.current_view = label
        for nav_label, widget in self.nav_buttons.items():
            if nav_label == label:
                widget.configure(bg=ACCENT, fg=BG_RAIL)
            else:
                widget.configure(bg=BG_RAIL, fg=TEXT_BODY)

    def _clear_content(self):
        # Stop markets feed before destroying widgets
        if hasattr(self, "_markets_tab") and self._markets_tab is not None:
            try:
                self._markets_tab.stop_feed()
            except Exception:
                pass
            self._markets_tab = None
        for child in self.content.winfo_children():
            child.destroy()

    def _card(self, parent, title="", subtitle="", padx=14, pady=12):
        frame = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDER_CARD, highlightthickness=1)
        if title:
            tk.Label(frame, text=title, bg=BG_PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=padx, pady=(pady, 2))
        if subtitle:
            tk.Label(frame, text=subtitle, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", padx=padx, pady=(0, 8))
        return frame

    def _scrollable_area(self, parent, bg=BG_CANVAS):
        wrapper = tk.Frame(parent, bg=bg)
        canvas = tk.Canvas(wrapper, bg=bg, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=bg)
        inner_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize_inner(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _resize_canvas(event):
            canvas.itemconfigure(inner_window, width=event.width)

        inner.bind("<Configure>", _resize_inner)
        canvas.bind("<Configure>", _resize_canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return wrapper, canvas, inner

    def _section_header(self, parent, title, subtitle="", actions=None):
        frame = tk.Frame(parent, bg=BG_CANVAS)
        frame.pack(fill="x", padx=20, pady=(18, 10))
        left = tk.Frame(frame, bg=BG_CANVAS)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=title, bg=BG_CANVAS, fg=TEXT_PRIMARY, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(left, text=subtitle, bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor="w", pady=(2, 0))
        if actions:
            action_frame = tk.Frame(frame, bg=BG_CANVAS)
            action_frame.pack(side="right")
            for action_text, action_cmd in actions:
                self._button(action_frame, action_text, action_cmd).pack(side="left", padx=4)
        return frame

    def _button(self, parent, text, command, accent=False, width=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=ACCENT if accent else BG_CARD,
            fg=BG_RAIL if accent else TEXT_PRIMARY,
            activebackground=ACCENT_DARK if accent else BG_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
        )

    def _entry(self, parent, textvariable=None, width=None, show=None):
        entry = tk.Entry(parent, textvariable=textvariable, bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", width=width, show=show)
        return entry

    def _combo(self, parent, variable, values, width=None):
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=width)
        return combo

    def _text_widget(self, parent, height=5):
        widget = scrolledtext.ScrolledText(parent, bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", wrap="word", height=height)
        widget.configure(selectbackground=ACCENT_DARK)
        return widget

    def _set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _mask_token(self, token):
        if not token:
            return "(not set)"
        if len(token) <= 8:
            return "*" * len(token)
        return f"{token[:3]}{'*' * (len(token) - 6)}{token[-3:]}"

    def _human_time(self, value):
        if not value:
            return "—"
        text = str(value).replace("T", " ")
        return text[:19]

    def _widget_ok(self, attr: str) -> bool:
        """Return True only if the attribute exists AND the Tk widget is still alive.
        Prevents TclError crashes when background threads fire UI updates after a
        widget has been destroyed (e.g. during tab/pane rebuild)."""
        widget = getattr(self, attr, None)
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except Exception:
            return False

    def _status_badge(self, parent, text, color):
        return tk.Label(parent, text=text, bg=color, fg=BG_RAIL, padx=8, pady=2, font=("Segoe UI", 9, "bold"))

    def show_toast(self, text, color=ACCENT):
        if self.toast_label and self.toast_label.winfo_exists():
            self.toast_label.destroy()
        self.toast_label = tk.Label(self.root, text=text, bg=color, fg=BG_RAIL, padx=16, pady=8, font=("Segoe UI", 10, "bold"))
        self.toast_label.place(relx=0.5, rely=0.04, anchor="n")
        self.root.after(3000, lambda: self.toast_label and self.toast_label.winfo_exists() and self.toast_label.destroy())

    def ask_pin(self, callback):
        dialog = tk.Toplevel(self.root)
        dialog.title("Admin PIN")
        dialog.configure(bg=BG_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="Enter 4-digit PIN", bg=BG_PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "bold")).pack(padx=20, pady=(18, 10))
        pin_var = tk.StringVar()
        entry = self._entry(dialog, textvariable=pin_var, width=8, show="*")
        entry.pack(padx=20, pady=(0, 14))
        entry.focus_set()

        def _submit():
            if pin_var.get() == "1914":
                dialog.destroy()
                callback()
            else:
                messagebox.showerror("Invalid PIN", "Incorrect PIN.")

        button_row = tk.Frame(dialog, bg=BG_PANEL)
        button_row.pack(pady=(0, 18))
        self._button(button_row, "Cancel", dialog.destroy).pack(side="left", padx=6)
        self._button(button_row, "Unlock", _submit, accent=True).pack(side="left", padx=6)
        dialog.bind("<Return>", lambda _e: _submit())

    def draw_graph_canvas(self, canvas, graph_type, current_node=""):
        canvas.delete("all")
        nodes = GRAPH_LAYOUTS.get(graph_type, GRAPH_LAYOUTS["reflexion"])
        width = max(canvas.winfo_width(), 900)
        height = max(canvas.winfo_height(), 180)
        canvas.configure(bg=BG_PANEL)
        count = len(nodes)
        if count == 1:
            positions = [(width // 2, height // 2)]
        else:
            gap = width // (count + 1)
            positions = [(gap * (idx + 1), height // 2) for idx in range(count)]

        for idx in range(len(nodes) - 1):
            x1, y1 = positions[idx]
            x2, y2 = positions[idx + 1]
            canvas.create_line(x1 + 26, y1, x2 - 26, y2, fill=ACCENT_LIGHT, width=2, arrow=tk.LAST, arrowshape=(10, 12, 4))

        for idx, node in enumerate(nodes):
            x, y = positions[idx]
            fill = NC.get(node, ACCENT)
            outline = "#facc15" if node == current_node else BORDER_CARD
            radius = 26 if node != current_node else 30
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=outline, width=3 if node == current_node else 2)
            canvas.create_text(x, y + 44, text=node.replace("_", "\n"), fill=TEXT_PRIMARY, font=("Segoe UI", 9, "bold"), justify="center")

    def _update_quick_agents(self, *_args):
        team = self.quick_team_var.get()
        agents = AGENT_REGISTRY.get(team, [])
        if hasattr(self, "quick_agent_combo"):
            self.quick_agent_combo.configure(values=agents)
        if self.quick_agent_var.get() not in agents and agents:
            self.quick_agent_var.set(agents[0])
        if hasattr(self, "home_graph_canvas"):
            self.draw_graph_canvas(self.home_graph_canvas, self.quick_graph_var.get())

    def _submit_quick_run(self):
        task = self.quick_task_text.get("1.0", "end").strip()
        if not task:
            self.show_toast("Enter a task first.", WARNING)
            return
        config = {
            "agent_id": self.quick_agent_var.get(),
            "project": self.quick_project_var.get(),
            "graph": self.quick_graph_var.get(),
            "task": task,
            "max_revisions": int(self.quick_max_rev_var.get() or 2),
        }
        self._run_agent(config)

    def _run_agent(self, config: dict):
        config = dict(config)
        config.setdefault("run_id", uuid.uuid4().hex[:12])
        run_id = config["run_id"]
        self.local_run_configs[run_id] = dict(config)
        self.run_logs.setdefault(run_id, [])
        self.run_state.setdefault(run_id, {"current_node": "", "status": "queued"})
        self.run_logs[run_id].append(f"[{datetime.now().strftime('%H:%M:%S')}] Run queued for {config['agent_id']}")

        if getattr(self.hub, "online", False):
            try:
                result = self.hub.submit_run(
                    agent_id=config["agent_id"],
                    project=config["project"],
                    graph=config["graph"],
                    task=config["task"],
                    max_revisions=config.get("max_revisions", 2),
                )
                if result:
                    self.show_toast("Run submitted to Hub.", SUCCESS)
                    self._ui_queue.put(("refresh_runs",))
                    return
            except Exception:
                pass

        cancel_flag = threading.Event()
        self.cancel_flags[run_id] = cancel_flag
        try:
            hub_db.save_run(
                run_id,
                config["agent_id"],
                config["project"],
                config["graph"],
                config["task"],
                0.0,
                "",
                0,
                "",
                1,
                "running",
            )
        except Exception:
            pass

        def _thread():
            def emit(event_type, **kwargs):
                self._ui_queue.put(("run_event", event_type, kwargs))

            try:
                final = run_graph({**config, "cancel_flag": cancel_flag}, emit=emit)
                status = "cancelled" if cancel_flag.is_set() else "complete"
                if str(final.get("output", "")).lower().startswith("run failed:"):
                    status = "failed"
                hub_db.save_run(
                    final.get("run_id", run_id),
                    final.get("agent_id", config["agent_id"]),
                    final.get("project", config["project"]),
                    final.get("graph_type", config["graph"]),
                    final.get("task", config["task"]),
                    float(final.get("score", 0.0) or 0.0),
                    final.get("critique", ""),
                    int(final.get("revision_count", 0) or 0),
                    final.get("output", ""),
                    int(final.get("skill_version", 1) or 1),
                    status,
                )
                if "briefing" in config.get("task", "").lower():
                    hub_db.cache_briefing(
                        {
                            "content": final.get("output", ""),
                            "score": final.get("score", 0.0),
                            "agent_id": final.get("agent_id", config["agent_id"]),
                            "created_at": datetime.now().isoformat(),
                        }
                    )
            except Exception as exc:
                hub_db.save_run(run_id, config["agent_id"], config["project"], config["graph"], config["task"], 0.0, str(exc), 0, f"Run failed: {exc}", 1, "failed")
                self._ui_queue.put(("run_event", "run_failed", {"run_id": run_id, "agent_id": config["agent_id"], "graph": config["graph"], "error": str(exc)}))
            finally:
                self._ui_queue.put(("refresh_runs",))
                self._ui_queue.put(("refresh_digest",))

        threading.Thread(target=_thread, daemon=True).start()
        self.show_toast("Running locally.", ACCENT)
        self._ui_queue.put(("refresh_runs",))

    def _poll_hub_events(self):
        try:
            for event in self.hub.poll_events():
                self._ui_queue.put(("hub_event", event))
        except Exception:
            pass
        self.root.after(500, self._poll_hub_events)

    def _poll_queue(self):
        while True:
            try:
                item = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            kind = item[0]
            if kind == "hub_event":
                self._handle_hub_event(item[1])
            elif kind == "run_event":
                self._handle_run_event(item[1], item[2])
            elif kind == "inez_result":
                think_run_id = item[1]
                result       = item[2]
                self._inez_handle_result(think_run_id, result)
            elif kind == "refresh_runs":
                if self._widget_ok("runs_tree"):
                    self._refresh_runs()
                self._refresh_home_status()
            elif kind == "refresh_todos":
                if self._widget_ok("todo_tree"):
                    self._refresh_todos()
            elif kind == "refresh_digest":
                if self._widget_ok("digest_text"):
                    self._refresh_digest()
            elif kind == "refresh_schedule":
                if self._widget_ok("schedule_tree"):
                    self._refresh_schedule()
            elif kind == "refresh_clients":
                if self._widget_ok("clients_cards_container"):
                    self._refresh_clients()
            elif kind == "refresh_travel":
                if self._widget_ok("travel_cards_container"):
                    self._refresh_travel()
            elif kind == "refresh_reports":
                if self._widget_ok("reports_container"):
                    self._refresh_reports()
            elif kind == "refresh_connectors":
                if self._widget_ok("connectors_tree"):
                    self._refresh_connectors()
            elif kind == "refresh_users":
                if self._widget_ok("users_tree"):
                    self._refresh_users()
            elif kind == "notification":
                self.show_toast(item[1], item[2])
            elif kind == "toast":
                self.show_toast(item[1], item[2] if len(item) > 2 else ACCENT)
        self.root.after(100, self._poll_queue)

    def _handle_hub_event(self, event):
        event_type = event.get("type") or event.get("event") or ""
        if event_type == "hub_status":
            self._update_status_bar()
            self._refresh_home_status()
            return
        if event_type in {"run_started", "node_update", "run_completed", "run_failed"}:
            self._handle_run_event(event_type, event)
            return
        if event_type == "notification":
            self.show_toast(event.get("text", "Notification"), event.get("color", ACCENT))

    def _handle_run_event(self, event_type, data):
        run_id = data.get("run_id")
        if not run_id:
            return
        self.run_logs.setdefault(run_id, [])
        stamp = datetime.now().strftime("%H:%M:%S")
        if event_type == "run_started":
            self.run_state.setdefault(run_id, {})
            self.run_state[run_id]["status"] = "running"
            self.run_logs[run_id].append(f"[{stamp}] Run started")
        elif event_type == "node_update":
            node = data.get("node", "")
            status = data.get("status", "")
            self.run_state.setdefault(run_id, {})
            if status == "running":
                self.run_state[run_id]["current_node"] = node
            self.run_state[run_id]["status"] = status or self.run_state[run_id].get("status", "running")
            message = f"[{stamp}] {node}: {status}"
            if data.get("score") is not None:
                message += f" | score={data.get('score')}"
            self.run_logs[run_id].append(message)
        elif event_type == "run_completed":
            self.run_state.setdefault(run_id, {})
            self.run_state[run_id]["status"] = "complete"
            self.run_logs[run_id].append(f"[{stamp}] Completed | score={float(data.get('score', 0.0) or 0.0):.2f}")
        elif event_type == "run_failed":
            self.run_state.setdefault(run_id, {})
            self.run_state[run_id]["status"] = "failed"
            self.run_logs[run_id].append(f"[{stamp}] Failed | {data.get('error', 'Unknown error')}")

        if self.selected_run_id == run_id and self._widget_ok("run_log_text"):
            self._update_run_detail(run_id)
        if self._widget_ok("runs_tree"):
            self._refresh_runs(select_run_id=run_id)
        self._refresh_home_status()

        # Forward run events to chat if this is a chat-initiated run
        if run_id in self._chat_run_frames:
            self._chat_handle_run_event(event_type, data, run_id)

    def _get_runs(self):
        agent = None if self.run_filter_agent_var.get() == "all" else self.run_filter_agent_var.get()
        project = None if self.run_filter_project_var.get() == "all" else self.run_filter_project_var.get()
        status = None if self.run_filter_status_var.get() == "all" else self.run_filter_status_var.get()
        rows = []
        try:
            if getattr(self.hub, "online", False):
                rows = self.hub.list_runs(limit=200, agent_id=agent, project=project, status=status) or []
        except Exception:
            rows = []
        if not rows:
            rows = hub_db.load_runs(limit=200, agent_id=agent, project=project, status=status)
        return rows

    def _refresh_home_status(self):
        # Guard: widget must exist and not have been destroyed
        if not hasattr(self, "home_status_value"):
            return
        try:
            if not self.home_status_value.winfo_exists():
                return
        except Exception:
            return
        online = bool(getattr(self.hub, "online", False))
        health = {}
        try:
            if hasattr(self.hub, "get_health"):
                health = self.hub.get_health() or {}
        except Exception:
            health = {}
        runs = self._get_runs()
        running = [r for r in runs if r.get("status") in {"running", "queued"}]
        status_text = "Online" if online else "Offline"
        try:
            self.home_status_value.configure(text=status_text, fg=SUCCESS if online else ERROR)
            uptime = health.get("uptime") or health.get("uptime_seconds") or ("—" if not online else "Connected")
            self.home_uptime_value.configure(text=str(uptime))
            self.home_active_runs_value.configure(text=str(len(running)))
        except Exception:
            pass

    def _render_agent_cards(self):
        for child in self.agent_cards_container.winfo_children():
            child.destroy()
        teams = list(AGENT_REGISTRY.items())
        for idx, (team, agents) in enumerate(teams):
            card = tk.Frame(self.agent_cards_container, bg=BG_CARD, highlightbackground=BORDER_CARD, highlightthickness=1)
            row, col = divmod(idx, 2)
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.agent_cards_container.grid_columnconfigure(col, weight=1)
            tk.Label(card, text=f"{TEAM_EMOJI.get(team, '•')}  {team}", bg=BG_CARD, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(14, 4))
            tk.Label(card, text=f"{len(agents)} agents", bg=BG_CARD, fg=ACCENT_LIGHT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(0, 10))
            for agent in agents:
                tk.Label(card, text=f"• {agent}", bg=BG_CARD, fg=TEXT_BODY, anchor="w").pack(fill="x", padx=14, pady=1)

    def show_home(self):
        self._set_active_nav("Home")
        self._clear_content()
        self._section_header(self.content, "ArchonHub", "Microsoft 365-inspired control surface for teams, runs, and workflows.")

        paned = tk.PanedWindow(self.content, orient="horizontal", sashwidth=6,
                               bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ── Left panel: Quick Run + Hub Status ───────────────────────────
        left = tk.Frame(paned, bg=BG_CANVAS, width=340)
        paned.add(left, minsize=300)

        quick = self._card(left, "Quick Run", "Submit a run to Hub or local LangGraph fallback.")
        quick.pack(fill="x", pady=(0, 10))
        form = tk.Frame(quick, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 12))

        tk.Label(form, text="Team", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=2)
        self.quick_team_combo = self._combo(form, self.quick_team_var, list(AGENT_REGISTRY.keys()))
        self.quick_team_combo.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.quick_team_combo.bind("<<ComboboxSelected>>", self._update_quick_agents)

        tk.Label(form, text="Agent", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=2)
        self.quick_agent_combo = self._combo(form, self.quick_agent_var, AGENT_REGISTRY[self.quick_team_var.get()])
        self.quick_agent_combo.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        tk.Label(form, text="Project", bg=BG_PANEL, fg=TEXT_BODY).grid(row=4, column=0, sticky="w", pady=2)
        self._combo(form, self.quick_project_var, PROJECTS).grid(row=5, column=0, sticky="ew", pady=(0, 6))

        tk.Label(form, text="Graph", bg=BG_PANEL, fg=TEXT_BODY).grid(row=6, column=0, sticky="w", pady=2)
        graph_combo = self._combo(form, self.quick_graph_var, GRAPH_NAMES)
        graph_combo.grid(row=7, column=0, sticky="ew", pady=(0, 6))
        graph_combo.bind("<<ComboboxSelected>>", self._update_quick_agents)

        tk.Label(form, text="Task", bg=BG_PANEL, fg=TEXT_BODY).grid(row=8, column=0, sticky="w", pady=2)
        self.quick_task_text = self._text_widget(form, height=5)
        self.quick_task_text.grid(row=9, column=0, sticky="nsew", pady=(0, 8))
        form.grid_columnconfigure(0, weight=1)
        self._button(form, "▶ Run Agent", self._submit_quick_run, accent=True).grid(row=10, column=0, sticky="ew")

        hub_card = self._card(left, "Hub Status")
        hub_card.pack(fill="x")
        grid = tk.Frame(hub_card, bg=BG_PANEL)
        grid.pack(fill="x", padx=14, pady=(0, 12))
        tk.Label(grid, text="Connection", bg=BG_PANEL, fg=TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=3)
        self.home_status_value = tk.Label(grid, text="Offline", bg=BG_PANEL, fg=ERROR,
                                          font=("Segoe UI", 11, "bold"))
        self.home_status_value.grid(row=0, column=1, sticky="e", pady=3)
        tk.Label(grid, text="Uptime", bg=BG_PANEL, fg=TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=3)
        self.home_uptime_value = tk.Label(grid, text="—", bg=BG_PANEL, fg=TEXT_PRIMARY)
        self.home_uptime_value.grid(row=1, column=1, sticky="e", pady=3)
        tk.Label(grid, text="Active runs", bg=BG_PANEL, fg=TEXT_MUTED).grid(row=2, column=0, sticky="w", pady=3)
        self.home_active_runs_value = tk.Label(grid, text="0", bg=BG_PANEL, fg=TEXT_PRIMARY)
        self.home_active_runs_value.grid(row=2, column=1, sticky="e", pady=3)
        grid.grid_columnconfigure(1, weight=1)

        # ── Right panel: Inez Chat ────────────────────────────────────────
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(right)
        self._build_inez_chat_panel(right)

        self._refresh_home_status()

    def _build_inez_chat_panel(self, parent):
        """Embed the full Inez chat interface into any parent frame (used on Home + Inez tab)."""
        # Header
        top = tk.Frame(parent, bg=BG_PANEL,
                       highlightbackground=BORDER_CARD, highlightthickness=1)
        top.pack(fill="x")

        av = tk.Canvas(top, width=34, height=34, bg=BG_PANEL, highlightthickness=0)
        av.create_oval(3, 3, 31, 31, fill="#7c3aed", outline="")
        av.create_text(17, 17, text="👑", font=("Segoe UI", 14))
        av.pack(side="left", padx=(12, 6), pady=6)

        name_col = tk.Frame(top, bg=BG_PANEL)
        name_col.pack(side="left", pady=6)
        tk.Label(name_col, text="Inez", bg=BG_PANEL, fg="#c4b5fd",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(name_col, text="Chief of Staff — Smith Capital Portfolio",
                 bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        hub_online = getattr(self.hub, "online", False)
        dot_color = SUCCESS if hub_online else WARNING
        dot_text  = "● Hub connected" if hub_online else "● Local mode"
        tk.Label(top, text=dot_text, bg=BG_PANEL, fg=dot_color,
                 font=("Segoe UI", 9)).pack(side="right", padx=14)

        # Bubble area
        bubble_outer = tk.Frame(parent, bg=BG_CANVAS)
        bubble_outer.pack(fill="both", expand=True)

        chat_canvas = tk.Canvas(bubble_outer, bg=BG_CANVAS, highlightthickness=0, bd=0)
        chat_sb = ttk.Scrollbar(bubble_outer, orient="vertical", command=chat_canvas.yview)
        self._chat_bubbles_frame = tk.Frame(chat_canvas, bg=BG_CANVAS)
        self._chat_canvas = chat_canvas
        bw = chat_canvas.create_window((0, 0), window=self._chat_bubbles_frame, anchor="nw")

        def _on_cfg(e): chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
        def _on_resize(e): chat_canvas.itemconfigure(bw, width=e.width)
        self._chat_bubbles_frame.bind("<Configure>", _on_cfg)
        chat_canvas.bind("<Configure>", _on_resize)
        chat_canvas.configure(yscrollcommand=chat_sb.set)
        chat_sb.pack(side="right", fill="y")
        chat_canvas.pack(side="left", fill="both", expand=True)

        for msg in self._chat_messages:
            self._chat_render_bubble(msg)

        if not self._chat_messages:
            welcome = {
                "role": "inez",
                "content": "Good to see you. I'm Inez — your Chief of Staff. What do you need?",
                "ts": datetime.now().strftime("%H:%M"),
            }
            self._chat_messages.append(welcome)
            self._chat_render_bubble(welcome)

        # Input bar
        input_bar = tk.Frame(parent, bg=BG_PANEL,
                             highlightbackground=BORDER_CARD, highlightthickness=1)
        input_bar.pack(fill="x", side="bottom")

        self._chat_input = tk.Text(input_bar, height=3, bg=BG_INPUT, fg=TEXT_PRIMARY,
                                   insertbackground=ACCENT, relief="flat",
                                   font=("Segoe UI", 11), wrap="word", padx=10, pady=8)
        self._chat_input.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)
        self._chat_input.bind("<Return>", lambda e: (self._inez_send(), "break")[1])
        self._chat_input.bind("<Shift-Return>", lambda e: None)

        send_btn = self._button(input_bar, "  Send  ", self._inez_send)
        send_btn.pack(side="right", padx=10, pady=8, ipadx=10, ipady=6)
        tk.Label(input_bar, text="Enter ↵ send  ·  ⇧Enter newline",
                 bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(side="right", padx=4)


    def show_runs(self):
        self._set_active_nav("Runs")
        self._clear_content()
        self._section_header(self.content, "Runs", "Monitor historical and active agent runs.")

        paned = tk.PanedWindow(self.content, orient="horizontal", sashwidth=6, bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        left = tk.Frame(paned, bg=BG_CANVAS, width=420)
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(left, minsize=400)
        paned.add(right)

        filters = self._card(left, "Filters")
        filters.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(filters, bg=BG_PANEL)
        inner.pack(fill="x", padx=14, pady=(0, 14))
        tk.Label(inner, text="Agent", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=4)
        self._combo(inner, self.run_filter_agent_var, ["all"] + [a for agents in AGENT_REGISTRY.values() for a in agents]).grid(row=1, column=0, sticky="ew")
        tk.Label(inner, text="Project", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        self._combo(inner, self.run_filter_project_var, ["all"] + PROJECTS).grid(row=3, column=0, sticky="ew")
        tk.Label(inner, text="Status", bg=BG_PANEL, fg=TEXT_BODY).grid(row=4, column=0, sticky="w", pady=4)
        self._combo(inner, self.run_filter_status_var, ["all", "queued", "running", "complete", "failed", "cancelled"]).grid(row=5, column=0, sticky="ew")
        self._button(inner, "Refresh", self._refresh_runs, accent=True).grid(row=6, column=0, sticky="ew", pady=(10, 0))
        inner.grid_columnconfigure(0, weight=1)

        list_card = self._card(left, "Run List")
        list_card.pack(fill="both", expand=True)
        columns = ("run_id", "agent", "project", "graph", "score", "status", "time")
        self.runs_tree = ttk.Treeview(list_card, columns=columns, show="headings", selectmode="browse")
        for column, text, width in (
            ("run_id", "Run ID", 140),
            ("agent", "Agent", 170),
            ("project", "Project", 130),
            ("graph", "Graph", 110),
            ("score", "Score", 70),
            ("status", "Status", 100),
            ("time", "Time", 150),
        ):
            self.runs_tree.heading(column, text=text)
            self.runs_tree.column(column, width=width, anchor="w")
        self.runs_tree.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.runs_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_run_selected())

        detail_card = self._card(right, "Run Detail")
        detail_card.pack(fill="both", expand=True)
        top = tk.Frame(detail_card, bg=BG_PANEL)
        top.pack(fill="x", padx=14, pady=(0, 10))
        self.run_meta_label = tk.Label(top, text="Select a run", bg=BG_PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold"))
        self.run_meta_label.pack(side="left")
        self.cancel_run_btn = self._button(top, "Cancel Run", self._cancel_selected_run)
        self.cancel_run_btn.pack(side="right")

        tk.Label(detail_card, text="Task", bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=14)
        self.run_task_text = self._text_widget(detail_card, height=4)
        self.run_task_text.pack(fill="x", padx=14, pady=(0, 8))
        self.run_task_text.configure(state="disabled")

        score_row = tk.Frame(detail_card, bg=BG_PANEL)
        score_row.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(score_row, text="Score", bg=BG_PANEL, fg=TEXT_BODY).pack(side="left")
        self.run_score_value = tk.Label(score_row, text="0.00", bg=BG_PANEL, fg=TEXT_PRIMARY)
        self.run_score_value.pack(side="right")
        self.run_score_bar = ttk.Progressbar(detail_card, style="Accent.Horizontal.TProgressbar", maximum=100)
        self.run_score_bar.pack(fill="x", padx=14, pady=(0, 8))

        tk.Label(detail_card, text="Critique", bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=14)
        self.run_critique_text = self._text_widget(detail_card, height=4)
        self.run_critique_text.pack(fill="x", padx=14, pady=(0, 8))
        self.run_critique_text.configure(state="disabled")

        self.run_graph_canvas = tk.Canvas(detail_card, height=150, bg=BG_PANEL, highlightthickness=0)
        self.run_graph_canvas.pack(fill="x", padx=14, pady=(0, 8))
        self.run_graph_canvas.bind("<Configure>", lambda _e: self.selected_run_id and self._update_run_graph())

        tk.Label(detail_card, text="Output", bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=14)
        self.run_output_text = self._text_widget(detail_card, height=10)
        self.run_output_text.pack(fill="both", expand=True, padx=14, pady=(0, 8))
        self.run_output_text.configure(state="disabled")

        tk.Label(detail_card, text="Live Execution Log", bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=14)
        self.run_log_text = self._text_widget(detail_card, height=10)
        self.run_log_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.run_log_text.configure(state="disabled")

        self._refresh_runs()

    def _refresh_runs(self, select_run_id=None):
        if not self._widget_ok("runs_tree"):
            return
        rows = self._get_runs()
        try:
            self.runs_tree.delete(*self.runs_tree.get_children())
            self.runs_lookup = {}
            for row in rows:
                run_id = row.get("run_id")
                self.runs_lookup[run_id] = row
                values = (
                    str(run_id)[:15],
                    row.get("agent_id", ""),
                    row.get("project", ""),
                    row.get("graph", ""),
                    f"{float(row.get('score', 0.0) or 0.0):.2f}",
                    row.get("status", ""),
                    self._human_time(row.get("created_at", "")),
                )
                tag = row.get("status", "")
                self.runs_tree.insert("", "end", iid=run_id, values=values, tags=(tag,))
            for tag, color in STATUS_COLORS.items():
                self.runs_tree.tag_configure(tag, foreground=color)
            target = select_run_id or self.selected_run_id
            if target and target in self.runs_tree.get_children():
                self.runs_tree.selection_set(target)
                self.runs_tree.focus(target)
                self._update_run_detail(target)
            elif rows:
                first = rows[0]["run_id"]
                self.runs_tree.selection_set(first)
                self._update_run_detail(first)
        except Exception:
            pass

    def _on_run_selected(self):
        selected = self.runs_tree.selection()
        if selected:
            self._update_run_detail(selected[0])

    def _update_run_graph(self):
        row = self.runs_lookup.get(self.selected_run_id, {})
        graph_name = row.get("graph", self.local_run_configs.get(self.selected_run_id, {}).get("graph", "reflexion"))
        current_node = self.run_state.get(self.selected_run_id, {}).get("current_node", "")
        self.draw_graph_canvas(self.run_graph_canvas, graph_name, current_node=current_node)

    def _update_run_detail(self, run_id):
        self.selected_run_id = run_id
        row = self.runs_lookup.get(run_id) or {}
        task = row.get("task", self.local_run_configs.get(run_id, {}).get("task", ""))
        output = row.get("output", "")
        critique = row.get("critique", "")
        score = float(row.get("score", 0.0) or 0.0)
        status = row.get("status", self.run_state.get(run_id, {}).get("status", ""))
        agent = row.get("agent_id", self.local_run_configs.get(run_id, {}).get("agent_id", ""))
        self.run_meta_label.configure(text=f"{agent} • {status}")
        self._set_text(self.run_task_text, task)
        self._set_text(self.run_output_text, output or "(awaiting output)")
        self._set_text(self.run_critique_text, critique or "—")
        self.run_score_value.configure(text=f"{score:.2f}")
        self.run_score_bar["value"] = score * 100
        self._set_text(self.run_log_text, "\n".join(self.run_logs.get(run_id, [])) or "No log events yet.")
        self.cancel_run_btn.configure(state="normal" if status == "running" else "disabled")
        self._update_run_graph()

    def _cancel_selected_run(self):
        if not self.selected_run_id:
            return
        if self.selected_run_id in self.cancel_flags:
            self.cancel_flags[self.selected_run_id].set()
            hub_db.update_run_status(self.selected_run_id, "cancelled")
            self.run_logs.setdefault(self.selected_run_id, []).append(f"[{datetime.now().strftime('%H:%M:%S')}] Cancellation requested")
            self._refresh_runs(select_run_id=self.selected_run_id)
            self.show_toast("Local cancellation requested.", WARNING)
            return
        try:
            if self.hub.cancel_run(self.selected_run_id):
                self.show_toast("Hub cancellation requested.", WARNING)
        except Exception:
            pass

    def show_todos(self):
        self._set_active_nav("Todos")
        self._clear_content()
        self._section_header(self.content, "Todos", "Track work across projects and agents.")

        paned = tk.PanedWindow(self.content, orient="horizontal", sashwidth=6, bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        left = tk.Frame(paned, bg=BG_CANVAS, width=380)
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(left, minsize=360)
        paned.add(right)

        add_card = self._card(left, "Add Todo")
        add_card.pack(fill="x", pady=(0, 12))
        form = tk.Frame(add_card, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 14))
        self.todo_title_var = tk.StringVar()
        self.todo_priority_var = tk.StringVar(value="medium")
        self.todo_project_var = tk.StringVar(value=PROJECTS[0])
        self.todo_due_var = tk.StringVar()
        tk.Label(form, text="Title", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=4)
        self._entry(form, self.todo_title_var).grid(row=1, column=0, sticky="ew")
        tk.Label(form, text="Description", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        self.todo_desc_text = self._text_widget(form, height=5)
        self.todo_desc_text.grid(row=3, column=0, sticky="ew")
        tk.Label(form, text="Priority", bg=BG_PANEL, fg=TEXT_BODY).grid(row=4, column=0, sticky="w", pady=4)
        self._combo(form, self.todo_priority_var, ["urgent", "high", "medium", "low"]).grid(row=5, column=0, sticky="ew")
        tk.Label(form, text="Project", bg=BG_PANEL, fg=TEXT_BODY).grid(row=6, column=0, sticky="w", pady=4)
        self._combo(form, self.todo_project_var, PROJECTS).grid(row=7, column=0, sticky="ew")
        tk.Label(form, text="Due Date", bg=BG_PANEL, fg=TEXT_BODY).grid(row=8, column=0, sticky="w", pady=4)
        self._entry(form, self.todo_due_var).grid(row=9, column=0, sticky="ew")
        self._button(form, "Add", self._add_todo, accent=True).grid(row=10, column=0, sticky="ew", pady=(10, 0))
        form.grid_columnconfigure(0, weight=1)

        filter_card = self._card(left, "Filters")
        filter_card.pack(fill="x")
        filters = tk.Frame(filter_card, bg=BG_PANEL)
        filters.pack(fill="x", padx=14, pady=(0, 14))
        tk.Label(filters, text="Status", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=4)
        self._combo(filters, self.todo_filter_status_var, ["all", "pending", "in_progress", "done"]).grid(row=1, column=0, sticky="ew")
        tk.Label(filters, text="Project", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        self._combo(filters, self.todo_filter_project_var, ["all"] + PROJECTS).grid(row=3, column=0, sticky="ew")
        self._button(filters, "Refresh", self._refresh_todos).grid(row=4, column=0, sticky="ew", pady=(10, 0))
        filters.grid_columnconfigure(0, weight=1)

        list_card = self._card(right, "Todo List")
        list_card.pack(fill="both", expand=True)
        columns = ("title", "priority", "status", "project", "due_date")
        self.todo_tree = ttk.Treeview(list_card, columns=columns, show="headings", selectmode="browse")
        for column, text, width in (
            ("title", "Title", 280),
            ("priority", "Priority", 90),
            ("status", "Status", 120),
            ("project", "Project", 130),
            ("due_date", "Due Date", 120),
        ):
            self.todo_tree.heading(column, text=text)
            self.todo_tree.column(column, width=width, anchor="w")
        self.todo_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.todo_tree.bind("<<TreeviewSelect>>", lambda _e: self._set_selected_todo())
        self.todo_tree.bind("<Button-3>", self._show_todo_menu)

        actions = tk.Frame(list_card, bg=BG_PANEL)
        actions.pack(fill="x", padx=14, pady=(0, 14))
        self._button(actions, "Edit", self._edit_selected_todo).pack(side="left", padx=4)
        self._button(actions, "Delete", self._delete_selected_todo).pack(side="left", padx=4)
        self._button(actions, "Mark Done", self._mark_selected_todo_done, accent=True).pack(side="left", padx=4)
        self._button(actions, "Mark In Progress", self._mark_selected_todo_in_progress).pack(side="left", padx=4)

        self.todo_menu = tk.Menu(self.root, tearoff=0, bg=BG_PANEL, fg=TEXT_PRIMARY)
        self.todo_menu.add_command(label="Edit", command=self._edit_selected_todo)
        self.todo_menu.add_command(label="Delete", command=self._delete_selected_todo)
        self.todo_menu.add_command(label="Mark Done", command=self._mark_selected_todo_done)
        self.todo_menu.add_command(label="Mark In Progress", command=self._mark_selected_todo_in_progress)
        self._refresh_todos()

    def _todo_query(self):
        status = None if self.todo_filter_status_var.get() == "all" else self.todo_filter_status_var.get()
        project = None if self.todo_filter_project_var.get() == "all" else self.todo_filter_project_var.get()
        rows = []
        try:
            if getattr(self.hub, "online", False):
                rows = self.hub.list_todos(status=status, project=project) or []
        except Exception:
            rows = []
        if not rows:
            rows = hub_db.list_todos(status=status, project=project)
        return rows

    def _refresh_todos(self):
        rows = self._todo_query()
        self.todo_tree.delete(*self.todo_tree.get_children())
        self.todo_lookup = {}
        for row in rows:
            todo_id = row["id"]
            self.todo_lookup[todo_id] = row
            self.todo_tree.insert("", "end", iid=todo_id, values=(row["title"], row["priority"], row["status"], row["project"], row["due_date"]), tags=(row["priority"], row["status"]))
        for tag, color in {**PRIORITY_COLORS, **STATUS_COLORS}.items():
            self.todo_tree.tag_configure(tag, foreground=color)
        if rows:
            target = self.selected_todo_id if self.selected_todo_id in self.todo_lookup else rows[0]["id"]
            self.todo_tree.selection_set(target)
            self.selected_todo_id = target

    def _set_selected_todo(self):
        selected = self.todo_tree.selection()
        self.selected_todo_id = selected[0] if selected else None

    def _show_todo_menu(self, event):
        iid = self.todo_tree.identify_row(event.y)
        if iid:
            self.todo_tree.selection_set(iid)
            self.selected_todo_id = iid
            self.todo_menu.tk_popup(event.x_root, event.y_root)

    def _add_todo(self):
        title = self.todo_title_var.get().strip()
        if not title:
            self.show_toast("Todo title is required.", WARNING)
            return
        description = self.todo_desc_text.get("1.0", "end").strip()
        try:
            if getattr(self.hub, "online", False):
                self.hub.create_todo(title=title, description=description, priority=self.todo_priority_var.get(), project=self.todo_project_var.get(), due_date=self.todo_due_var.get())
            else:
                hub_db.create_todo(title=title, description=description, priority=self.todo_priority_var.get(), project=self.todo_project_var.get(), due_date=self.todo_due_var.get())
            self.todo_title_var.set("")
            self.todo_due_var.set("")
            self.todo_desc_text.delete("1.0", "end")
            self.show_toast("Todo added.", SUCCESS)
            self._refresh_todos()
            self._ui_queue.put(("refresh_digest",))
        except Exception as exc:
            self.show_toast(f"Add failed: {exc}", ERROR)

    def _edit_selected_todo(self):
        if not self.selected_todo_id or self.selected_todo_id not in self.todo_lookup:
            return
        todo = self.todo_lookup[self.selected_todo_id]
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Todo")
        dialog.configure(bg=BG_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        fields = {
            "title": tk.StringVar(value=todo.get("title", "")),
            "priority": tk.StringVar(value=todo.get("priority", "medium")),
            "status": tk.StringVar(value=todo.get("status", "pending")),
            "project": tk.StringVar(value=todo.get("project", "")),
            "due_date": tk.StringVar(value=todo.get("due_date", "")),
        }
        tk.Label(dialog, text="Title", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
        self._entry(dialog, fields["title"]).grid(row=1, column=0, sticky="ew", padx=16)
        tk.Label(dialog, text="Description", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", padx=16, pady=4)
        desc = self._text_widget(dialog, height=6)
        desc.grid(row=3, column=0, sticky="ew", padx=16)
        desc.insert("1.0", todo.get("description", ""))
        tk.Label(dialog, text="Priority", bg=BG_PANEL, fg=TEXT_BODY).grid(row=4, column=0, sticky="w", padx=16, pady=4)
        self._combo(dialog, fields["priority"], ["urgent", "high", "medium", "low"]).grid(row=5, column=0, sticky="ew", padx=16)
        tk.Label(dialog, text="Status", bg=BG_PANEL, fg=TEXT_BODY).grid(row=6, column=0, sticky="w", padx=16, pady=4)
        self._combo(dialog, fields["status"], ["pending", "in_progress", "done"]).grid(row=7, column=0, sticky="ew", padx=16)
        tk.Label(dialog, text="Project", bg=BG_PANEL, fg=TEXT_BODY).grid(row=8, column=0, sticky="w", padx=16, pady=4)
        self._combo(dialog, fields["project"], PROJECTS).grid(row=9, column=0, sticky="ew", padx=16)
        tk.Label(dialog, text="Due Date", bg=BG_PANEL, fg=TEXT_BODY).grid(row=10, column=0, sticky="w", padx=16, pady=4)
        self._entry(dialog, fields["due_date"]).grid(row=11, column=0, sticky="ew", padx=16)

        def _save():
            hub_db.update_todo(
                self.selected_todo_id,
                title=fields["title"].get(),
                description=desc.get("1.0", "end").strip(),
                priority=fields["priority"].get(),
                status=fields["status"].get(),
                project=fields["project"].get(),
                due_date=fields["due_date"].get(),
            )
            dialog.destroy()
            self._refresh_todos()

        row = tk.Frame(dialog, bg=BG_PANEL)
        row.grid(row=12, column=0, sticky="e", padx=16, pady=16)
        self._button(row, "Cancel", dialog.destroy).pack(side="left", padx=4)
        self._button(row, "Save", _save, accent=True).pack(side="left", padx=4)
        dialog.grid_columnconfigure(0, weight=1)

    def _delete_selected_todo(self):
        if self.selected_todo_id:
            hub_db.delete_todo(self.selected_todo_id)
            self.selected_todo_id = None
            self._refresh_todos()
            self._ui_queue.put(("refresh_digest",))

    def _mark_selected_todo_done(self):
        if self.selected_todo_id:
            hub_db.update_todo(self.selected_todo_id, status="done")
            self._refresh_todos()
            self._ui_queue.put(("refresh_digest",))

    def _mark_selected_todo_in_progress(self):
        if self.selected_todo_id:
            hub_db.update_todo(self.selected_todo_id, status="in_progress")
            self._refresh_todos()

    def show_digest(self):
        self._set_active_nav("Digest")
        self._clear_content()
        self._section_header(
            self.content,
            "📰 Daily Digest",
            "Portfolio summary, run performance, and todo pressure.",
            actions=[("🔄 Refresh", self._refresh_digest), ("⚡ Request Briefing", self._request_briefing)],
        )

        stats_row = tk.Frame(self.content, bg=BG_CANVAS)
        stats_row.pack(fill="x", padx=20, pady=(0, 10))
        self.digest_total_card = self._stat_card(stats_row, "Total Runs", "0")
        self.digest_total_card.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.digest_avg_card = self._stat_card(stats_row, "Avg Score", "0.00")
        self.digest_avg_card.pack(side="left", fill="x", expand=True, padx=8)
        self.digest_todo_card = self._stat_card(stats_row, "Pending Todos", "0")
        self.digest_todo_card.pack(side="left", fill="x", expand=True, padx=(8, 0))

        digest_card = self._card(self.content, "")
        digest_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.digest_text = self._text_widget(digest_card, height=30)
        self.digest_text.pack(fill="both", expand=True, padx=14, pady=14)
        self.digest_text.configure(state="disabled")
        self._refresh_digest()

    def _stat_card(self, parent, title, value):
        card = tk.Frame(parent, bg=BG_PANEL, highlightbackground=BORDER_CARD, highlightthickness=1, padx=14, pady=12)
        tk.Label(card, text=title, bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w")
        value_label = tk.Label(card, text=value, bg=BG_PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 18, "bold"))
        value_label.pack(anchor="w", pady=(4, 0))
        card.value_label = value_label
        return card

    def _refresh_digest(self):
        stats = hub_db.agent_stats()
        total_runs = stats.get("total_runs", 0)
        avg_score = float(stats.get("avg_score", 0.0) or 0.0)
        pending_todos = len(hub_db.list_todos(status="pending"))
        self.digest_total_card.value_label.configure(text=str(total_runs))
        self.digest_avg_card.value_label.configure(text=f"{avg_score:.2f}")
        self.digest_todo_card.value_label.configure(text=str(pending_todos))

        cached = hub_db.get_briefing_cache()
        recent_runs = hub_db.load_runs(limit=5)
        todo_rows = hub_db.list_todos(status="pending")[:5]
        lines = []
        if cached:
            content = cached.get("content") if isinstance(cached, dict) else str(cached)
            lines.append("LATEST BRIEFING")
            lines.append("=" * 70)
            lines.append(content or "(empty briefing)")
            lines.append("")
        lines.append("RUN SNAPSHOT")
        lines.append("=" * 70)
        if recent_runs:
            for row in recent_runs:
                lines.append(f"- {self._human_time(row.get('created_at'))} | {row.get('agent_id')} | {row.get('project')} | {row.get('graph')} | {row.get('status')} | score={float(row.get('score', 0.0) or 0.0):.2f}")
        else:
            lines.append("- No runs yet.")
        lines.append("")
        lines.append("PENDING TODOS")
        lines.append("=" * 70)
        if todo_rows:
            for todo in todo_rows:
                lines.append(f"- [{todo.get('priority')}] {todo.get('title')} ({todo.get('project')}) due {todo.get('due_date') or '—'}")
        else:
            lines.append("- No pending todos.")
        self._set_text(self.digest_text, "\n".join(lines))

    def _request_briefing(self):
        config = {
            "agent_id": "grants-research-agent",
            "project": "holdings",
            "graph": "research",
            "task": "Generate a concise daily briefing for ArchonHub: summarize active projects, pending todos, latest runs, and next priorities.",
            "max_revisions": 1,
        }
        self._run_agent(config)

    def _schedule_rows(self):
        rows = []
        for job_id, name, schedule_info, task in BUILT_IN_JOBS:
            schedule_text = ", ".join(f"{k}={v}" for k, v in schedule_info.items())
            rows.append(
                {
                    "id": job_id,
                    "agent_id": name,
                    "project": "system",
                    "schedule": f"🔒 {schedule_text}",
                    "next_fire": "built-in",
                    "status": "active",
                    "graph": "reflexion",
                    "task": task,
                    "run_type": "cron",
                    "built_in": True,
                }
            )
        for row in hub_db.list_scheduled_jobs():
            rows.append(
                {
                    "id": row["id"],
                    "agent_id": row.get("agent_id", ""),
                    "project": row.get("project", ""),
                    "schedule": row.get("cron_expr") or f"interval {row.get('interval_sec', 0)}s",
                    "next_fire": row.get("next_fire", ""),
                    "status": row.get("status", ""),
                    "graph": row.get("graph", "reflexion"),
                    "task": row.get("task", ""),
                    "run_type": row.get("run_type", "cron"),
                    "built_in": False,
                }
            )
        return rows

    def show_schedule(self):
        self._set_active_nav("Schedule")
        self._clear_content()
        self._section_header(self.content, "Schedule", f"Timezone: {TIMEZONE_NAME}")

        card = self._card(self.content, "")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        controls = tk.Frame(card, bg=BG_PANEL)
        controls.pack(fill="x", padx=14, pady=(0, 10))
        self._button(controls, "▶ Trigger", self._trigger_selected_job, accent=True).pack(side="left", padx=4)
        self._button(controls, "Delete", self._delete_selected_job).pack(side="left", padx=4)
        self._button(controls, "Refresh", self._refresh_schedule).pack(side="left", padx=4)

        columns = ("id", "agent_id", "project", "schedule", "next_fire", "status")
        self.schedule_tree = ttk.Treeview(card, columns=columns, show="headings", selectmode="browse")
        for column, text, width in (
            ("id", "ID", 170),
            ("agent_id", "Agent / Job", 220),
            ("project", "Project", 120),
            ("schedule", "Schedule", 220),
            ("next_fire", "Next Fire", 180),
            ("status", "Status", 100),
        ):
            self.schedule_tree.heading(column, text=text)
            self.schedule_tree.column(column, width=width, anchor="w")
        self.schedule_tree.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.schedule_tree.bind("<<TreeviewSelect>>", lambda _e: self._set_selected_job())

        add_card = self._card(card, "Add Job")
        add_card.pack(fill="x", padx=14, pady=(0, 14))
        form = tk.Frame(add_card, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 14))
        self.job_agent_var = tk.StringVar(value=[a for agents in AGENT_REGISTRY.values() for a in agents][0])
        self.job_project_var = tk.StringVar(value=PROJECTS[0])
        self.job_graph_var = tk.StringVar(value="reflexion")
        self.job_type_var = tk.StringVar(value="cron")
        self.job_schedule_var = tk.StringVar(value="0 7 * * *")
        tk.Label(form, text="Agent", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=4)
        self._combo(form, self.job_agent_var, [a for agents in AGENT_REGISTRY.values() for a in agents]).grid(row=1, column=0, sticky="ew")
        tk.Label(form, text="Project", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=4)
        self._combo(form, self.job_project_var, PROJECTS).grid(row=1, column=1, sticky="ew", padx=(10, 0))
        tk.Label(form, text="Graph", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        self._combo(form, self.job_graph_var, GRAPH_NAMES).grid(row=3, column=0, sticky="ew")
        tk.Label(form, text="Run Type", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)
        self._combo(form, self.job_type_var, ["cron", "interval"]).grid(row=3, column=1, sticky="ew", padx=(10, 0))
        tk.Label(form, text="Schedule", bg=BG_PANEL, fg=TEXT_BODY).grid(row=4, column=0, sticky="w", pady=4)
        self._entry(form, self.job_schedule_var).grid(row=5, column=0, columnspan=2, sticky="ew")
        tk.Label(form, text="Task", bg=BG_PANEL, fg=TEXT_BODY).grid(row=6, column=0, sticky="w", pady=4)
        self.job_task_text = self._text_widget(form, height=4)
        self.job_task_text.grid(row=7, column=0, columnspan=2, sticky="ew")
        self._button(form, "Add Job", self._add_job, accent=True).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        self._refresh_schedule()

    def _refresh_schedule(self):
        rows = self._schedule_rows()
        self.schedule_tree.delete(*self.schedule_tree.get_children())
        self.schedule_lookup = {}
        for row in rows:
            self.schedule_lookup[row["id"]] = row
            self.schedule_tree.insert("", "end", iid=row["id"], values=(row["id"], row["agent_id"], row["project"], row["schedule"], row["next_fire"], row["status"]), tags=(row["status"],))
        for tag, color in STATUS_COLORS.items():
            self.schedule_tree.tag_configure(tag, foreground=color)

    def _set_selected_job(self):
        selected = self.schedule_tree.selection()
        self.selected_job_id = selected[0] if selected else None

    def _add_job(self):
        task = self.job_task_text.get("1.0", "end").strip()
        if not task:
            self.show_toast("Task is required.", WARNING)
            return
        schedule = self.job_schedule_var.get().strip()
        run_type = self.job_type_var.get()
        kwargs = {
            "agent_id": self.job_agent_var.get(),
            "project": self.job_project_var.get(),
            "graph": self.job_graph_var.get(),
            "task": task,
            "run_type": run_type,
        }
        if run_type == "interval":
            kwargs["interval_sec"] = int(schedule or 3600)
        else:
            kwargs["cron_expr"] = schedule
        hub_db.create_scheduled_job(**kwargs)
        self.job_task_text.delete("1.0", "end")
        self.show_toast("Job added.", SUCCESS)
        self._refresh_schedule()

    def _trigger_selected_job(self):
        if not self.selected_job_id or self.selected_job_id not in self.schedule_lookup:
            return
        row = self.schedule_lookup[self.selected_job_id]
        self._run_agent(
            {
                "agent_id": row["agent_id"] if not row.get("built_in") else "finance-cfo",
                "project": row["project"] or "system",
                "graph": row.get("graph", "reflexion"),
                "task": row.get("task", f"Trigger scheduled job {row['id']}"),
                "max_revisions": 1,
            }
        )

    def _delete_selected_job(self):
        if not self.selected_job_id:
            return
        if self.selected_job_id in BUILT_IN_JOB_IDS:
            self.show_toast("Built-in jobs are locked.", WARNING)
            return
        hub_db.delete_scheduled_job(self.selected_job_id)
        self.selected_job_id = None
        self._refresh_schedule()

    def show_clients(self):
        self._set_active_nav("Clients")
        self._clear_content()
        self._section_header(self.content, "Clients", "Client relationships and service delivery.", actions=[("Add Client", self._open_client_dialog)])

        wrapper, _canvas, self.clients_cards_container = self._scrollable_area(self.content, bg=BG_CANVAS)
        wrapper.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._refresh_clients()

    def _refresh_clients(self):
        for child in self.clients_cards_container.winfo_children():
            child.destroy()
        clients = hub_db.list_clients()
        if not clients:
            tk.Label(self.clients_cards_container, text="No clients yet.", bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor="w", padx=10, pady=10)
            return
        for idx, client in enumerate(clients):
            card = tk.Frame(self.clients_cards_container, bg=BG_PANEL, highlightbackground=BORDER_CARD, highlightthickness=1)
            row, col = divmod(idx, 2)
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            self.clients_cards_container.grid_columnconfigure(col, weight=1)
            top = tk.Frame(card, bg=BG_PANEL)
            top.pack(fill="x", padx=14, pady=(14, 8))
            tk.Label(top, text=client.get("name", ""), bg=BG_PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "bold")).pack(side="left")
            self._status_badge(top, client.get("status", "active"), STATUS_COLORS.get(client.get("status", "active"), ACCENT)).pack(side="right")
            for label, value in (
                ("Business Type", client.get("business_type", "")),
                ("Service", client.get("service", "")),
                ("Contact", client.get("contact_name", "")),
                ("Email", client.get("contact_email", "")),
            ):
                row_frame = tk.Frame(card, bg=BG_PANEL)
                row_frame.pack(fill="x", padx=14, pady=2)
                tk.Label(row_frame, text=label, bg=BG_PANEL, fg=TEXT_MUTED, width=12, anchor="w").pack(side="left")
                tk.Label(row_frame, text=value or "—", bg=BG_PANEL, fg=TEXT_BODY, anchor="w").pack(side="left", fill="x", expand=True)
            buttons = tk.Frame(card, bg=BG_PANEL)
            buttons.pack(fill="x", padx=14, pady=(10, 14))
            self._button(buttons, "Edit", lambda c=client: self._open_client_dialog(c)).pack(side="left", padx=4)
            self._button(buttons, "Delete", lambda cid=client["id"]: self._delete_client(cid)).pack(side="left", padx=4)

    def _open_client_dialog(self, client=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Client")
        dialog.configure(bg=BG_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        fields = {
            "slug": tk.StringVar(value=client.get("slug", "") if client else ""),
            "name": tk.StringVar(value=client.get("name", "") if client else ""),
            "business_type": tk.StringVar(value=client.get("business_type", "") if client else ""),
            "service": tk.StringVar(value=client.get("service", "") if client else ""),
            "contact_name": tk.StringVar(value=client.get("contact_name", "") if client else ""),
            "contact_email": tk.StringVar(value=client.get("contact_email", "") if client else ""),
            "status": tk.StringVar(value=client.get("status", "active") if client else "active"),
            "project_slug": tk.StringVar(value=client.get("project_slug", "") if client else ""),
        }
        labels = [
            ("Slug", "slug"),
            ("Name", "name"),
            ("Business Type", "business_type"),
            ("Service", "service"),
            ("Contact Name", "contact_name"),
            ("Contact Email", "contact_email"),
            ("Status", "status"),
            ("Project", "project_slug"),
        ]
        for idx, (label, key) in enumerate(labels):
            tk.Label(dialog, text=label, bg=BG_PANEL, fg=TEXT_BODY).grid(row=idx * 2, column=0, sticky="w", padx=16, pady=(12 if idx == 0 else 6, 4))
            if key == "status":
                self._combo(dialog, fields[key], ["active", "on_hold", "prospect", "closed"]).grid(row=idx * 2 + 1, column=0, sticky="ew", padx=16)
            else:
                self._entry(dialog, fields[key]).grid(row=idx * 2 + 1, column=0, sticky="ew", padx=16)
        tk.Label(dialog, text="Notes", bg=BG_PANEL, fg=TEXT_BODY).grid(row=16, column=0, sticky="w", padx=16, pady=6)
        notes = self._text_widget(dialog, height=5)
        notes.grid(row=17, column=0, sticky="ew", padx=16)
        notes.insert("1.0", client.get("notes", "") if client else "")

        def _save():
            payload = {key: var.get().strip() for key, var in fields.items()}
            payload["notes"] = notes.get("1.0", "end").strip()
            if client:
                hub_db.update_client(client["id"], **payload)
            else:
                hub_db.create_client(**payload)
            dialog.destroy()
            self._refresh_clients()

        row = tk.Frame(dialog, bg=BG_PANEL)
        row.grid(row=18, column=0, sticky="e", padx=16, pady=16)
        self._button(row, "Cancel", dialog.destroy).pack(side="left", padx=4)
        self._button(row, "Save", _save, accent=True).pack(side="left", padx=4)
        dialog.grid_columnconfigure(0, weight=1)

    def _delete_client(self, client_id):
        hub_db.delete_client(client_id)
        self._refresh_clients()

    # ── Org Chart ─────────────────────────────────────────────────────────────

    def show_org(self):
        self._set_active_nav("Org")
        self._clear_content()
        try:
            from org_chart import OrgChartTab
        except Exception as e:
            tk.Label(self.content, text=f"Org chart failed to load:\n{e}",
                     bg=BG_CANVAS, fg=ERROR, font=("Segoe UI", 11)).pack(expand=True)
            return
        tab = OrgChartTab(self.content)
        tab.pack(fill="both", expand=True)

    # ── Markets ───────────────────────────────────────────────────────────────

    def show_markets(self):
        self._set_active_nav("Markets")
        self._clear_content()
        try:
            from markets_tab import MarketsTab
        except Exception as e:
            tk.Label(self.content, text=f"Markets tab failed to load:\n{e}",
                     bg=BG_CANVAS, fg=ERROR, font=("Segoe UI", 11)).pack(expand=True)
            return
        tab = MarketsTab(self.content)
        tab.pack(fill="both", expand=True)
        self._markets_tab = tab
        tab.start_feed()

    # ── Reports ───────────────────────────────────────────────────────────────

    def show_reports(self):
        self._set_active_nav("Reports")
        self._clear_content()
        self._section_header(
            self.content, "Reports", "Daily briefings, research, and automation reports.",
            actions=[
                ("Run Briefing", lambda: self._run_report_job("daily_briefing")),
                ("Run Reflexion", lambda: self._run_report_job("daily_reflexion")),
            ],
        )
        # Filter bar
        filter_bar = tk.Frame(self.content, bg=BG_CANVAS)
        filter_bar.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(filter_bar, text="Type:", bg=BG_CANVAS, fg=TEXT_BODY,
                 font=("Segoe UI", 10)).pack(side="left")
        self._report_filter_var = tk.StringVar(value="all")
        types = ["all", "briefing", "reflexion", "research", "travel", "operations",
                 "automation", "project_status"]
        combo = self._combo(filter_bar, self._report_filter_var, types)
        combo.pack(side="left", padx=(6, 16))
        self._button(filter_bar, "🔄 Refresh", self._refresh_reports).pack(side="left")

        wrapper, _canvas, self.reports_container = self._scrollable_area(self.content, bg=BG_CANVAS)
        wrapper.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Detail pane below
        self.report_detail_frame = tk.Frame(self.content, bg=BG_PANEL,
                                            highlightbackground=BORDER_CARD, highlightthickness=1)
        self.report_detail_frame.pack(fill="x", padx=20, pady=(0, 16))
        self.report_detail_text = None

        self._refresh_reports()

    def _refresh_reports(self):
        if not hasattr(self, "reports_container"):
            return
        try:
            if not self.reports_container.winfo_exists():
                return
        except Exception:
            return
        for child in self.reports_container.winfo_children():
            child.destroy()

        rtype = getattr(self, "_report_filter_var", None)
        filter_val = rtype.get() if rtype else "all"
        try:
            reports = hub_db.list_reports(
                report_type=None if filter_val == "all" else filter_val,
                limit=80,
            )
        except Exception:
            reports = []

        if not reports:
            tk.Label(self.reports_container, text="No reports yet. Reports are generated daily by the scheduler.",
                     bg=BG_CANVAS, fg=TEXT_MUTED, wraplength=700).pack(anchor="w", padx=10, pady=20)
            return

        # Group by report_type for visual separation
        from collections import defaultdict
        by_type: dict = defaultdict(list)
        for r in reports:
            by_type[r.get("report_type", "other")].append(r)

        TYPE_EMOJI = {
            "briefing":      "🌅",
            "reflexion":     "🔄",
            "research":      "🔬",
            "travel":        "✈",
            "operations":    "⚙️",
            "automation":    "⚡",
            "project_status":"📋",
            "daily":         "📰",
        }

        STATUS_BADGE = {
            "complete":   ("#00C864", "✓ Complete"),
            "generating": (ACCENT,    "⏳ Generating"),
            "partial":    ("#F5A623", "⚠ Partial"),
            "failed":     (ERROR,     "✗ Failed"),
        }

        for rtype_key, rtype_reports in sorted(by_type.items()):
            emoji = TYPE_EMOJI.get(rtype_key, "📄")
            header = tk.Label(
                self.reports_container,
                text=f"{emoji}  {rtype_key.replace('_', ' ').title()} ({len(rtype_reports)})",
                bg=BG_CANVAS, fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold"),
            )
            header.pack(anchor="w", padx=10, pady=(14, 4))

            for report in rtype_reports:
                self._render_report_card(report, STATUS_BADGE)

    def _render_report_card(self, report: dict, status_badge: dict):
        card = tk.Frame(self.reports_container, bg=BG_PANEL,
                        highlightbackground=BORDER_CARD, highlightthickness=1)
        card.pack(fill="x", padx=10, pady=4)

        top = tk.Frame(card, bg=BG_PANEL)
        top.pack(fill="x", padx=14, pady=(10, 4))

        tk.Label(top, text=report.get("title", "Untitled Report"),
                 bg=BG_PANEL, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        status = report.get("status", "complete")
        badge_color, badge_text = status_badge.get(status, (ACCENT, status))
        self._status_badge(top, badge_text, badge_color).pack(side="right")

        # Meta row
        gen_at = report.get("generated_at", "")[:16].replace("T", " ")
        by = report.get("generated_by", "")[:40]
        project = report.get("project_slug", "")
        meta_parts = [p for p in [gen_at, f"by {by}" if by else "", project] if p]
        tk.Label(card, text="  •  ".join(meta_parts),
                 bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14)

        # Summary
        summary = report.get("summary", "")
        if summary and summary != "Generating..." and summary != "Running...":
            tk.Label(card, text=summary, bg=BG_PANEL, fg=TEXT_BODY,
                     wraplength=900, justify="left",
                     font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(4, 2))

        # Action buttons
        btn_row = tk.Frame(card, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=14, pady=(6, 10))
        self._button(btn_row, "View Full Report",
                     lambda r=report: self._view_report(r)).pack(side="left", padx=4)
        job_id = report.get("job_id", "")
        if job_id:
            self._button(btn_row, "Re-run",
                         lambda j=job_id: self._run_report_job(j)).pack(side="left", padx=4)
        self._button(btn_row, "Delete",
                     lambda rid=report["id"]: self._delete_report(rid)).pack(side="left", padx=4)

    def _view_report(self, report: dict):
        """Open report content in a scrollable popup."""
        dialog = tk.Toplevel(self.root)
        dialog.title(report.get("title", "Report"))
        dialog.configure(bg=BG_PANEL)
        dialog.geometry("900x700")
        dialog.transient(self.root)

        header = tk.Frame(dialog, bg=BG_PANEL)
        header.pack(fill="x", padx=16, pady=(12, 0))
        tk.Label(header, text=report.get("title",""), bg=BG_PANEL,
                 fg=TEXT_PRIMARY, font=("Segoe UI", 13, "bold")).pack(side="left")

        gen_at = report.get("generated_at","")[:16].replace("T"," ")
        tk.Label(header, text=gen_at, bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="right")

        tk.Frame(dialog, bg=BORDER_CARD, height=1).pack(fill="x", padx=16, pady=8)

        text_frame = tk.Frame(dialog, bg=BG_PANEL)
        text_frame.pack(fill="both", expand=True, padx=16, pady=(0,12))
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        txt = tk.Text(text_frame, bg=BG_CANVAS, fg=TEXT_BODY,
                      font=("Consolas", 10), relief="flat", wrap="word",
                      yscrollcommand=scrollbar.set, padx=12, pady=8)
        txt.pack(fill="both", expand=True)
        scrollbar.config(command=txt.yview)
        content = report.get("content","") or report.get("summary","No content available.")
        txt.insert("1.0", content)
        txt.configure(state="disabled")

        self._button(dialog, "Close", dialog.destroy, accent=True).pack(pady=(0,12))

    def _run_report_job(self, job_id: str):
        """Trigger a report job immediately — calls report_monitor directly (no HTTP auth needed)."""
        def _do():
            try:
                from report_monitor import run_report_job_sync
                run_report_job_sync(job_id)
                self._ui_queue.put(("notification", f"Report '{job_id}' complete", SUCCESS))
                self.root.after(2000, self._refresh_reports)
            except Exception as e:
                self._ui_queue.put(("notification", f"Report job failed: {e}", ERROR))
        threading.Thread(target=_do, daemon=True).start()

    def _delete_report(self, report_id: str):
        hub_db.delete_report(report_id)
        self._refresh_reports()

    # ── Travel ────────────────────────────────────────────────────────────────

    def show_travel(self):
        self._set_active_nav("Travel")
        self._clear_content()
        self._section_header(self.content, "Travel", "Trips, status, and budget tracking.", actions=[("Add Trip", self._open_trip_dialog)])
        wrapper, _canvas, self.travel_cards_container = self._scrollable_area(self.content, bg=BG_CANVAS)
        wrapper.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._refresh_travel()

    def _refresh_travel(self):
        for child in self.travel_cards_container.winfo_children():
            child.destroy()
        trips = self.hub.list_trips()
        if not trips:
            tk.Label(self.travel_cards_container, text="No trips yet.", bg=BG_CANVAS, fg=TEXT_MUTED).pack(anchor="w", padx=10, pady=10)
            return
        for idx, trip in enumerate(trips):
            card = tk.Frame(self.travel_cards_container, bg=BG_PANEL, highlightbackground=BORDER_CARD, highlightthickness=1)
            card.pack(fill="x", padx=10, pady=10)
            top = tk.Frame(card, bg=BG_PANEL)
            top.pack(fill="x", padx=14, pady=(14, 8))
            tk.Label(top, text=trip.get("name", ""), bg=BG_PANEL, fg=TEXT_PRIMARY, font=("Segoe UI", 12, "bold")).pack(side="left")
            self._status_badge(top, trip.get("status", "planning"), STATUS_COLORS.get(trip.get("status", "planning"), ACCENT)).pack(side="right")
            tk.Label(card, text=f"{trip.get('destination', '')} • {trip.get('depart_date', '—')} → {trip.get('return_date', '—')}", bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=14)
            budget = float(trip.get("budget", 0) or 0)
            spent = float(trip.get("spent", 0) or 0)
            pct = min(100, int((spent / budget) * 100)) if budget > 0 else 0
            tk.Label(card, text=f"Budget ${budget:,.0f} • Spent ${spent:,.0f}", bg=BG_PANEL, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(8, 2))
            bar = ttk.Progressbar(card, style="Accent.Horizontal.TProgressbar", maximum=100, value=pct)
            bar.pack(fill="x", padx=14)
            if trip.get("notes"):
                tk.Label(card, text=trip.get("notes"), bg=BG_PANEL, fg=TEXT_BODY, wraplength=900, justify="left").pack(anchor="w", padx=14, pady=(8, 4))
            actions = tk.Frame(card, bg=BG_PANEL)
            actions.pack(fill="x", padx=14, pady=(8, 14))
            self._button(actions, "Edit", lambda t=trip: self._open_trip_dialog(t)).pack(side="left", padx=4)
            self._button(actions, "Delete", lambda tid=trip["id"]: self._delete_trip(tid)).pack(side="left", padx=4)

    def _open_trip_dialog(self, trip=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Trip")
        dialog.configure(bg=BG_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()
        fields = {
            "name": tk.StringVar(value=trip.get("name", "") if trip else ""),
            "destination": tk.StringVar(value=trip.get("destination", "") if trip else ""),
            "depart_date": tk.StringVar(value=trip.get("depart_date", "") if trip else ""),
            "return_date": tk.StringVar(value=trip.get("return_date", "") if trip else ""),
            "status": tk.StringVar(value=trip.get("status", "planning") if trip else "planning"),
            "budget": tk.StringVar(value=str(trip.get("budget", 0) if trip else 0)),
            "spent": tk.StringVar(value=str(trip.get("spent", 0) if trip else 0)),
        }
        row = 0
        for label, key in (("Name", "name"), ("Destination", "destination"), ("Depart Date", "depart_date"), ("Return Date", "return_date"), ("Status", "status"), ("Budget", "budget"), ("Spent", "spent")):
            tk.Label(dialog, text=label, bg=BG_PANEL, fg=TEXT_BODY).grid(row=row, column=0, sticky="w", padx=16, pady=(12 if row == 0 else 6, 4))
            if key == "status":
                self._combo(dialog, fields[key], ["planning", "booked", "in_progress", "complete"]).grid(row=row + 1, column=0, sticky="ew", padx=16)
            else:
                self._entry(dialog, fields[key]).grid(row=row + 1, column=0, sticky="ew", padx=16)
            row += 2
        tk.Label(dialog, text="Notes", bg=BG_PANEL, fg=TEXT_BODY).grid(row=row, column=0, sticky="w", padx=16, pady=6)
        notes = self._text_widget(dialog, height=5)
        notes.grid(row=row + 1, column=0, sticky="ew", padx=16)
        notes.insert("1.0", trip.get("notes", "") if trip else "")

        def _save():
            payload = {
                "name": fields["name"].get().strip(),
                "destination": fields["destination"].get().strip(),
                "depart_date": fields["depart_date"].get().strip(),
                "return_date": fields["return_date"].get().strip(),
                "status": fields["status"].get().strip(),
                "budget": float(fields["budget"].get() or 0),
                "spent": float(fields["spent"].get() or 0),
                "notes": notes.get("1.0", "end").strip(),
            }
            if trip:
                self.hub.update_trip(trip["id"], **payload)
            else:
                self.hub.create_trip(**payload)
            dialog.destroy()
            self._refresh_travel()

        button_row = tk.Frame(dialog, bg=BG_PANEL)
        button_row.grid(row=row + 2, column=0, sticky="e", padx=16, pady=16)
        self._button(button_row, "Cancel", dialog.destroy).pack(side="left", padx=4)
        self._button(button_row, "Save", _save, accent=True).pack(side="left", padx=4)
        dialog.grid_columnconfigure(0, weight=1)

    def _delete_trip(self, trip_id):
        self.hub.delete_trip(trip_id)
        self._refresh_travel()

    def show_connectors(self):
        self._set_active_nav("Connect")
        self._clear_content()
        self._section_header(self.content, "Email Connectors", "Manage Gmail, Outlook, and IMAP accounts.")

        paned = tk.PanedWindow(self.content, orient="horizontal", sashwidth=6, bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        left = tk.Frame(paned, bg=BG_CANVAS, width=540)
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(left, minsize=500)
        paned.add(right, minsize=360)

        # ── Left: Account List ────────────────────────────────────────────
        list_card = self._card(left, "Connected Accounts")
        list_card.pack(fill="both", expand=True)

        columns = ("label", "email", "provider", "auth", "status")
        self.connectors_tree = ttk.Treeview(list_card, columns=columns, show="headings", selectmode="browse", height=14)
        for col, text, width in (
            ("label",    "Label",    140),
            ("email",    "Email",    200),
            ("provider", "Provider",  90),
            ("auth",     "Auth",      90),
            ("status",   "Status",   100),
        ):
            self.connectors_tree.heading(col, text=text)
            self.connectors_tree.column(col, width=width, anchor="w")
        vsb = ttk.Scrollbar(list_card, orient="vertical", command=self.connectors_tree.yview)
        self.connectors_tree.configure(yscrollcommand=vsb.set)
        self.connectors_tree.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=(0, 10))
        vsb.pack(side="left", fill="y", pady=(0, 10), padx=(0, 6))
        self.connectors_tree.bind("<<TreeviewSelect>>", self._on_connector_select)

        action_bar = tk.Frame(list_card, bg=BG_PANEL)
        action_bar.pack(fill="x", padx=14, pady=(0, 14))
        self._button(action_bar, "🔌 Test",     self._test_selected_connector, accent=True).pack(side="left", padx=4)
        self._button(action_bar, "🔄 Re-Auth",  self._reauth_selected_connector).pack(side="left", padx=4)
        self._button(action_bar, "🗑 Delete",   self._delete_selected_connector).pack(side="left", padx=4)
        self._button(action_bar, "↻ Refresh",   self._refresh_connectors).pack(side="right", padx=4)

        # ── Right: Notebook (Add / Details) ──────────────────────────────
        right_nb = ttk.Notebook(right, style="Dark.TNotebook")
        right_nb.pack(fill="both", expand=True)

        add_frame = tk.Frame(right_nb, bg=BG_PANEL)
        detail_frame = tk.Frame(right_nb, bg=BG_PANEL)
        right_nb.add(add_frame,    text="  ➕ Add Account  ")
        right_nb.add(detail_frame, text="  🔍 Details  ")

        # ── Add Account tab ──────────────────────────────────────────────
        self._connector_vars = {
            "label":              tk.StringVar(),
            "email_address":      tk.StringVar(),
            "provider":           tk.StringVar(value="gmail"),
            "oauth_client_id":    tk.StringVar(),
            "oauth_client_secret":tk.StringVar(),
            "imap_host":          tk.StringVar(),
            "imap_port":          tk.StringVar(value="993"),
            "smtp_host":          tk.StringVar(),
            "smtp_port":          tk.StringVar(value="587"),
            "username":           tk.StringVar(),
            "password":           tk.StringVar(),
        }

        add_scroll = tk.Frame(add_frame, bg=BG_PANEL)
        add_scroll.pack(fill="both", expand=True, padx=14, pady=12)

        # Static top fields
        for lbl, key in [("Label *", "label"), ("Email Address *", "email_address")]:
            tk.Label(add_scroll, text=lbl, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
            self._entry(add_scroll, self._connector_vars[key]).pack(fill="x")

        tk.Label(add_scroll, text="Provider *", bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
        provider_combo = self._combo(add_scroll, self._connector_vars["provider"],
                                     ["gmail", "outlook", "imap", "zoho", "yahoo"])
        provider_combo.pack(fill="x")

        # Dynamic section — rebuilt on provider change
        self._connector_dyn_frame = tk.Frame(add_scroll, bg=BG_PANEL)
        self._connector_dyn_frame.pack(fill="x")
        self._connector_add_btn_frame = tk.Frame(add_scroll, bg=BG_PANEL)
        self._connector_add_btn_frame.pack(fill="x", pady=(12, 0))

        self._connector_vars["provider"].trace_add("write", lambda *_: self._rebuild_connector_form())
        self._rebuild_connector_form()

        # ── Details tab ──────────────────────────────────────────────────
        self._connector_detail_vars = {
            "label":    tk.StringVar(value="—"),
            "email":    tk.StringVar(value="—"),
            "provider": tk.StringVar(value="—"),
            "auth":     tk.StringVar(value="—"),
            "status":   tk.StringVar(value="—"),
            "token":    tk.StringVar(value="—"),
            "synced":   tk.StringVar(value="—"),
            "error":    tk.StringVar(value=""),
        }
        self._connector_selected_id = None

        det = detail_frame
        for label, key in [
            ("Label",          "label"),
            ("Email",          "email"),
            ("Provider",       "provider"),
            ("Auth Type",      "auth"),
            ("Status",         "status"),
            ("Token / Auth",   "token"),
            ("Last Synced",    "synced"),
        ]:
            tk.Label(det, text=label, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(8, 2))
            tk.Label(det, textvariable=self._connector_detail_vars[key],
                     bg=BG_PANEL, fg=TEXT_BODY, font=("Segoe UI", 10, "bold"), wraplength=280, justify="left").pack(anchor="w", padx=14)

        tk.Label(det, text="Last Error", bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(8, 2))
        self._connector_err_label = tk.Label(det, textvariable=self._connector_detail_vars["error"],
                                              bg=BG_PANEL, fg=ERROR, font=("Segoe UI", 9), wraplength=280, justify="left")
        self._connector_err_label.pack(anchor="w", padx=14)

        det_btns = tk.Frame(det, bg=BG_PANEL)
        det_btns.pack(anchor="w", padx=14, pady=(16, 0))
        self._button(det_btns, "🔌 Test Connection", self._test_selected_connector, accent=True).pack(side="left", padx=(0, 8))
        self._button(det_btns, "🔄 Re-Authorize",    self._reauth_selected_connector).pack(side="left")

        self._right_nb_connectors = right_nb
        self._refresh_connectors()

    # ── OAuth presets ────────────────────────────────────────────────────

    _PROVIDER_PRESETS = {
        "gmail":   {"imap_host": "imap.gmail.com",          "imap_port": "993",
                    "smtp_host": "smtp.gmail.com",           "smtp_port": "587", "oauth": True},
        "outlook": {"imap_host": "outlook.office365.com",   "imap_port": "993",
                    "smtp_host": "smtp.office365.com",       "smtp_port": "587", "oauth": True},
        "imap":    {"imap_host": "",    "imap_port": "993",
                    "smtp_host": "",    "smtp_port": "587",  "oauth": False},
        "zoho":    {"imap_host": "imap.zoho.com",            "imap_port": "993",
                    "smtp_host": "smtp.zoho.com",            "smtp_port": "587", "oauth": False},
        "yahoo":   {"imap_host": "imap.mail.yahoo.com",      "imap_port": "993",
                    "smtp_host": "smtp.mail.yahoo.com",      "smtp_port": "587", "oauth": False},
    }

    def _rebuild_connector_form(self):
        """Destroy and rebuild the dynamic form section based on selected provider."""
        for w in self._connector_dyn_frame.winfo_children():
            w.destroy()
        for w in self._connector_add_btn_frame.winfo_children():
            w.destroy()

        provider = self._connector_vars["provider"].get()
        preset = self._PROVIDER_PRESETS.get(provider, self._PROVIDER_PRESETS["imap"])

        # Apply host/port presets
        self._connector_vars["imap_host"].set(preset["imap_host"])
        self._connector_vars["imap_port"].set(preset["imap_port"])
        self._connector_vars["smtp_host"].set(preset["smtp_host"])
        self._connector_vars["smtp_port"].set(preset["smtp_port"])

        f = self._connector_dyn_frame

        if preset["oauth"]:
            # ── OAuth2 mode ──────────────────────────────────────────────
            provider_name = "Google" if provider == "gmail" else "Microsoft"
            note = (
                f"Authorize ArchonHub to access your {provider_name} account via OAuth2.\n"
                f"You need a {'Google Cloud' if provider == 'gmail' else 'Azure App'} Client ID & Secret."
            )
            tk.Label(f, text=note, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9),
                     wraplength=280, justify="left").pack(anchor="w", pady=(10, 6))

            for lbl, key in [("Client ID *", "oauth_client_id"), ("Client Secret *", "oauth_client_secret")]:
                tk.Label(f, text=lbl, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 2))
                show = "*" if "secret" in key else None
                self._entry(f, self._connector_vars[key], show=show).pack(fill="x")

            # Help link
            help_url = (
                "https://console.cloud.google.com/apis/credentials"
                if provider == "gmail"
                else "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps"
            )
            lnk = tk.Label(f, text=f"📋 Open {provider_name} Console →", bg=BG_PANEL,
                           fg=ACCENT, font=("Segoe UI", 9, "underline"), cursor="hand2")
            lnk.pack(anchor="w", pady=(4, 0))
            lnk.bind("<Button-1>", lambda _e: webbrowser.open(help_url))

            redirect_note = tk.Label(
                f,
                text=f"Redirect URI:  http://localhost:8765/api/connectors/oauth/{provider}/callback",
                bg=BG_PANEL, fg="#6b7a99", font=("Segoe UI", 8),
            )
            redirect_note.pack(anchor="w", pady=(2, 8))

            # Authorize button
            btn_label = f"🔐 Authorize with {provider_name}"
            self._button(self._connector_add_btn_frame, btn_label,
                         lambda p=provider: self._create_and_authorize(p), accent=True).pack(fill="x")

        else:
            # ── Password mode ────────────────────────────────────────────
            for lbl, key, show in [
                ("IMAP Host",  "imap_host",  None),
                ("IMAP Port",  "imap_port",  None),
                ("SMTP Host",  "smtp_host",  None),
                ("SMTP Port",  "smtp_port",  None),
                ("Username",   "username",   None),
                ("Password",   "password",   "*"),
            ]:
                tk.Label(f, text=lbl, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 2))
                self._entry(f, self._connector_vars[key], show=show).pack(fill="x")

            self._button(self._connector_add_btn_frame, "➕ Add Connector",
                         self._add_password_connector, accent=True).pack(fill="x")

    def _create_and_authorize(self, provider: str):
        """Save connector then open browser for OAuth authorization."""
        data = {k: v.get().strip() for k, v in self._connector_vars.items()}
        if not data["label"] or not data["email_address"]:
            self.show_toast("Label and email are required.", WARNING)
            return
        if not data["oauth_client_id"] or not data["oauth_client_secret"]:
            self.show_toast("Client ID and Client Secret are required for OAuth.", WARNING)
            return

        preset = self._PROVIDER_PRESETS.get(provider, {})
        connector = hub_db.create_connector(
            label=data["label"],
            email_address=data["email_address"],
            provider=provider,
            auth_type="oauth2",
            imap_host=preset.get("imap_host", ""),
            imap_port=int(preset.get("imap_port", 993)),
            smtp_host=preset.get("smtp_host", ""),
            smtp_port=int(preset.get("smtp_port", 587)),
            username=data["email_address"],
            oauth_client_id=data["oauth_client_id"],
            oauth_client_secret=data["oauth_client_secret"],
        )
        connector_id = connector["id"]
        self._refresh_connectors()
        self.show_toast(f"Connector created — opening browser for authorization…", ACCENT)
        self._start_oauth_flow(connector_id, provider)

    def _add_password_connector(self):
        """Save a plain-password IMAP connector."""
        data = {k: v.get().strip() for k, v in self._connector_vars.items()}
        if not data["label"] or not data["email_address"]:
            self.show_toast("Label and email are required.", WARNING)
            return
        hub_db.create_connector(
            label=data["label"],
            email_address=data["email_address"],
            provider=data["provider"],
            auth_type="password",
            imap_host=data["imap_host"],
            imap_port=int(data["imap_port"] or 993),
            smtp_host=data["smtp_host"],
            smtp_port=int(data["smtp_port"] or 587),
            username=data["username"],
            credentials={"password": data["password"]},
        )
        # Clear form
        for key, var in self._connector_vars.items():
            if key not in ("provider",):
                var.set("")
        self._refresh_connectors()
        self.show_toast("Connector added.", SUCCESS)

    def _start_oauth_flow(self, connector_id: str, provider: str):
        """Call hub server to get OAuth URL, open browser, then poll for completion."""
        import urllib.request as _ur
        import json as _json

        def _do():
            try:
                # Fetch auth URL from hub server (requires server running on 8765)
                url = f"http://localhost:8765/api/connectors/oauth/{provider}/init?connector_id={connector_id}"
                # We need an auth header — re-use saved token if available
                req = _ur.Request(url, headers={"Accept": "application/json"})
                token = getattr(self, "_hub_token", None)
                if token:
                    req.add_header("Authorization", f"Bearer {token}")
                try:
                    with _ur.urlopen(req, timeout=8) as resp:
                        payload = _json.loads(resp.read())
                    auth_url = payload.get("auth_url", "")
                except Exception:
                    # Hub may not be running — fall back to building URL directly
                    auth_url = self._build_local_oauth_url(connector_id, provider)

                if not auth_url:
                    self._ui_queue.put(("toast", "Could not get OAuth URL. Is the Hub server running?", WARNING))
                    return

                webbrowser.open(auth_url)
                self._ui_queue.put(("toast", "Browser opened — complete authorization, then return here.", ACCENT))

                # Poll for up to 2 minutes
                for _ in range(60):
                    import time as _t
                    _t.sleep(2)
                    fresh = hub_db.get_connector(connector_id)
                    if fresh and fresh.get("status") == "active":
                        self._ui_queue.put(("toast", f"✅ {fresh.get('email_address', '')} authorized!", SUCCESS))
                        self._ui_queue.put(("refresh_connectors",))
                        return
                self._ui_queue.put(("toast", "Authorization timed out. Check connector status.", WARNING))
                self._ui_queue.put(("refresh_connectors",))
            except Exception as exc:
                self._ui_queue.put(("toast", f"OAuth flow error: {exc}", ERROR))

        threading.Thread(target=_do, daemon=True).start()

    def _build_local_oauth_url(self, connector_id: str, provider: str) -> str:
        """Build OAuth URL directly using oauth_connector module (hub server fallback)."""
        try:
            connector = hub_db.get_connector(connector_id)
            if not connector:
                return ""
            client_id  = connector.get("oauth_client_id", "")
            client_sec = connector.get("oauth_client_secret", "")
            if provider == "gmail":
                from oauth_connector import GoogleOAuth, store_pending_state
                g = GoogleOAuth(client_id, client_sec, connector_id)
                url, state, verifier = g.get_authorization_url()
                store_pending_state(state, connector_id, "google", verifier)
                return url
            else:
                from oauth_connector import MicrosoftOAuth, store_pending_state
                m = MicrosoftOAuth(client_id, client_sec, connector_id)
                url, state = m.get_authorization_url()
                store_pending_state(state, connector_id, "microsoft")
                return url
        except Exception:
            return ""

    def _reauth_selected_connector(self):
        """Re-run OAuth for the selected connector."""
        if not self._connector_selected_id:
            self.show_toast("Select a connector first.", WARNING)
            return
        connector = hub_db.get_connector(self._connector_selected_id)
        if not connector:
            return
        provider = connector.get("provider", "")
        if provider not in ("gmail", "outlook"):
            self.show_toast("Re-authorization is only for OAuth connectors.", WARNING)
            return
        self.show_toast("Opening browser for re-authorization…", ACCENT)
        self._start_oauth_flow(self._connector_selected_id, provider)

    def _refresh_connectors(self):
        import time as _t
        rows = hub_db.list_connectors()
        self.connectors_tree.delete(*self.connectors_tree.get_children())
        self._connector_lookup = {}
        now_ts = _t.time()
        for row in rows:
            cid = row["id"]
            self._connector_lookup[cid] = row
            provider  = row.get("provider", "")
            auth_type = row.get("auth_type", "password")
            status    = row.get("status", "pending")

            # Compute display auth label + token status badge
            if auth_type == "oauth2":
                exp_str = row.get("token_expires_at", "")
                if exp_str and exp_str.isdigit():
                    exp_ts = int(exp_str)
                    if exp_ts < now_ts:
                        auth_display = "⚠️ expired"
                        if status == "active":
                            status = "token_expired"
                    else:
                        hours_left = (exp_ts - now_ts) / 3600
                        auth_display = f"🔑 OAuth2 ({hours_left:.0f}h)"
                else:
                    auth_display = "🔑 OAuth2"
            else:
                auth_display = "🔒 password"

            status_tag = status
            self.connectors_tree.insert(
                "", "end", iid=cid,
                values=(row.get("label", ""), row.get("email_address", ""),
                        provider, auth_display, status),
                tags=(status_tag,),
            )

        for tag, color in {
            **STATUS_COLORS,
            "active":        SUCCESS,
            "token_expired": WARNING,
            "error":         ERROR,
            "pending":       TEXT_MUTED,
        }.items():
            self.connectors_tree.tag_configure(tag, foreground=color)

        # Refresh detail panel if something is selected
        if self._connector_selected_id and self._connector_selected_id in self._connector_lookup:
            self._load_connector_detail(self._connector_lookup[self._connector_selected_id])

    def _on_connector_select(self, _event=None):
        sel = self.connectors_tree.selection()
        self._connector_selected_id = sel[0] if sel else None
        if self._connector_selected_id and self._connector_selected_id in self._connector_lookup:
            self._load_connector_detail(self._connector_lookup[self._connector_selected_id])
            # Switch to details tab
            if hasattr(self, "_right_nb_connectors"):
                self._right_nb_connectors.select(1)

    def _load_connector_detail(self, row: dict):
        import time as _t
        now_ts = _t.time()
        auth_type = row.get("auth_type", "password")
        exp_str   = row.get("token_expires_at", "")

        if auth_type == "oauth2" and exp_str and exp_str.isdigit():
            exp_ts = int(exp_str)
            if exp_ts < now_ts:
                token_disp = "⚠️ Token expired — re-authorize required"
            else:
                left_secs = exp_ts - now_ts
                h = int(left_secs // 3600)
                m = int((left_secs % 3600) // 60)
                token_disp = f"🔑 Valid — expires in {h}h {m}m"
        elif auth_type == "oauth2":
            token_disp = "🔒 Not yet authorized"
        else:
            token_disp = "🔒 Password auth"

        synced = row.get("last_synced") or "Never"
        if synced != "Never":
            try:
                synced = datetime.fromisoformat(synced).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        self._connector_detail_vars["label"].set(row.get("label", "—"))
        self._connector_detail_vars["email"].set(row.get("email_address", "—"))
        self._connector_detail_vars["provider"].set(row.get("provider", "—"))
        self._connector_detail_vars["auth"].set(auth_type)
        self._connector_detail_vars["status"].set(row.get("status", "—"))
        self._connector_detail_vars["token"].set(token_disp)
        self._connector_detail_vars["synced"].set(synced)
        self._connector_detail_vars["error"].set(row.get("last_error") or "")

    # backward compat alias (used by _ui_queue handler)
    def _set_selected_connector(self):
        self._on_connector_select()

    def _test_selected_connector(self):
        if not self._connector_selected_id or self._connector_selected_id not in self._connector_lookup:
            self.show_toast("Select a connector first.", WARNING)
            return
        connector = self._connector_lookup[self._connector_selected_id]

        def _thread():
            try:
                from oauth_connector import test_connector as _tc
                ok, msg = _tc(connector)
            except Exception as exc:
                ok, msg = False, str(exc)

            hub_db.update_connector(
                self._connector_selected_id,
                status="active" if ok else "error",
                last_error="" if ok else msg,
                last_synced=datetime.now().isoformat() if ok else None,
            )
            color = SUCCESS if ok else ERROR
            self._ui_queue.put(("toast", f"{'✅' if ok else '❌'} {msg}", color))
            self._ui_queue.put(("refresh_connectors",))

        threading.Thread(target=_thread, daemon=True).start()

    def _delete_selected_connector(self):
        if self._connector_selected_id:
            hub_db.delete_connector(self._connector_selected_id)
            self._connector_selected_id = None
            self._refresh_connectors()
            self.show_toast("Connector deleted.", SUCCESS)


    def show_admin(self):
        if not self.admin_unlocked:
            self.ask_pin(self._unlock_admin)
            return
        self._render_admin()

    def _unlock_admin(self):
        self.admin_unlocked = True
        self._render_admin()

    def _render_admin(self):
        self._set_active_nav("Admin")
        self._clear_content()
        self._section_header(self.content, "Admin", "Protected controls, users, config, scheduler, and logs.")
        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        hub_tab = tk.Frame(notebook, bg=BG_CANVAS)
        config_tab = tk.Frame(notebook, bg=BG_CANVAS)
        users_tab = tk.Frame(notebook, bg=BG_CANVAS)
        scheduler_tab = tk.Frame(notebook, bg=BG_CANVAS)
        logs_tab = tk.Frame(notebook, bg=BG_CANVAS)
        notebook.add(hub_tab, text="Hub Control")
        notebook.add(config_tab, text="Config")
        notebook.add(users_tab, text="Users")
        notebook.add(scheduler_tab, text="Scheduler")
        notebook.add(logs_tab, text="Logs")

        self._build_admin_hub_tab(hub_tab)
        self._build_admin_config_tab(config_tab)
        self._build_admin_users_tab(users_tab)
        self._build_admin_scheduler_tab(scheduler_tab)
        self._build_admin_logs_tab(logs_tab)

    def _build_admin_hub_tab(self, parent):
        card = self._card(parent, "Hub Control")
        card.pack(fill="both", expand=True, padx=10, pady=10)
        health = {}
        try:
            if hasattr(self.hub, "get_health"):
                health = self.hub.get_health() or {}
        except Exception:
            health = {}
        info = tk.Frame(card, bg=BG_PANEL)
        info.pack(fill="x", padx=14, pady=(0, 14))
        rows = [
            ("Status", "online" if getattr(self.hub, "online", False) else "offline"),
            ("Port", str(health.get("port", 8765))),
            ("PID", str(health.get("pid", "n/a"))),
            ("Mode", str(health.get("mode", "desktop"))),
        ]
        for idx, (label, value) in enumerate(rows):
            tk.Label(info, text=label, bg=BG_PANEL, fg=TEXT_MUTED).grid(row=idx, column=0, sticky="w", pady=4)
            tk.Label(info, text=value, bg=BG_PANEL, fg=TEXT_PRIMARY).grid(row=idx, column=1, sticky="w", pady=4, padx=(12, 0))
        buttons = tk.Frame(card, bg=BG_PANEL)
        buttons.pack(fill="x", padx=14, pady=(0, 14))
        self._button(buttons, "Start Hub", self._start_hub_server, accent=True).pack(side="left", padx=4)
        self._button(buttons, "Stop Hub", self._stop_hub_server).pack(side="left", padx=4)
        self._button(buttons, "Open Web Dashboard", lambda: webbrowser.open("http://localhost:8765")).pack(side="left", padx=4)

    def _build_admin_config_tab(self, parent):
        card = self._card(parent, "AI Provider")
        card.pack(fill="x", padx=10, pady=10)
        config = hub_db.get_config()
        config = config if isinstance(config, dict) else {}
        ai_cfg = self._load_ai_config_file()

        PROVIDERS = ["openai", "anthropic", "ollama", "github", "groq", "gemini"]
        MODELS_BY_PROVIDER = {
            "openai":    ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o4-mini", "o3-mini"],
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-sonnet-4-5"],
            "ollama":    ["llama3.2", "llama3.2:3b", "llama3.1", "mistral", "phi3", "gemma2", "qwen2.5"],
            "github":    ["gpt-4o-mini", "gpt-4o", "Meta-Llama-3-8B-Instruct", "Phi-3.5-mini-instruct"],
            "groq":      ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
            "gemini":    ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
        }
        BASE_URLS = {
            "openai":    "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "ollama":    "http://localhost:11434/v1",
            "github":    "https://models.inference.ai.azure.com",
            "groq":      "https://api.groq.com/openai/v1",
            "gemini":    "",
        }

        cur_provider = config.get("llm_provider") or ai_cfg.get("provider", "openai")
        cur_model    = config.get("llm_model")    or ai_cfg.get("model",    "gpt-4o-mini")
        cur_key      = config.get("llm_api_key")  or ai_cfg.get("apiKey",   "")
        cur_url      = config.get("llm_base_url") or ai_cfg.get("baseUrl",  "")

        self.admin_provider_var = tk.StringVar(value=cur_provider)
        self.admin_model_var    = tk.StringVar(value=cur_model)
        self.admin_key_var      = tk.StringVar(value=cur_key)
        self.admin_url_var      = tk.StringVar(value=cur_url or BASE_URLS.get(cur_provider, ""))
        self.admin_threads_var  = tk.IntVar(value=int(config.get("thread_pool_size", 3) or 3))

        form = tk.Frame(card, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        tk.Label(form, text="Provider", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=4)
        tk.Label(form, text="Model",    bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=1, sticky="w", pady=4, padx=(8, 0))
        self._combo(form, self.admin_provider_var, PROVIDERS).grid(row=1, column=0, sticky="ew")
        self.admin_model_combo = self._combo(form, self.admin_model_var, MODELS_BY_PROVIDER.get(cur_provider, []))
        self.admin_model_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        tk.Label(form, text="API Key", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        tk.Label(form, text="Base URL (leave blank for default)", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=1, sticky="w", pady=4, padx=(8, 0))
        self._entry(form, self.admin_key_var, show="*").grid(row=3, column=0, sticky="ew")
        self._entry(form, self.admin_url_var).grid(row=3, column=1, sticky="ew", padx=(8, 0))

        tk.Label(form, text="Thread Pool Size", bg=BG_PANEL, fg=TEXT_BODY).grid(row=4, column=0, sticky="w", pady=4)
        tk.Spinbox(form, from_=1, to=32, textvariable=self.admin_threads_var, bg=BG_INPUT, fg=TEXT_PRIMARY, relief="flat").grid(row=5, column=0, sticky="ew")

        btn_row = tk.Frame(form, bg=BG_PANEL)
        btn_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self._button(btn_row, "Save", self._save_admin_config, accent=True).pack(side="left", padx=4)
        self._button(btn_row, "Test Connection", self._test_llm_connection).pack(side="left", padx=4)

        def _on_provider_change(*_):
            p = self.admin_provider_var.get()
            models = MODELS_BY_PROVIDER.get(p, [])
            self.admin_model_combo["values"] = models
            if models and self.admin_model_var.get() not in models:
                self.admin_model_var.set(models[0])
            default_url = BASE_URLS.get(p, "")
            if default_url:
                self.admin_url_var.set(default_url)
        self.admin_provider_var.trace_add("write", _on_provider_change)

    def _build_admin_users_tab(self, parent):
        card = self._card(parent, "Users")
        card.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("id", "username", "email", "role", "is_active", "last_login")
        self.users_tree = ttk.Treeview(card, columns=columns, show="headings", selectmode="browse")
        for column, text, width in (
            ("id", "ID", 60),
            ("username", "Username", 150),
            ("email", "Email", 220),
            ("role", "Role", 100),
            ("is_active", "Active", 80),
            ("last_login", "Last Login", 160),
        ):
            self.users_tree.heading(column, text=text)
            self.users_tree.column(column, width=width, anchor="w")
        self.users_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.users_tree.bind("<<TreeviewSelect>>", lambda _e: self._set_selected_user())

        form = tk.Frame(card, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 14))
        self.user_username_var = tk.StringVar()
        self.user_email_var = tk.StringVar()
        self.user_password_var = tk.StringVar()
        self.user_role_var = tk.StringVar(value="user")
        tk.Label(form, text="Username", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w")
        self._entry(form, self.user_username_var).grid(row=1, column=0, sticky="ew")
        tk.Label(form, text="Email", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self._entry(form, self.user_email_var).grid(row=1, column=1, sticky="ew", padx=(10, 0))
        tk.Label(form, text="Password", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        self._entry(form, self.user_password_var, show="*").grid(row=3, column=0, sticky="ew")
        tk.Label(form, text="Role", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)
        self._combo(form, self.user_role_var, ["user", "admin"]).grid(row=3, column=1, sticky="ew", padx=(10, 0))
        buttons = tk.Frame(form, bg=BG_PANEL)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self._button(buttons, "Add User", self._add_user, accent=True).pack(side="left", padx=4)
        self._button(buttons, "Delete Selected", self._delete_selected_user).pack(side="left", padx=4)
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        self._refresh_users()

    def _build_admin_scheduler_tab(self, parent):
        self.admin_schedule_tree = ttk.Treeview(parent, columns=("id", "agent_id", "project", "schedule", "status"), show="headings")
        for column, text, width in (
            ("id", "ID", 180),
            ("agent_id", "Agent", 220),
            ("project", "Project", 120),
            ("schedule", "Schedule", 260),
            ("status", "Status", 100),
        ):
            self.admin_schedule_tree.heading(column, text=text)
            self.admin_schedule_tree.column(column, width=width, anchor="w")
        self.admin_schedule_tree.pack(fill="both", expand=True, padx=10, pady=10)
        for row in self._schedule_rows():
            self.admin_schedule_tree.insert("", "end", values=(row["id"], row["agent_id"], row["project"], row["schedule"], row["status"]))

    def _build_admin_logs_tab(self, parent):
        controls = tk.Frame(parent, bg=BG_CANVAS)
        controls.pack(fill="x", padx=10, pady=(10, 6))
        files = [path.name for path in LOG_DIR.glob("*.log")] if LOG_DIR.exists() else []
        if files and not self.log_file_var.get():
            self.log_file_var.set(files[0])
        self._combo(controls, self.log_file_var, files or [""]).pack(side="left", fill="x", expand=True)
        self._button(controls, "Refresh", self._refresh_logs, accent=True).pack(side="left", padx=6)
        self.logs_text = self._text_widget(parent, height=30)
        self.logs_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.logs_text.configure(state="disabled")
        self._refresh_logs()

    def _save_admin_config(self):
        cfg = {
            "llm_provider":    self.admin_provider_var.get(),
            "llm_model":       self.admin_model_var.get(),
            "llm_api_key":     self.admin_key_var.get(),
            "llm_base_url":    self.admin_url_var.get(),
            "thread_pool_size": int(self.admin_threads_var.get() or 3),
        }
        hub_db.update_config(cfg)
        self._save_ai_config_file({
            "provider": cfg["llm_provider"],
            "model":    cfg["llm_model"],
            "apiKey":   cfg["llm_api_key"],
            "baseUrl":  cfg["llm_base_url"],
            "enabled":  True,
        })
        self.show_toast("Config saved.", SUCCESS)

    def _test_llm_connection(self):
        import threading as _t
        self.show_toast("Testing connection…", ACCENT)
        def _run():
            try:
                from hub_nodes import _llm
                llm = _llm()
                from langchain_core.messages import HumanMessage
                resp = llm.invoke([HumanMessage(content="Reply with exactly: OK")])
                text = getattr(resp, "content", str(resp))[:80]
                self._ui_queue.put(("toast", f"✅ Connected — {text}", SUCCESS))
            except Exception as exc:
                self._ui_queue.put(("toast", f"❌ {exc}", ERROR))
        _t.Thread(target=_run, daemon=True).start()

    def _load_ai_config_file(self) -> dict:
        paths = [
            APP_ROOT / ".agents" / "data" / "ai_config.json",
            APP_ROOT / "projects" / "agentharness-v2" / "data" / "ai_config.json",
        ]
        for p in paths:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return {}

    def _save_ai_config_file(self, data: dict):
        dest = APP_ROOT / ".agents" / "data" / "ai_config.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _refresh_users(self):
        rows = hub_db.list_users()
        self.users_tree.delete(*self.users_tree.get_children())
        self.users_lookup = {}
        for row in rows:
            self.users_lookup[str(row["id"])] = row
            self.users_tree.insert("", "end", iid=str(row["id"]), values=(row["id"], row["username"], row.get("email", ""), row.get("role", ""), row.get("is_active", ""), self._human_time(row.get("last_login"))))

    def _set_selected_user(self):
        selected = self.users_tree.selection()
        self.selected_user_id = selected[0] if selected else None

    def _add_user(self):
        if not self.user_username_var.get().strip() or not self.user_password_var.get().strip():
            self.show_toast("Username and password required.", WARNING)
            return
        try:
            hub_db.create_user(self.user_username_var.get().strip(), self.user_email_var.get().strip() or None, self.user_password_var.get(), self.user_role_var.get())
            self.user_username_var.set("")
            self.user_email_var.set("")
            self.user_password_var.set("")
            self.user_role_var.set("user")
            self._refresh_users()
            self.show_toast("User added.", SUCCESS)
        except Exception as exc:
            self.show_toast(f"Add user failed: {exc}", ERROR)

    def _delete_selected_user(self):
        if self.selected_user_id:
            hub_db.delete_user(int(self.selected_user_id))
            self.selected_user_id = None
            self._refresh_users()

    def _refresh_logs(self):
        selected = self.log_file_var.get()
        if not selected:
            self._set_text(self.logs_text, "No log files found.")
            return
        path = LOG_DIR / selected
        if not path.exists():
            self._set_text(self.logs_text, f"Log file not found: {selected}")
            return
        content = path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        self._set_text(self.logs_text, "\n".join(lines[-2000:]))

    def _start_hub_server(self):
        candidates = [
            HERE / "hub_server.py",
            APP_ROOT / "_archive" / "agentharness-v3-app" / "hub_server.py",
        ]
        server_path = next((path for path in candidates if path.exists()), None)
        if server_path is None:
            self.show_toast("Hub server script not found.", WARNING)
            return
        if self.hub_process and self.hub_process.poll() is None:
            self.show_toast("Hub server already running.", WARNING)
            return
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        self.hub_process = subprocess.Popen([sys.executable, str(server_path)], cwd=str(server_path.parent), creationflags=flags)
        self.show_toast("Hub server launch requested.", SUCCESS)

    def _stop_hub_server(self):
        if self.hub_process and self.hub_process.poll() is None:
            try:
                self.hub_process.terminate()
                self.show_toast("Hub server stop requested.", WARNING)
                return
            except Exception as exc:
                self.show_toast(f"Stop failed: {exc}", ERROR)
                return
        self.show_toast("No managed hub server process.", WARNING)

    # ── Chat ─────────────────────────────────────────────────────────────────

    def show_inez(self):
        self._clear_content()
        self._set_active_nav("Inez")
        self._build_inez_chat_panel(self.content)


    def _inez_send(self):
        task = (self._chat_input.get("1.0", "end") or "").strip()
        if not task:
            return
        self._chat_input.delete("1.0", "end")

        ts = datetime.now().strftime("%H:%M")

        # Add user bubble
        user_msg = {"role": "user", "content": task, "ts": ts}
        self._chat_messages.append(user_msg)
        self._chat_render_bubble(user_msg)
        self._inez_history.append({"role": "user", "content": task})

        # Add Inez thinking bubble
        think_run_id = "inez-think-" + str(uuid.uuid4())[:8]
        inez_think_msg = {
            "role": "inez_thinking",
            "content": "Inez is analyzing your request...",
            "run_id": think_run_id,
            "ts": ts,
        }
        self._chat_messages.append(inez_think_msg)
        self._chat_render_bubble(inez_think_msg)

        def _on_inez_result(result):
            """Called in background thread when Inez finishes thinking."""
            self._ui_queue.put(("inez_result", think_run_id, result))

        # Try Hub first, fall back to local inez_agent
        if getattr(self.hub, "online", False):
            def _hub_think():
                try:
                    resp = self.hub.post_json("/api/inez/chat", {
                        "message": task,
                        "conversation_id": self._inez_conv_id,
                    }, timeout=_HUB_LLM_TIMEOUT)
                    if resp:
                        self._inez_conv_id = resp.get("conversation_id", self._inez_conv_id)
                    _on_inez_result(resp or {})
                except Exception as exc:
                    _on_inez_result({"inez_message": str(exc), "dispatches": [], "needs_agents": False, "error": str(exc)})
            threading.Thread(target=_hub_think, daemon=True).start()
        else:
            try:
                from inez_agent import think_async
                think_async(task, self._inez_history, _on_inez_result)
            except ImportError:
                self._ui_queue.put(("inez_result", think_run_id, {
                    "inez_message": "Inez agent module not available. Check that inez_agent.py is in the app/v3 folder.",
                    "dispatches": [],
                    "needs_agents": False,
                    "error": "ImportError",
                }))

    def _inez_handle_result(self, think_run_id, result):
        """Process Inez's decision on the main thread (called from _poll_queue)."""
        inez_message = result.get("inez_message", "")
        dispatches   = result.get("dispatches", [])
        ts = datetime.now().strftime("%H:%M")

        # Remove Inez thinking bubble from run_frames so animation stops
        self._chat_run_frames.pop(think_run_id, None)
        self._chat_dot_state.pop(think_run_id, None)

        # Finalize thinking bubble
        status_lbl = self._chat_run_status_label.pop(think_run_id, None)
        if status_lbl:
            try:
                status_lbl.configure(text="✓  Done", fg=SUCCESS)
            except Exception:
                pass

        # Add Inez response bubble
        if inez_message:
            inez_msg = {"role": "inez", "content": inez_message, "ts": ts}
            self._chat_messages.append(inez_msg)
            self._inez_history.append({"role": "inez", "content": inez_message})
            self._chat_render_bubble(inez_msg)

        # Dispatch agent runs
        for dispatch in dispatches:
            agent_id = dispatch.get("agent_id", "")
            project  = dispatch.get("project", "")
            graph    = dispatch.get("graph", "reflexion")
            task_txt = dispatch.get("task", "")
            if not agent_id or not task_txt:
                continue

            run_id = str(uuid.uuid4())
            deploy_msg = {
                "role": "thinking",
                "content": task_txt,
                "agent_id": agent_id,
                "project": project,
                "graph": graph,
                "run_id": run_id,
                "ts": ts,
            }
            self._chat_messages.append(deploy_msg)
            self._chat_render_bubble(deploy_msg)

            config = {
                "agent_id": agent_id, "project": project,
                "graph": graph, "task": task_txt,
                "max_revisions": 2, "run_id": run_id,
            }
            self._submit_chat_run(config, run_id)
            self._chat_dot_state[run_id] = 0
            self._chat_animate_dots(run_id)

    def _submit_chat_run(self, config, run_id):
        if getattr(self.hub, "online", False):
            try:
                self.hub.submit_run(
                    agent_id=config["agent_id"], project=config["project"],
                    graph=config["graph"], task=config["task"],
                    max_revisions=config.get("max_revisions", 2),
                )
                return
            except Exception:
                pass
        # Fallback: local execution in thread
        cancel_flag = threading.Event()
        self.cancel_flags[run_id] = cancel_flag

        def _thread():
            try:
                from hub_nodes import run_graph
                def emit(event_type, **kwargs):
                    self._ui_queue.put(("run_event", event_type, {"run_id": run_id, **kwargs}))
                run_graph({**config, "cancel_flag": cancel_flag}, emit=emit)
            except Exception as exc:
                self._ui_queue.put(("run_event", "run_failed",
                                    {"run_id": run_id, "error": str(exc)}))
        threading.Thread(target=_thread, daemon=True).start()

    def _chat_render_bubble(self, msg):
        if self._chat_bubbles_frame is None:
            return
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        ts      = msg.get("ts", "")
        run_id  = msg.get("run_id", "")

        outer = tk.Frame(self._chat_bubbles_frame, bg=BG_CANVAS)
        outer.pack(fill="x", padx=18, pady=6, anchor="e" if role == "user" else "w")

        if role == "user":
            self._chat_user_bubble(outer, content, ts)
        elif role == "thinking":
            self._chat_thinking_bubble(outer, msg)
        elif role == "inez_thinking":
            self._inez_thinking_bubble(outer, msg)
        elif role in ("agent", "inez"):
            self._chat_agent_bubble(outer, msg)

        self._chat_scroll_bottom()

    def _chat_user_bubble(self, parent, content, ts):
        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="e")
        bubble = tk.Frame(wrap, bg=ACCENT_DARK,
                          highlightbackground=ACCENT, highlightthickness=1)
        bubble.pack(anchor="e")
        tk.Label(bubble, text=content, bg=ACCENT_DARK, fg="#ffffff",
                 font=("Segoe UI", 11), wraplength=520, justify="left",
                 padx=14, pady=10).pack()
        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="e", padx=4)

    def _chat_thinking_bubble(self, parent, msg):
        agent_id = msg.get("agent_id", "agent")
        graph    = msg.get("graph", "reflexion")
        run_id   = msg.get("run_id", "")
        ts       = msg.get("ts", "")

        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="w", fill="x")

        # Agent avatar dot
        av = tk.Canvas(wrap, width=32, height=32, bg=BG_CANVAS, highlightthickness=0)
        av.create_oval(4, 4, 28, 28, fill=ACCENT, outline="")
        av.create_text(16, 16, text="⚡", fill="white", font=("Segoe UI", 12))
        av.pack(side="left", anchor="nw", pady=4)

        bubble = tk.Frame(wrap, bg=BG_CARD,
                          highlightbackground=BORDER_CARD, highlightthickness=1)
        bubble.pack(side="left", anchor="nw", fill="x", expand=True, padx=6)

        # Header — agent + graph
        hdr = tk.Frame(bubble, bg=BG_CARD)
        hdr.pack(fill="x", padx=12, pady=(10,4))
        tk.Label(hdr, text=f"⚡  Deploying  ", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Label(hdr, text=agent_id, bg=BG_CARD, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(hdr, text=f"  ·  {graph}", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)

        # Steps container
        steps_frame = tk.Frame(bubble, bg=BG_CARD)
        steps_frame.pack(fill="x", padx=12, pady=6)
        self._chat_run_step_labels[run_id] = []

        # Show expected graph nodes as pending steps
        nodes = GRAPH_LAYOUTS.get(graph, ["load_memory", "act", "evaluate", "save_memory"])
        for node in nodes:
            row = tk.Frame(steps_frame, bg=BG_CARD)
            row.pack(anchor="w", pady=1)
            dot = tk.Label(row, text="○", bg=BG_CARD, fg=TEXT_MUTED,
                           font=("Segoe UI", 10))
            dot.pack(side="left")
            lbl = tk.Label(row, text=f"  {node}", bg=BG_CARD, fg=TEXT_MUTED,
                           font=("Segoe UI Mono", 9))
            lbl.pack(side="left")
            self._chat_run_step_labels[run_id].append((node, dot, lbl))

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)

        # Status / dots line
        status_lbl = tk.Label(bubble, text="● Thinking...", bg=BG_CARD, fg=ACCENT,
                              font=("Segoe UI", 9, "italic"), padx=12, pady=8)
        status_lbl.pack(anchor="w")
        self._chat_run_status_label[run_id] = status_lbl

        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=42)

        # Store frame reference so we can replace it on completion
        self._chat_run_frames[run_id] = (parent, wrap, bubble, steps_frame, status_lbl)


    def _inez_thinking_bubble(self, parent, msg):
        """Inez's own thinking bubble — purple themed."""
        run_id = msg.get("run_id", "")
        ts     = msg.get("ts", "")

        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="w", fill="x")

        av = tk.Canvas(wrap, width=32, height=32, bg=BG_CANVAS, highlightthickness=0)
        av.create_oval(4, 4, 28, 28, fill="#7c3aed", outline="")
        av.create_text(16, 16, text="👑", font=("Segoe UI", 12))
        av.pack(side="left", anchor="nw", pady=4)

        bubble = tk.Frame(wrap, bg=BG_CARD,
                          highlightbackground="#7c3aed", highlightthickness=1)
        bubble.pack(side="left", anchor="nw", fill="x", expand=True, padx=6)

        hdr = tk.Frame(bubble, bg=BG_CARD)
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(hdr, text="Inez", bg=BG_CARD, fg="#c4b5fd",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(hdr, text="  ·  analyzing request", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)

        status_lbl = tk.Label(bubble, text="● Thinking...", bg=BG_CARD, fg="#c4b5fd",
                              font=("Segoe UI", 9, "italic"), padx=12, pady=8)
        status_lbl.pack(anchor="w")
        self._chat_run_status_label[run_id] = status_lbl

        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=42)

        self._chat_run_frames[run_id] = (parent, wrap, bubble, None, status_lbl)
        self._chat_dot_state[run_id] = 0
        self._chat_animate_dots(run_id)

    def _chat_agent_bubble(self, parent, msg):
        agent_id = msg.get("agent_id", "agent")
        content  = msg.get("content", "")
        score    = msg.get("score", None)
        graph    = msg.get("graph", "")
        ts       = msg.get("ts", "")
        run_id   = msg.get("run_id", "")
        is_inez  = agent_id in ("inez", "inez-chief-of-staff") or msg.get("role") == "inez"

        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="w", fill="x")

        av = tk.Canvas(wrap, width=32, height=32, bg=BG_CANVAS, highlightthickness=0)
        if is_inez:
            av.create_oval(4, 4, 28, 28, fill="#7c3aed", outline="")
            av.create_text(16, 16, text="👑", font=("Segoe UI", 12))
        else:
            av.create_oval(4, 4, 28, 28, fill=SUCCESS, outline="")
            av.create_text(16, 16, text="✓", fill="white", font=("Segoe UI", 12, "bold"))
        av.pack(side="left", anchor="nw", pady=4)

        border_color = "#7c3aed" if is_inez else SUCCESS
        bubble = tk.Frame(wrap, bg=BG_PANEL,
                          highlightbackground=border_color, highlightthickness=1)
        bubble.pack(side="left", anchor="nw", fill="x", expand=True, padx=6)

        hdr = tk.Frame(bubble, bg=BG_PANEL)
        hdr.pack(fill="x", padx=12, pady=(8, 4))
        name_color = "#c4b5fd" if is_inez else SUCCESS
        display_name = "Inez" if is_inez else agent_id
        tk.Label(hdr, text=display_name, bg=BG_PANEL, fg=name_color,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        if graph and not is_inez:
            tk.Label(hdr, text=f"  ·  {graph}", bg=BG_PANEL, fg=TEXT_MUTED,
                     font=("Segoe UI", 9)).pack(side="left")
        if score is not None and not is_inez:
            sc = float(score)
            sc_color = SUCCESS if sc >= 0.75 else WARNING if sc >= 0.5 else ERROR
            tk.Label(hdr, text=f"  ·  score {sc:.2f}", bg=BG_PANEL, fg=sc_color,
                     font=("Segoe UI", 9, "bold")).pack(side="left")

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)
        tk.Label(bubble, text=content, bg=BG_PANEL, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11), wraplength=580, justify="left",
                 padx=14, pady=12, anchor="w").pack(fill="x")
        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=42)

    def _chat_animate_dots(self, run_id):
        if run_id not in self._chat_run_status_label:
            return
        if run_id not in self._chat_run_frames:
            return
        lbl = self._chat_run_status_label.get(run_id)
        if lbl is None:
            return
        try:
            lbl.winfo_exists()
        except Exception:
            return
        if not lbl.winfo_exists():
            return
        tick = self._chat_dot_state.get(run_id, 0)
        dots = "●" * (tick % 3 + 1) + "○" * (2 - tick % 3)
        current_node = self.run_state.get(run_id, {}).get("current_node", "")
        node_text = f"  Running {current_node}..." if current_node else "  Thinking..."
        try:
            lbl.configure(text=f"{dots}{node_text}")
        except Exception:
            return
        self._chat_dot_state[run_id] = tick + 1
        # Continue animating every 400ms while still in run_frames
        self.root.after(400, lambda: self._chat_animate_dots(run_id))

    def _chat_handle_run_event(self, event_type, data, run_id):
        stamp = datetime.now().strftime("%H:%M:%S")

        if event_type == "node_update":
            node   = data.get("node", "")
            status = data.get("status", "")
            # Update step indicators
            for (n, dot_lbl, name_lbl) in self._chat_run_step_labels.get(run_id, []):
                try:
                    if n == node:
                        if status == "running":
                            dot_lbl.configure(text="▶", fg=ACCENT)
                            name_lbl.configure(fg=ACCENT)
                        elif status in ("done", "complete"):
                            dot_lbl.configure(text="✓", fg=SUCCESS)
                            name_lbl.configure(fg=SUCCESS)
                    elif self._node_is_done(run_id, n, node):
                        dot_lbl.configure(text="✓", fg=SUCCESS)
                        name_lbl.configure(fg=TEXT_BODY)
                except Exception:
                    pass
            # Update status label
            status_lbl = self._chat_run_status_label.get(run_id)
            if status_lbl:
                try:
                    status_lbl.configure(
                        text=f"▶  Running  {node}  ·  {stamp}",
                        fg=ACCENT
                    )
                except Exception:
                    pass

        elif event_type in ("run_completed", "run_failed"):
            # Mark all remaining steps done/failed
            is_fail = event_type == "run_failed"
            for (n, dot_lbl, name_lbl) in self._chat_run_step_labels.get(run_id, []):
                try:
                    cur_text = dot_lbl.cget("text")
                    if cur_text not in ("✓", "✗"):
                        if is_fail:
                            dot_lbl.configure(text="✗", fg=ERROR)
                            name_lbl.configure(fg=ERROR)
                        else:
                            dot_lbl.configure(text="✓", fg=SUCCESS)
                            name_lbl.configure(fg=SUCCESS)
                except Exception:
                    pass

            # Update status label
            status_lbl = self._chat_run_status_label.get(run_id)
            if status_lbl:
                try:
                    if is_fail:
                        status_lbl.configure(text=f"✗  Failed  ·  {stamp}", fg=ERROR)
                    else:
                        score = float(data.get("score", 0) or 0)
                        status_lbl.configure(
                            text=f"✓  Complete  ·  score {score:.2f}  ·  {stamp}",
                            fg=SUCCESS
                        )
                except Exception:
                    pass

            # Stop animation
            self._chat_run_frames.pop(run_id, None)
            self._chat_dot_state.pop(run_id, None)

            # Add agent response bubble
            if not is_fail:
                output = data.get("output", "") or self._get_run_output(run_id)
                if output:
                    # Find corresponding chat message for agent/graph
                    think_msg = next(
                        (m for m in self._chat_messages
                         if m.get("run_id") == run_id and m.get("role") == "thinking"),
                        {}
                    )
                    agent_msg = {
                        "role": "agent",
                        "content": output,
                        "agent_id": think_msg.get("agent_id", "agent"),
                        "graph": think_msg.get("graph", ""),
                        "score": data.get("score"),
                        "run_id": run_id,
                        "ts": datetime.now().strftime("%H:%M"),
                    }
                    self._chat_messages.append(agent_msg)
                    if self.current_view in ("Chat", "Inez") and self._chat_bubbles_frame:
                        outer = tk.Frame(self._chat_bubbles_frame, bg=BG_CANVAS)
                        outer.pack(fill="x", padx=18, pady=6, anchor="w")
                        self._chat_agent_bubble(outer, agent_msg)
                        self._chat_scroll_bottom()

            # Clean up step labels
            self._chat_run_step_labels.pop(run_id, None)
            self._chat_run_status_label.pop(run_id, None)

    def _node_is_done(self, run_id, node, current_node):
        """Return True if node comes before current_node in the graph layout."""
        run_msg = next(
            (m for m in self._chat_messages
             if m.get("run_id") == run_id and m.get("role") == "thinking"), {}
        )
        graph = run_msg.get("graph", "reflexion")
        layout = GRAPH_LAYOUTS.get(graph, [])
        try:
            return layout.index(node) < layout.index(current_node)
        except ValueError:
            return False

    def _get_run_output(self, run_id):
        try:
            runs = hub_db.load_runs(limit=1, agent_id=None, project=None, status=None)
            for r in runs:
                if r.get("run_id") == run_id:
                    return r.get("output", "")
        except Exception:
            pass
        return ""

    def _chat_scroll_bottom(self):
        try:
            if self._chat_canvas:
                self._chat_canvas.update_idletasks()
                self._chat_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # ── End Chat ──────────────────────────────────────────────────────────────

    def on_close(self):
        try:
            self.hub.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ArchonHubApp()
    app.run()

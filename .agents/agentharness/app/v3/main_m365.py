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

from pages.constants import *
from pages.threading_mixin import ThreadingMixin
from pages.notifications_page import NotificationsPageMixin
from pages.memory_page import MemoryPageMixin
from pages.files_page import FilesPageMixin
from pages.search_sandbox_page import SearchSandboxPageMixin
from pages.brief_page import BriefPageMixin
from pages.agents_page import AgentsPageMixin
from pages.connectors_page import ConnectorsPageMixin
from pages.models_page import ModelsPageMixin
from pages.admin_page import AdminPageMixin
from pages.inez_page import InezPageMixin

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
NAV_ITEMS = [
    ("🏠", "Home",     "show_home"),
    ("▶",  "Runs",     "show_runs"),
    ("✓",  "Todos",    "show_todos"),
    ("📋", "Brief",    "show_brief"),
    ("📊", "Reports",  "show_reports"),
    ("📅", "Schedule", "show_schedule"),
    ("👥", "Clients",  "show_clients"),
    ("✈",  "Travel",   "show_travel"),
    ("📈", "Markets",  "show_markets"),
    ("🏢", "Org",      "show_org"),
    ("🧠", "Memory",   "show_memory"),
    ("📁", "Files",    "show_files"),
    ("⚡", "Connect",  "show_connectors"),
    ("🤖", "Agents",   "show_agents"),
    ("🔬", "Models",   "show_models"),
    ("🔔", "Notifs",  "show_notifications"),
    ("🔍", "Search",  "show_web_search"),
    ("⚡", "Sandbox", "show_sandbox"),
    ("👑", "Inez",     "show_inez"),
    ("🔑", "Admin",    "show_admin"),
]


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

    def get_json(self, path, **params):
        if path.startswith("/api/notifications"):
            return hub_db.list_notifications()
        return None

    def _get(self, path, **params):
        return self.get_json(path, **params)

    def put_json(self, path, data):
        return None

    def delete(self, path):
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


class ArchonHubApp(
    ThreadingMixin,
    NotificationsPageMixin,
    MemoryPageMixin,
    FilesPageMixin,
    SearchSandboxPageMixin,
    BriefPageMixin,
    AgentsPageMixin,
    ConnectorsPageMixin,
    ModelsPageMixin,
    AdminPageMixin,
    InezPageMixin,
):
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
        self._inez_pending = {}           # server run_id -> local think_run_id (async 202 reply routing)
        self._inez_status = {}            # cached /api/inez/status response
        self._inez_hud_visible = True     # whether the INEZ awareness HUD strip is shown

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
        self.root.after(2000, self._health_fallback_poll)  # direct ping fallback
        self._poll_notifications()
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
        self._notif_count = 0
        self._notif_btn = tk.Label(self.status_bar, text="🔔", fg=TEXT_MUTED, bg=BG_PANEL,
                                   font=("Segoe UI Emoji", 13), cursor="hand2")
        self._notif_btn.pack(side="left", padx=4)
        self._notif_btn.bind("<Button-1>", lambda _e: self._show_notifications_panel())
        self._notif_badge = tk.Label(self.status_bar, text="", fg=ERROR, bg=BG_PANEL,
                                     font=("Segoe UI", 8, "bold"))
        self._notif_badge.pack(side="left")
        self.clock_label = tk.Label(self.status_bar, text="", fg=TEXT_MUTED, bg=BG_PANEL)
        self.clock_label.pack(side="right", padx=10)

        # Main shell — expands into remaining space above the status bar
        self.shell = tk.Frame(self.root, bg=BG_CANVAS)
        self.shell.pack(fill="both", expand=True)

        self.rail = tk.Frame(self.shell, width=60, bg=BG_RAIL)
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)

        # Logo at the top (fixed, not scrollable)
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

        # Scrollable canvas for nav buttons
        rail_canvas = tk.Canvas(self.rail, bg=BG_RAIL, highlightthickness=0, width=60)
        rail_canvas.pack(fill="both", expand=True)
        rail_inner = tk.Frame(rail_canvas, bg=BG_RAIL)
        rail_window = rail_canvas.create_window((0, 0), window=rail_inner, anchor="nw", width=60)

        def _on_rail_configure(_e):
            rail_canvas.configure(scrollregion=rail_canvas.bbox("all"))
        rail_inner.bind("<Configure>", _on_rail_configure)

        def _rail_scroll(e):
            rail_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        rail_canvas.bind("<MouseWheel>", _rail_scroll)
        rail_inner.bind("<MouseWheel>", _rail_scroll)

        for icon, label, method_name in NAV_ITEMS:
            btn = tk.Label(
                rail_inner,
                text=icon,
                bg=BG_RAIL,
                fg=TEXT_BODY,
                width=3,
                pady=8,
                cursor="hand2",
                font=("Segoe UI Emoji", 15),
            )
            btn.pack(fill="x", padx=4, pady=1)
            btn.bind("<Button-1>", lambda _e, name=method_name: getattr(self, name)())
            btn.bind("<Enter>", lambda _e, widget=btn: widget.configure(bg=BG_HOVER))
            btn.bind("<Leave>", lambda _e, widget=btn, nav=label: self._reset_nav_bg(widget, nav))
            btn.bind("<MouseWheel>", _rail_scroll)
            ToolTip(btn, label)
            self.nav_buttons[label] = btn

        tk.Label(self.rail, text="v1", fg=TEXT_MUTED, bg=BG_RAIL).pack(side="bottom", pady=8)

        self.content = tk.Frame(self.shell, bg=BG_CANVAS)
        self.content.pack(side="left", fill="both", expand=True)

    def _update_clock(self):
        self.clock_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self._update_status_bar()
        self.root.after(1000, self._update_clock)

    def _health_fallback_poll(self):
        """Every 5s: if HubClient says offline, do a direct health ping as fallback.
        Fixes the 5-second WS-reconnect gap where hub is reachable but client shows offline."""
        import threading as _t
        def _ping():
            try:
                import urllib.request as _ur
                _ur.urlopen("http://localhost:8765/api/health", timeout=2)
                if not getattr(self.hub, "online", False):
                    self.hub._set_online(True)
                    self._ui_queue.put(("call", self._update_status_bar))
            except Exception:
                pass
        if not getattr(self.hub, "online", False):
            _t.Thread(target=_ping, daemon=True).start()
        try:
            self.root.after(5000, self._health_fallback_poll)
        except Exception:
            pass

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

    def _toast(self, text, color=ACCENT):
        self.show_toast(text, color)

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
            elif kind == "inez_status_loaded":
                self._apply_inez_status()
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
            elif kind == "device_code_dialog":
                self._device_code_dialog(item[1], item[2], item[3])
            elif kind == "refresh_users":
                if self._widget_ok("users_tree"):
                    self._refresh_users()
            elif kind == "set_text":
                try:
                    self._set_text(item[1], item[2])
                except Exception:
                    pass
            elif kind == "call":
                try:
                    item[1]()
                except Exception:
                    pass
            elif kind == "call_with_arg":
                try:
                    item[1](item[2])
                except Exception:
                    pass
            elif kind == "configure":
                try:
                    item[1].configure(**item[2])
                except Exception:
                    pass
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
        if event_type == "inez_response":
            self._handle_inez_response(event)
            return
        if event_type == "notification":
            self.show_toast(event.get("text", "Notification"), event.get("color", ACCENT))

    def _handle_inez_response(self, event):
        """Route an async Inez reply (delivered over WebSocket) to the chat bubble
        that initiated it.

        POST /api/inez/chat returns 202 immediately; the actual answer arrives here
        as an `inez_response` broadcast. `_inez_pending` maps the server's run_id to
        the local thinking-bubble id so we render into the right conversation and
        ignore replies belonging to other clients/turns. The event payload carries
        the same fields the HTTP body used to (inez_message, dispatches, …), so we
        hand it to the unchanged _inez_handle_result renderer.
        """
        server_run_id = event.get("run_id")
        think_run_id = self._inez_pending.pop(server_run_id, None) if server_run_id else None
        if not think_run_id:
            return  # not a turn this client is waiting on (or already handled)
        self._inez_handle_result(think_run_id, event)

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

    def _poll_notifications(self):
        try:
            if hasattr(self.hub, "_get"):
                data = self.hub._get("/api/notifications")
            else:
                data = self.hub.list_notifications(unread_only=True)
            items = data if isinstance(data, list) else (data or {}).get("notifications", [])
            unread = sum(1 for item in (items or []) if not item.get("dismissed") and not item.get("read"))
            self._notif_count = unread
            if self._widget_ok("_notif_badge"):
                self._notif_badge.configure(text=str(unread) if unread else "")
            if self._widget_ok("_notif_btn"):
                self._notif_btn.configure(fg=ERROR if unread else TEXT_MUTED)
        except Exception:
            if self._widget_ok("_notif_badge"):
                self._notif_badge.configure(text="")
        finally:
            self.root.after(30000, self._poll_notifications)

    def _show_notifications_panel(self):
        win = tk.Toplevel(self.root)
        win.title("Notifications")
        win.geometry("400x500")
        win.configure(bg=BG_CANVAS)
        self._section_header(win, "🔔 Notifications", "Recent alerts and system messages.")
        wrapper, _canvas, inner = self._scrollable_area(win, BG_CANVAS)
        wrapper.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        def _fetch_notifications():
            try:
                if hasattr(self.hub, "_get"):
                    data = self.hub._get("/api/notifications") or []
                else:
                    data = self.hub.list_notifications(unread_only=False) or []
                return data if isinstance(data, list) else data.get("notifications", [])
            except Exception:
                return []

        def _render():
            for child in inner.winfo_children():
                child.destroy()
            notifications = _fetch_notifications()
            unread = sum(1 for item in notifications if not item.get("dismissed") and not item.get("read"))
            self._notif_count = unread
            if self._widget_ok("_notif_badge"):
                self._notif_badge.configure(text=str(unread) if unread else "")
            if self._widget_ok("_notif_btn"):
                self._notif_btn.configure(fg=ERROR if unread else TEXT_MUTED)
            if not notifications:
                tk.Label(inner, text="No notifications", bg=BG_CANVAS, fg=TEXT_MUTED,
                         font=("Segoe UI", 10)).pack(anchor="center", pady=24)
                return
            for item in notifications:
                card = tk.Frame(inner, bg=BG_PANEL, highlightbackground=BORDER_CARD, highlightthickness=1)
                card.pack(fill="x", pady=6)
                top = tk.Frame(card, bg=BG_PANEL)
                top.pack(fill="x", padx=12, pady=(10, 4))
                tk.Label(top, text=item.get("title", "Notification"), bg=BG_PANEL, fg=TEXT_PRIMARY,
                         font=("Segoe UI", 10, "bold")).pack(side="left", anchor="w")
                ts = str(item.get("created_at") or item.get("time") or item.get("timestamp") or "")[:16]
                tk.Label(top, text=ts, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(side="right")
                tk.Label(
                    card,
                    text=item.get("body") or item.get("message") or "(no details)",
                    bg=BG_PANEL,
                    fg=TEXT_BODY,
                    justify="left",
                    wraplength=320,
                ).pack(fill="x", padx=12, pady=(0, 8))

                def _dismiss(notification_id=item.get("id")):
                    try:
                        try:
                            self.hub.delete(f"/api/notifications/{notification_id}")
                        except Exception:
                            self.hub.post_json(f"/api/notifications/{notification_id}/dismiss", {})
                        self._toast("Notification dismissed.", SUCCESS)
                    except Exception as exc:
                        self._toast(f"Notification error: {exc}", ERROR)
                    _render()

                btn_row = tk.Frame(card, bg=BG_PANEL)
                btn_row.pack(fill="x", padx=12, pady=(0, 10))
                self._button(btn_row, "Dismiss", _dismiss).pack(side="right")

        _render()

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

    def _fetch_inez_status(self):
        """Fetch /api/inez/status from Hub (or local fallback) in a background thread."""
        def _work():
            result = {}
            try:
                if getattr(self.hub, "online", False):
                    r = self.hub.get_json("/api/inez/status")
                    if isinstance(r, dict):
                        result.update(r)
            except Exception:
                pass
            if not result:
                try:
                    from inez_agent import generate_status_report
                    result = generate_status_report()
                except Exception:
                    result = {"awareness": "All systems nominal.", "urgent_count": 0, "missions": []}
            self._inez_status = result
            self._ui_queue.put(("inez_status_loaded",))
        threading.Thread(target=_work, daemon=True).start()

    def _apply_inez_status(self):
        """Refresh all INEZ HUD widgets with the current self._inez_status data."""
        status = self._inez_status
        awareness = status.get("awareness", "All systems nominal.")
        urgent_count = int(status.get("urgent_count", 0) or 0)
        missions = status.get("missions", [])

        # ── Mission HUD on home screen ────────────────────────────────────
        if self._widget_ok("home_urgent_value"):
            urg_text  = f"  {urgent_count} urgent" if urgent_count > 0 else "  All clear"
            urg_color = ERROR if urgent_count > 0 else SUCCESS
            try:
                self.home_urgent_value.configure(text=urg_text, fg=urg_color)
            except Exception:
                pass

        if self._widget_ok("home_awareness_text"):
            first_line = awareness.split("\n")[0][:120]
            try:
                self.home_awareness_text.configure(text=first_line)
            except Exception:
                pass

        if hasattr(self, "home_mission_grid"):
            try:
                if self.home_mission_grid.winfo_exists():
                    self._render_mission_grid(self.home_mission_grid, missions)
            except Exception:
                pass

        # ── Awareness HUD strip inside Inez chat panel ────────────────────
        if hasattr(self, "_inez_awareness_frame"):
            try:
                if self._inez_awareness_frame.winfo_exists():
                    if urgent_count > 0 and self._inez_hud_visible:
                        first_line = awareness.split("\n")[0][:200]
                        if hasattr(self, "_inez_awareness_label"):
                            try:
                                if self._inez_awareness_label.winfo_exists():
                                    self._inez_awareness_label.configure(text=first_line)
                            except Exception:
                                pass
                        self._inez_awareness_frame.pack(fill="x", after=self._inez_header_frame)
                    else:
                        self._inez_awareness_frame.pack_forget()
            except Exception:
                pass

        # ── Urgent count label in Inez header ─────────────────────────────
        if hasattr(self, "_inez_urgent_label"):
            try:
                if self._inez_urgent_label.winfo_exists():
                    urg_text  = f"{urgent_count} need attention" if urgent_count > 0 else ""
                    urg_color = ERROR if urgent_count > 0 else TEXT_MUTED
                    self._inez_urgent_label.configure(text=urg_text, fg=urg_color)
            except Exception:
                pass

    def _render_mission_grid(self, frame, missions):
        """Render a 2-column grid of project mission status tiles inside frame."""
        for child in frame.winfo_children():
            child.destroy()
        if not missions:
            tk.Label(frame, text="No mission data yet", bg=BG_PANEL,
                     fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            return
        status_color_map = {
            "active": SUCCESS, "live": SUCCESS, "complete": SUCCESS, "completed": SUCCESS,
            "pending": WARNING, "pre-launch": WARNING, "planning": WARNING,
            "paused": TEXT_MUTED, "inactive": TEXT_MUTED,
        }
        for idx, m in enumerate(missions[:6]):
            row, col = divmod(idx, 2)
            tile = tk.Frame(frame, bg=BG_CARD,
                            highlightbackground=BORDER_CARD, highlightthickness=1)
            tile.grid(row=row, column=col, sticky="ew",
                      padx=(0, 4) if col == 0 else (0, 0), pady=2)
            s = m.get("status", "unknown").lower()
            dot_color = status_color_map.get(s, ACCENT)
            dot_cv = tk.Canvas(tile, width=8, height=8, bg=BG_CARD, highlightthickness=0)
            dot_cv.create_oval(1, 1, 7, 7, fill=dot_color, outline="")
            dot_cv.pack(side="left", padx=(6, 3), pady=6)
            name = (m.get("name") or m.get("slug") or "")[:18]
            tk.Label(tile, text=name, bg=BG_CARD, fg=TEXT_BODY,
                     font=("Segoe UI", 9), anchor="w").pack(
                         side="left", fill="x", expand=True, padx=(0, 6), pady=4)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def _inez_quick_send(self, text: str):
        """Pre-fill and immediately send a quick-action message to Inez."""
        try:
            if not hasattr(self, "_chat_input") or not self._chat_input.winfo_exists():
                return
        except Exception:
            return
        self._chat_input.delete("1.0", "end")
        self._chat_input.insert("1.0", text)
        self._inez_send()

    def show_home(self):
        self._set_active_nav("Home")
        self._clear_content()
        self._section_header(self.content, "Mission Control", "Inez — Chief of Staff · Smith Capital Portfolio")

        paned = tk.PanedWindow(self.content, orient="horizontal", sashwidth=6,
                               bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ── Left panel: Mission HUD ───────────────────────────────────────
        left = tk.Frame(paned, bg=BG_CANVAS, width=340)
        paned.add(left, minsize=300)

        mission_card = self._card(left, "INEZ — Mission HUD")
        mission_card.pack(fill="x")

        # ── Urgency row ──────────────────────────────────────────────────
        urg_row = tk.Frame(mission_card, bg=BG_PANEL)
        urg_row.pack(fill="x", padx=14, pady=(0, 4))
        tk.Label(urg_row, text="⚡", bg=BG_PANEL, fg="#c4b5fd",
                 font=("Segoe UI", 11)).pack(side="left")
        self.home_urgent_value = tk.Label(urg_row, text="  Loading...",
                                          bg=BG_PANEL, fg=TEXT_MUTED,
                                          font=("Segoe UI", 10, "bold"))
        self.home_urgent_value.pack(side="left", padx=(4, 0))

        # ── Awareness text ────────────────────────────────────────────────
        self.home_awareness_text = tk.Label(
            mission_card, text="Fetching awareness data...",
            bg=BG_PANEL, fg=TEXT_BODY, wraplength=280, justify="left",
            font=("Segoe UI", 9))
        self.home_awareness_text.pack(anchor="w", padx=14, pady=(0, 8))

        # ── Mission grid ──────────────────────────────────────────────────
        self.home_mission_grid = tk.Frame(mission_card, bg=BG_PANEL)
        self.home_mission_grid.pack(fill="x", padx=14, pady=(0, 8))
        self._render_mission_grid(self.home_mission_grid, [])

        # ── Ask Inez CTA ──────────────────────────────────────────────────
        self._button(mission_card, "👑 Ask Inez", self.show_inez, accent=True).pack(
            fill="x", padx=14, pady=(0, 8))

        # ── Hub connection status (compact) ───────────────────────────────
        tk.Frame(mission_card, bg=BORDER_CARD, height=1).pack(fill="x", padx=14, pady=(0, 6))
        stat_grid = tk.Frame(mission_card, bg=BG_PANEL)
        stat_grid.pack(fill="x", padx=14, pady=(0, 12))
        tk.Label(stat_grid, text="Hub", bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        self.home_status_value = tk.Label(stat_grid, text="Offline",
                                          bg=BG_PANEL, fg=ERROR,
                                          font=("Segoe UI", 9, "bold"))
        self.home_status_value.grid(row=0, column=1, sticky="e", pady=2)
        tk.Label(stat_grid, text="Uptime", bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        self.home_uptime_value = tk.Label(stat_grid, text="—",
                                          bg=BG_PANEL, fg=TEXT_BODY,
                                          font=("Segoe UI", 9))
        self.home_uptime_value.grid(row=1, column=1, sticky="e", pady=2)
        tk.Label(stat_grid, text="Active runs", bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.home_active_runs_value = tk.Label(stat_grid, text="0",
                                               bg=BG_PANEL, fg=TEXT_BODY,
                                               font=("Segoe UI", 9))
        self.home_active_runs_value.grid(row=2, column=1, sticky="e", pady=2)
        stat_grid.grid_columnconfigure(1, weight=1)

        # ── Right panel: Inez Chat ────────────────────────────────────────
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(right)
        self._build_inez_chat_panel(right)

        self._refresh_home_status()
        self._fetch_inez_status()

    def _build_inez_chat_panel(self, parent):
        """Embed the full Inez chat interface into any parent frame (used on Home + Inez tab)."""
        # ── Header ────────────────────────────────────────────────────────
        self._inez_header_frame = tk.Frame(parent, bg=BG_PANEL,
                                           highlightbackground=BORDER_CARD,
                                           highlightthickness=1)
        self._inez_header_frame.pack(fill="x")

        av = tk.Canvas(self._inez_header_frame, width=34, height=34,
                       bg=BG_PANEL, highlightthickness=0)
        av.create_oval(3, 3, 31, 31, fill="#7c3aed", outline="")
        av.create_text(17, 17, text="👑", font=("Segoe UI", 14))
        av.pack(side="left", padx=(12, 6), pady=8)

        name_col = tk.Frame(self._inez_header_frame, bg=BG_PANEL)
        name_col.pack(side="left", pady=8)
        tk.Label(name_col, text="INEZ", bg=BG_PANEL, fg="#c4b5fd",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(name_col, text="Intelligent Neural Executive Zone",
                 bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        right_col = tk.Frame(self._inez_header_frame, bg=BG_PANEL)
        right_col.pack(side="right", padx=14, pady=8)
        hub_online = getattr(self.hub, "online", False)
        dot_color = SUCCESS if hub_online else WARNING
        dot_text  = "● ACTIVE" if hub_online else "● LOCAL"
        tk.Label(right_col, text=dot_text, bg=BG_PANEL, fg=dot_color,
                 font=("Segoe UI", 9, "bold")).pack(anchor="e")
        urgent_count = int(self._inez_status.get("urgent_count", 0) or 0)
        urg_text  = f"{urgent_count} need attention" if urgent_count > 0 else ""
        urg_color = ERROR if urgent_count > 0 else TEXT_MUTED
        self._inez_urgent_label = tk.Label(right_col, text=urg_text,
                                           bg=BG_PANEL, fg=urg_color,
                                           font=("Segoe UI", 8))
        self._inez_urgent_label.pack(anchor="e")

        # ── Awareness HUD (collapsible purple strip) ───────────────────────
        self._inez_awareness_frame = tk.Frame(parent, bg="#1a0f3a",
                                              highlightbackground="#5b21b6",
                                              highlightthickness=1)
        # Only show on build if we already have status data with urgency
        if urgent_count > 0 and self._inez_hud_visible:
            self._inez_awareness_frame.pack(fill="x")

        hud_top = tk.Frame(self._inez_awareness_frame, bg="#1a0f3a")
        hud_top.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(hud_top, text="⚡ INEZ AWARENESS", bg="#1a0f3a", fg="#c4b5fd",
                 font=("Segoe UI", 8, "bold")).pack(side="left")

        def _dismiss_hud():
            self._inez_hud_visible = False
            try:
                self._inez_awareness_frame.pack_forget()
            except Exception:
                pass

        tk.Button(hud_top, text="✕", command=_dismiss_hud, bg="#1a0f3a", fg=TEXT_MUTED,
                  relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 9)).pack(side="right")

        awareness = self._inez_status.get("awareness", "")
        first_line = awareness.split("\n")[0][:200] if awareness else "All systems nominal."
        self._inez_awareness_label = tk.Label(self._inez_awareness_frame,
                                              text=first_line, bg="#1a0f3a", fg=TEXT_BODY,
                                              wraplength=500, justify="left",
                                              font=("Segoe UI", 9))
        self._inez_awareness_label.pack(anchor="w", padx=12, pady=(0, 8))

        # ── Quick Actions ─────────────────────────────────────────────────
        qa_frame = tk.Frame(parent, bg=BG_PANEL,
                            highlightbackground=BORDER_CARD, highlightthickness=1)
        qa_frame.pack(fill="x")
        qa_inner = tk.Frame(qa_frame, bg=BG_PANEL)
        qa_inner.pack(fill="x", padx=12, pady=8)
        for qa_label, qa_text in [
            ("Status",          "What's the current status of all missions?"),
            ("Brief Me",        "Give me a morning briefing."),
            ("Priorities",      "What needs my immediate attention?"),
            ("Recommendations", "What do you recommend I focus on today?"),
        ]:
            btn = tk.Button(qa_inner, text=qa_label,
                            command=lambda t=qa_text: self._inez_quick_send(t),
                            bg="#2d1b69", fg="#c4b5fd", relief="flat", bd=0,
                            padx=12, pady=4, cursor="hand2",
                            font=("Segoe UI", 9),
                            activebackground="#3d2b89", activeforeground="#e9d5ff")
            btn.pack(side="left", padx=(0, 6))

        # ── Bubble area + memory sidebar ──────────────────────────────────
        chat_shell = tk.Frame(parent, bg=BG_CANVAS)
        chat_shell.pack(fill="both", expand=True)

        chat_col = tk.Frame(chat_shell, bg=BG_CANVAS)
        chat_col.pack(side="left", fill="both", expand=True)
        mem_col = tk.Frame(chat_shell, bg=BG_CANVAS, width=220)
        mem_col.pack(side="right", fill="y", padx=(8, 0))
        mem_col.pack_propagate(False)

        bubble_outer = tk.Frame(chat_col, bg=BG_CANVAS)
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

        mem_card = self._card(mem_col, "Memory")
        mem_card.pack(fill="both", expand=True)
        self._inez_mem_listbox = tk.Text(
            mem_card,
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 9),
            wrap="word",
            height=18,
            state="disabled",
        )
        self._inez_mem_listbox.pack(fill="both", expand=True, padx=14, pady=14)
        self._refresh_inez_memory_sidebar()

        input_bar = tk.Frame(chat_col, bg=BG_PANEL,
                             highlightbackground=BORDER_CARD, highlightthickness=1)
        input_bar.pack(fill="x", side="bottom")

        self._chat_input = tk.Text(input_bar, height=3, bg=BG_INPUT, fg=TEXT_PRIMARY,
                                   insertbackground=ACCENT, relief="flat",
                                   font=("Segoe UI", 11), wrap="word", padx=10, pady=8)
        self._chat_input.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=8)
        self._chat_input.bind("<Return>", lambda e: (self._inez_send(), "break")[1])
        self._chat_input.bind("<Shift-Return>", lambda e: None)

        if not hasattr(self, "_inez_web_search_var"):
            self._inez_web_search_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            input_bar,
            text="Web search",
            variable=self._inez_web_search_var,
            bg=BG_PANEL,
            fg=TEXT_BODY,
            activebackground=BG_PANEL,
            activeforeground=TEXT_PRIMARY,
            selectcolor=BG_INPUT,
            highlightthickness=0,
        ).pack(side="right", padx=4)
        send_btn = self._button(input_bar, "  Send  ", self._inez_send)
        send_btn.pack(side="right", padx=10, pady=8, ipadx=10, ipady=6)
        tk.Label(input_bar, text="Enter ↵ send  ·  ⇧Enter newline",
                 bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(side="right", padx=4)


    def show_runs(self):
        self._set_active_nav("Runs")
        self._clear_content()
        self._section_header(self.content, "Runs", "Monitor historical and active agent runs.")

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        runs_tab = tk.Frame(notebook, bg=BG_CANVAS)
        sandbox_tab = tk.Frame(notebook, bg=BG_CANVAS)
        notebook.add(runs_tab, text="Runs")
        notebook.add(sandbox_tab, text="🖥 Sandbox")

        self._build_runs_main_tab(runs_tab)
        self._build_sandbox_tab(sandbox_tab)

    def _build_runs_main_tab(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal", sashwidth=6, bg=BG_CANVAS, relief="flat")
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

    def _build_sandbox_tab(self, parent):
        """Code execution sandbox tab."""
        top = tk.Frame(parent, bg=BG_CANVAS)
        top.pack(fill="x", padx=10, pady=(10, 4))

        status_lbl = tk.Label(top, text="Checking sandbox…", bg=BG_CANVAS, fg=TEXT_MUTED,
                              font=("Segoe UI", 9))
        status_lbl.pack(side="left")
        self._button(top, "▶ Run Code", lambda: self._run_sandbox_code(), accent=True).pack(side="right", padx=4)
        self._button(
            top,
            "Clear",
            lambda: (
                self._sandbox_editor.delete("1.0", "end"),
                self._sandbox_output.configure(state="normal"),
                self._sandbox_output.delete("1.0", "end"),
                self._sandbox_output.configure(state="disabled"),
            ),
        ).pack(side="right")

        editor_card = self._card(parent, "Code Editor")
        editor_card.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        self._sandbox_editor = tk.Text(
            editor_card,
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            font=("Consolas", 10),
            relief="flat",
            wrap="none",
            height=18,
        )
        self._sandbox_editor.pack(fill="both", expand=True, padx=10, pady=10)
        self._sandbox_editor.insert("1.0", "# Enter Python code here\nimport pandas as pd\nprint(pd.__version__)\n")

        out_card = self._card(parent, "Output")
        out_card.pack(fill="x", padx=10, pady=(0, 10))
        self._sandbox_output = tk.Text(
            out_card,
            bg=BG_INPUT,
            fg=SUCCESS,
            font=("Consolas", 9),
            relief="flat",
            height=8,
            state="disabled",
        )
        self._sandbox_output.pack(fill="both", expand=True, padx=10, pady=10)

        import threading as _t

        def _check():
            try:
                s = self.hub._get("/api/sandbox/status")
                if s:
                    docker = "🐳 Docker" if s.get("docker_available") else "⚙ subprocess"
                    self._ui_queue.put((
                        "configure",
                        status_lbl,
                        {"text": f"Sandbox ready — {docker} mode | timeout {s.get('timeout_seconds', 30)}s", "fg": SUCCESS},
                    ))
            except Exception:
                pass

        _t.Thread(target=_check, daemon=True).start()

    def _run_sandbox_code(self):
        if not hasattr(self, "_sandbox_editor"):
            return
        code = self._sandbox_editor.get("1.0", "end").strip()
        if not code:
            return
        import threading as _t, time

        self._sandbox_output.configure(state="normal")
        self._sandbox_output.delete("1.0", "end")
        self._sandbox_output.insert("end", "Running…\n")
        self._sandbox_output.configure(state="disabled")

        def _run():
            t0 = time.time()
            try:
                result = self.hub.post_json("/api/sandbox/execute", {"code": code, "language": "python"})
                elapsed = time.time() - t0
                lines = []
                if result:
                    if result.get("stdout"):
                        lines.append("── stdout ──")
                        lines.append(result["stdout"])
                    if result.get("stderr"):
                        lines.append("── stderr ──")
                        lines.append(result["stderr"])
                    if result.get("error"):
                        lines.append(f"── error: {result['error']} ──")
                    lines.append(f"\n⏱ {elapsed:.2f}s | exit {result.get('exit_code', 0)}")
                else:
                    lines.append("(no output)")
                self._ui_queue.put(("set_text", self._sandbox_output, "\n".join(lines)))
            except Exception as e:
                self._ui_queue.put(("set_text", self._sandbox_output, f"Error: {e}"))

        _t.Thread(target=_run, daemon=True).start()

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
        tab = OrgChartTab(self.content, callbacks={
            "run_agent":  self._org_run_agent,
            "ask_inez":   self._org_ask_inez,
            "view_runs":  self._org_view_runs,
            "view_skill": self._org_view_skill,
        })
        tab.pack(fill="both", expand=True)

    def _org_run_agent(self, agent_id: str, agent_label: str):
        """Called from Org chart — pre-populate and launch Runs tab for this agent."""
        self.quick_agent_var.set(agent_id)
        # Find and set the team
        for team, agents in AGENT_REGISTRY.items():
            if agent_id in agents:
                self.quick_team_var.set(team)
                break
        self.show_inez()
        # Pre-fill Inez with a run request
        msg = f"Run agent {agent_id} ({agent_label}) — what task should I give it?"
        try:
            if self._chat_input and self._chat_input.winfo_exists():
                self._chat_input.delete("1.0", "end")
                self._chat_input.insert("1.0", msg)
        except Exception:
            pass

    def _org_ask_inez(self, agent_id: str, agent_label: str):
        """Called from Org chart — open Inez tab with a pre-filled question about the agent."""
        self.show_inez()
        msg = f"Tell me about the {agent_label} agent ({agent_id}) — what is it responsible for and what's its current status?"
        try:
            if self._chat_input and self._chat_input.winfo_exists():
                self._chat_input.delete("1.0", "end")
                self._chat_input.insert("1.0", msg)
        except Exception:
            pass

    def _org_view_runs(self, agent_id: str):
        """Called from Org chart — jump to Runs tab filtered to this agent."""
        self.run_filter_agent_var.set(agent_id)
        self.show_runs()

    def _org_view_skill(self, agent_id: str, agent_label: str):
        """Called from Org chart — show skill file in a popup (handled by OrgChartTab itself as fallback)."""
        pass

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

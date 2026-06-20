"""
org_chart.py — ArchonHub Org Chart
====================================
Interactive hierarchical org chart for Smith Capital Group.

Features:
  • Full tree from Smith Capital Group → Divisions → Teams → Agents
  • Canvas-based render with zoom (scroll wheel) and pan (drag)
  • Expand / collapse subtrees — click the ▾/▸ triangle on parent nodes
  • Clickable nodes — detail panel with live action buttons
  • Action buttons: Run Agent · Ask Inez · View Runs · View Skill File
  • Double-click an agent node to launch Run Agent immediately
  • Division quick-nav chips — jump to any division in one click
  • Breadcrumb bar shows current selection path
  • Drag threshold — short drag does NOT misfire as a click
  • Color-coded divisions
  • Search/filter to highlight agents by name or role
  • Data-driven: agent details pulled from hub_db.agent_registry
  • Callbacks wired back to main app for cross-tab navigation
"""

from __future__ import annotations

import math
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

import sys
HERE = Path(__file__).parent
for _p in [HERE, HERE.parent.parent, HERE.parent.parent.parent]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import hub_db
    DB_OK = True
except Exception:
    DB_OK = False

try:
    from ah_logging import get_logger
    logger = get_logger("org_chart")
except Exception:
    import logging
    logger = logging.getLogger("org_chart")

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DARK    = "#0D1117"
BG_PANEL   = "#16213E"
BG_CANVAS  = "#0F3460"
BG_CARD    = "#1E2A45"
BG_RAIL    = "#1A1A2E"
TEXT_PRIMARY = "#E8EAF0"
TEXT_BODY    = "#B0B8C8"
TEXT_MUTED   = "#6B7A99"
ACCENT       = "#00B8FF"
SUCCESS      = "#00C864"
WARNING      = "#F5A623"
ERROR        = "#FF4444"
BORDER       = "#2A3A5C"

# Division colors (fill, border)
DIV_COLORS: dict[str, tuple[str, str]] = {
    "root":        ("#7c3aed", "#a78bfa"),   # purple — Smith Capital Group
    "executive":   ("#0e7490", "#22d3ee"),   # teal — Executive
    "holdings":    ("#1d4ed8", "#60a5fa"),   # blue — Holdings
    "finance":     ("#047857", "#34d399"),   # green — Finance
    "markets":     ("#b45309", "#fbbf24"),   # gold — Markets
    "portfolio":   ("#9d174d", "#f472b6"),   # pink — Portfolio Co.
    "legal":       ("#7c2d12", "#fb923c"),   # orange — Legal/Law
    "nonprofit":   ("#1e3a5f", "#93c5fd"),   # sky — Non-profit
    "social":      ("#4c1d95", "#c4b5fd"),   # violet — Social/Media
    "agent":       ("#1e2a45", "#00B8FF"),   # default agent
    "inez":        ("#5b21b6", "#a78bfa"),   # special for Inez
}

# ── Company hierarchy definition ──────────────────────────────────────────────

def _build_org_tree() -> dict:
    """
    Returns the full Smith Capital Group org tree as nested dicts.
    Each node: {id, label, role, division, children:[...], agent_id?}
    """
    def team(tid, label, role, div, agents: list[tuple[str,str]]) -> dict:
        return {
            "id": tid, "label": label, "role": role, "division": div,
            "children": [
                {"id": aid, "label": aname, "role": "Agent", "division": "agent",
                 "agent_id": aid, "children": []}
                for aid, aname in agents
            ],
        }

    return {
        "id":    "smith-capital-group",
        "label": "Smith Capital Group",
        "role":  "Parent Company",
        "division": "root",
        "children": [
            # ── Executive Office ─────────────────────────────────────────
            {
                "id": "executive-office", "label": "Executive Office",
                "role": "Leadership", "division": "executive",
                "children": [
                    {
                        "id": "inez", "label": "Inez",
                        "role": "Chief of Staff (AI)",
                        "division": "inez", "agent_id": "inez",
                        "children": [],
                    },
                ],
            },
            # ── Holdings Division ────────────────────────────────────────
            team("holdings-div", "Holdings", "Corporate Holdings", "holdings", [
                ("holdings-project-lead",  "Project Lead"),
                ("holdings-legal-agent",   "Legal"),
                ("holdings-finance-agent", "Finance"),
                ("holdings-tax-agent",     "Tax"),
                ("holdings-compliance-agent", "Compliance"),
            ]),
            # ── Finance & Capital Markets ────────────────────────────────
            {
                "id": "finance-markets", "label": "Finance & Capital Markets",
                "role": "Division", "division": "finance",
                "children": [
                    team("smithcap-finance", "SmithCap Finance", "Financial Services", "finance", [
                        ("finance-cfo",           "CFO"),
                        ("finance-cpa",           "CPA"),
                        ("finance-tax-strategist","Tax Strategist"),
                        ("finance-bookkeeper",    "Bookkeeper"),
                        ("finance-advisor",       "Advisor"),
                    ]),
                    team("markets-desk", "Markets Desk", "Investment & Trading", "markets", [
                        ("markets-project-lead",    "Project Lead"),
                        ("markets-cio",             "CIO"),
                        ("markets-cro",             "CRO"),
                        ("markets-options-strategist", "Options Strategist"),
                        ("markets-quant",           "Quant"),
                        ("markets-intelligence-desk","Intelligence Desk"),
                        ("markets-equity-analyst",  "Equity Analyst"),
                        ("markets-macro-analyst",   "Macro Analyst"),
                        ("markets-tactical-alpha",  "Tactical Alpha"),
                        ("markets-technical-analyst","Technical Analyst"),
                    ]),
                ],
            },
            # ── Portfolio Companies ──────────────────────────────────────
            {
                "id": "portfolio-div", "label": "Portfolio Companies",
                "role": "Division", "division": "portfolio",
                "children": [
                    team("xftc", "XFTC", "Fintech Platform", "portfolio", [
                        ("xftc-project-lead",  "Project Lead"),
                        ("xftc-plugin-dev",    "Plugin Dev"),
                        ("xftc-frontend-dev",  "Frontend Dev"),
                        ("xftc-payments-agent","Payments"),
                        ("xftc-qa-agent",      "QA"),
                    ]),
                    team("s2t-designs", "S2T Designs", "Design Agency", "portfolio", [
                        ("s2t-project-lead",  "Project Lead"),
                        ("s2t-webdev-agent",  "Web Dev"),
                        ("s2t-seo-agent",     "SEO"),
                    ]),
                    team("nutrue", "Nutrue", "Health & Wellness Brand", "portfolio", [
                        ("nutrue-project-lead",       "Project Lead"),
                        ("nutrue-brand-agent",        "Brand"),
                        ("nutrue-ecommerce-agent",    "eCommerce"),
                        ("nutrue-finance-agent",      "Finance"),
                        ("nutrue-inbro-retrofit-agent","InBro Retrofit"),
                        ("nutrue-legal-agent",        "Legal"),
                        ("nutrue-marketing-agent",    "Marketing"),
                    ]),
                    team("night-king", "Night King", "Media & Entertainment", "portfolio", [
                        ("nightking-project-lead", "Project Lead"),
                        ("nightking-brand-agent",  "Brand"),
                        ("nightking-design-agent", "Design"),
                        ("nightking-media-agent",  "Media"),
                    ]),
                    team("elevation", "The Elevation", "Events & Community", "portfolio", [
                        ("elevation-project-lead",   "Project Lead"),
                        ("elevation-brand-agent",    "Brand"),
                        ("elevation-events-agent",   "Events"),
                        ("elevation-funding-agent",  "Funding"),
                        ("elevation-legal-agent",    "Legal"),
                        ("elevation-marketing-agent","Marketing"),
                    ]),
                    team("solar", "Solar Repair", "Renewable Energy", "portfolio", [
                        ("solar-project-lead",    "Project Lead"),
                        ("solar-marketing-agent", "Marketing"),
                    ]),
                    team("sigma-signal", "Sigma Signal", "Signals & Research", "portfolio", [
                        ("sigma-signal-project-lead", "Project Lead"),
                        ("sigma-signal-writer",       "Writer"),
                    ]),
                ],
            },
            # ── Professional Services ────────────────────────────────────
            {
                "id": "prof-services", "label": "Professional Services",
                "role": "Division", "division": "legal",
                "children": [
                    team("business-law", "Business Law", "Legal Services", "legal", [
                        ("business-law-project-lead",      "Project Lead"),
                        ("business-law-entity-agent",      "Entity"),
                        ("business-law-contracts-agent",   "Contracts"),
                        ("business-law-ip-agent",          "IP"),
                        ("business-law-employment-agent",  "Employment"),
                        ("business-law-realestate-agent",  "Real Estate"),
                        ("business-law-regulatory-agent",  "Regulatory"),
                    ]),
                    team("ministry", "Ministry", "Faith & Community", "nonprofit", [
                        ("ministry-project-lead",  "Project Lead"),
                        ("ministry-sermon-writer", "Sermon Writer"),
                    ]),
                ],
            },
            # ── Community & Social Impact ────────────────────────────────
            {
                "id": "community-div", "label": "Community & Social Impact",
                "role": "Division", "division": "nonprofit",
                "children": [
                    team("pbs-foundation", "PBS Foundation", "Non-Profit", "nonprofit", [
                        ("pbs-project-lead",          "Project Lead"),
                        ("pbs-board-agent",           "Board"),
                        ("pbs-communications-agent",  "Communications"),
                        ("pbs-fundraising-agent",     "Fundraising"),
                        ("pbs-legal-agent",           "Legal"),
                        ("pbs-programs-agent",        "Programs"),
                    ]),
                    team("grants-yepc", "Grants / YEPC", "Grant Writing & Education", "nonprofit", [
                        ("grants-research-agent",         "Grants Research"),
                        ("grant-writer-agent",            "Grant Writer"),
                        ("yepc-grant-writer-agent",       "YEPC Grant Writer"),
                        ("yepc-real-estate-research-agent","Real Estate Research"),
                        ("yepc-project-manager",          "Project Manager"),
                    ]),
                    team("social-media", "Social Media", "Digital Marketing", "social", [
                        ("social-project-lead",       "Project Lead"),
                        ("social-content-strategist", "Content Strategist"),
                        ("social-copywriter",         "Copywriter"),
                        ("social-ads-manager",        "Ads Manager"),
                    ]),
                ],
            },
        ],
    }


# ── Layout engine ────────────────────────────────────────────────────────────

NODE_W   = 140   # node box width
NODE_H   = 48    # node box height
H_GAP    = 20    # horizontal gap between siblings
V_GAP    = 70    # vertical gap between levels


def _subtree_width(node: dict) -> float:
    """Recursively calculate the minimum width needed by a subtree."""
    if not node["children"]:
        return NODE_W
    children_width = sum(_subtree_width(c) for c in node["children"])
    gaps = H_GAP * (len(node["children"]) - 1)
    return max(NODE_W, children_width + gaps)


def _assign_positions(node: dict, x: float, y: float) -> None:
    """Assign (x, y) center coordinates to each node recursively."""
    node["_x"] = x
    node["_y"] = y
    if not node["children"]:
        return
    total_w  = sum(_subtree_width(c) for c in node["children"])
    total_w += H_GAP * (len(node["children"]) - 1)
    cx = x - total_w / 2
    for child in node["children"]:
        cw  = _subtree_width(child)
        _assign_positions(child, cx + cw / 2, y + NODE_H + V_GAP)
        cx += cw + H_GAP


def _collect_nodes(node: dict, out: list) -> None:
    out.append(node)
    for c in node.get("children", []):
        _collect_nodes(c, out)


def _collect_edges(node: dict, out: list) -> None:
    for c in node.get("children", []):
        out.append((node, c))
        _collect_edges(c, out)


# ── Org Chart Widget ─────────────────────────────────────────────────────────

class OrgChartTab(tk.Frame):
    """
    Full org chart panel. Embed in the main content area.

    callbacks (dict) — optional hooks wired to main app:
        "run_agent"  : fn(agent_id, agent_label)
        "ask_inez"   : fn(agent_id, agent_label)
        "view_runs"  : fn(agent_id)
        "view_skill" : fn(agent_id, agent_label)
    """

    MIN_ZOOM       = 0.25
    MAX_ZOOM       = 2.5
    DRAG_THRESHOLD = 6      # px — less than this = treat as click
    TOGGLE_RADIUS  = 9      # px — hit area for the ▾/▸ triangle badge

    def __init__(self, parent, callbacks=None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._cbs             = callbacks or {}
        self._zoom            = 0.7
        self._offset_x        = 0.0
        self._offset_y        = 40.0
        self._drag_start      = None
        self._drag_offset_start = None
        self._drag_dist       = 0.0
        self._last_click_time = 0.0
        self._selected_id:    str | None  = None
        self._selected_node:  dict | None = None
        self._collapsed:      set[str]    = set()   # IDs of collapsed parents
        self._all_nodes:      list[dict]  = []
        self._all_edges:      list        = []
        self._agent_db:       dict[str, dict] = {}
        self._node_by_id:     dict[str, dict] = {}
        self._parent_map:     dict[str, str]  = {}  # child_id → parent_id
        self._search_var      = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)

        self._build_ui()
        self._load_data()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG_RAIL)
        top.pack(fill="x")

        tk.Label(top, text="🏢  SMITH CAPITAL GROUP", bg=BG_RAIL, fg=ACCENT,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=14, pady=8)

        # Search
        tk.Label(top, text="🔍", bg=BG_RAIL, fg=TEXT_MUTED,
                 font=("Segoe UI", 11)).pack(side="left", padx=(20, 4))
        tk.Entry(top, textvariable=self._search_var, bg=BG_CARD, fg=TEXT_PRIMARY,
                 relief="flat", font=("Segoe UI", 10), width=22,
                 insertbackground=ACCENT).pack(side="left", ipady=4, padx=(0, 12))

        # Zoom controls
        self._zoom_lbl = tk.Label(top, text="70%", bg=BG_RAIL, fg=TEXT_BODY,
                                   font=("Segoe UI", 9), width=5)
        self._zoom_lbl.pack(side="right", padx=(0, 10))
        self._btn(top, "−", self._zoom_out).pack(side="right", padx=2, pady=6)
        self._btn(top, "Fit", self._fit_view).pack(side="right", padx=2, pady=6)
        self._btn(top, "+", self._zoom_in).pack(side="right", padx=2, pady=6)
        self._btn(top, "⟳", self._load_data).pack(side="right", padx=8, pady=6)
        self._btn(top, "⊞ Expand All", self._expand_all).pack(side="right", padx=2, pady=6)
        self._btn(top, "⊟ Collapse All", self._collapse_all).pack(side="right", padx=2, pady=6)

        # ── Division quick-nav chips ──────────────────────────────────────
        nav = tk.Frame(self, bg=BG_DARK)
        nav.pack(fill="x", padx=14, pady=(6, 0))
        tk.Label(nav, text="Jump to:", bg=BG_DARK, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(side="left", padx=(0, 8))

        div_chips = [
            ("🏛  Executive",    "executive-office"),
            ("🏢  Holdings",     "holdings-div"),
            ("💼  Finance",      "smithcap-finance"),
            ("📈  Markets",      "markets-desk"),
            ("🚀  Portfolio",    "portfolio-div"),
            ("⚖️  Prof. Svcs",   "prof-services"),
            ("🌱  Community",    "community-div"),
        ]
        for chip_label, node_id in div_chips:
            btn = tk.Button(
                nav, text=chip_label,
                command=lambda nid=node_id: self._jump_to_node(nid),
                bg=BG_CARD, fg=TEXT_BODY, relief="flat",
                padx=10, pady=3, cursor="hand2", font=("Segoe UI", 8),
                activebackground=BG_CANVAS, activeforeground=TEXT_PRIMARY,
            )
            btn.pack(side="left", padx=(0, 4))

        # ── Legend ─────────────────────────────────────────────────────────
        legend = tk.Frame(self, bg=BG_DARK)
        legend.pack(fill="x", padx=14, pady=(4, 0))
        legend_items = [
            ("root",      "Smith Capital"),
            ("executive", "Executive"),
            ("holdings",  "Holdings"),
            ("finance",   "Finance"),
            ("markets",   "Markets"),
            ("portfolio", "Portfolio"),
            ("legal",     "Prof. Services"),
            ("nonprofit", "Non-Profit"),
            ("social",    "Social / Media"),
        ]
        for div, label in legend_items:
            fill, _ = DIV_COLORS.get(div, DIV_COLORS["agent"])
            dot = tk.Canvas(legend, width=10, height=10, bg=BG_DARK, highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=fill, outline="")
            dot.pack(side="left", padx=(8, 2))
            tk.Label(legend, text=label, bg=BG_DARK, fg=TEXT_MUTED,
                     font=("Segoe UI", 8)).pack(side="left", padx=(0, 6))
        tk.Label(legend, text="  ▾ click to expand/collapse",
                 bg=BG_DARK, fg=TEXT_MUTED, font=("Segoe UI", 8, "italic")).pack(
                     side="right", padx=8)

        # ── Breadcrumb ─────────────────────────────────────────────────────
        bc_frame = tk.Frame(self, bg="#0a0f1a",
                            highlightbackground=BORDER, highlightthickness=1)
        bc_frame.pack(fill="x")
        tk.Label(bc_frame, text="📍", bg="#0a0f1a", fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(10, 4), pady=4)
        self._breadcrumb_label = tk.Label(
            bc_frame, text="Smith Capital Group",
            bg="#0a0f1a", fg=ACCENT, font=("Segoe UI", 9))
        self._breadcrumb_label.pack(side="left", pady=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Main split: canvas | detail ────────────────────────────────────
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        # Canvas
        canvas_frame = tk.Frame(body, bg=BG_DARK)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        self._canvas = tk.Canvas(canvas_frame, bg=BG_DARK,
                                  highlightthickness=0, cursor="fleur")
        vsb = tk.Scrollbar(canvas_frame, orient="vertical",   command=self._canvas.yview)
        hsb = tk.Scrollbar(canvas_frame, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._canvas.pack(fill="both", expand=True)

        self._canvas.bind("<ButtonPress-1>",   self._on_mouse_press)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_mouse_release)
        self._canvas.bind("<Double-Button-1>",  self._on_double_click)
        self._canvas.bind("<MouseWheel>",       self._on_mousewheel)
        self._canvas.bind("<Button-4>",         lambda e: self._zoom_step(1.1))
        self._canvas.bind("<Button-5>",         lambda e: self._zoom_step(0.9))

        # Detail panel
        self._detail_frame = tk.Frame(body, bg=BG_PANEL, width=280,
                                       highlightbackground=BORDER, highlightthickness=1)
        self._detail_frame.grid(row=0, column=1, sticky="nsew")
        self._detail_frame.pack_propagate(False)
        self._build_detail_panel()

    def _build_detail_panel(self):
        for w in self._detail_frame.winfo_children():
            w.destroy()

        tk.Label(self._detail_frame, text="Node Details", bg=BG_PANEL, fg=ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(14, 4))
        tk.Frame(self._detail_frame, bg=BORDER, height=1).pack(fill="x", padx=10)

        self._detail_name = tk.Label(self._detail_frame, text="—", bg=BG_PANEL,
                                      fg=TEXT_PRIMARY, font=("Segoe UI", 13, "bold"),
                                      wraplength=240, justify="left")
        self._detail_name.pack(anchor="w", padx=14, pady=(10, 2))

        self._detail_role = tk.Label(self._detail_frame, text="", bg=BG_PANEL,
                                      fg=ACCENT, font=("Segoe UI", 9))
        self._detail_role.pack(anchor="w", padx=14, pady=(0, 2))

        self._detail_div = tk.Label(self._detail_frame, text="", bg=BG_PANEL,
                                     fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._detail_div.pack(anchor="w", padx=14)

        tk.Frame(self._detail_frame, bg=BORDER, height=1).pack(fill="x", padx=10, pady=8)

        # ── Action buttons (shown for agent nodes) ─────────────────────────
        self._action_frame = tk.Frame(self._detail_frame, bg=BG_PANEL)
        self._action_frame.pack(fill="x", padx=14, pady=(0, 6))

        self._btn_run = self._action_btn(
            self._action_frame, "▶  Run Agent", "#1a4a1a", SUCCESS,
            lambda: self._action_run_agent())
        self._btn_run.pack(fill="x", pady=2)

        self._btn_inez = self._action_btn(
            self._action_frame, "👑  Ask Inez", "#2d1b69", "#c4b5fd",
            lambda: self._action_ask_inez())
        self._btn_inez.pack(fill="x", pady=2)

        self._btn_runs = self._action_btn(
            self._action_frame, "📊  View Runs", "#0a2a3a", ACCENT,
            lambda: self._action_view_runs())
        self._btn_runs.pack(fill="x", pady=2)

        self._btn_skill = self._action_btn(
            self._action_frame, "📄  View Skill File", "#1a1a2e", TEXT_BODY,
            lambda: self._action_view_skill())
        self._btn_skill.pack(fill="x", pady=2)

        # Hide action buttons until an agent node is selected
        self._action_frame.pack_forget()

        tk.Frame(self._detail_frame, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(4, 8))

        # DB details area
        db_frame = tk.Frame(self._detail_frame, bg=BG_PANEL)
        db_frame.pack(fill="x", padx=14)
        self._detail_status  = self._detail_kv(db_frame, "Status",  "—")
        self._detail_project = self._detail_kv(db_frame, "Project", "—")
        self._detail_children = self._detail_kv(db_frame, "Children", "—")

        tk.Frame(self._detail_frame, bg=BORDER, height=1).pack(fill="x", padx=10, pady=8)

        # Description / system_prompt preview
        tk.Label(self._detail_frame, text="Description", bg=BG_PANEL,
                 fg=TEXT_MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14)
        desc_frame = tk.Frame(self._detail_frame, bg=BG_CARD)
        desc_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        vsb2 = tk.Scrollbar(desc_frame)
        vsb2.pack(side="right", fill="y")
        self._detail_desc = tk.Text(desc_frame, bg=BG_CARD, fg=TEXT_BODY,
                                     font=("Segoe UI", 9), relief="flat",
                                     wrap="word", yscrollcommand=vsb2.set,
                                     padx=8, pady=6, height=8)
        self._detail_desc.pack(fill="both", expand=True)
        vsb2.config(command=self._detail_desc.yview)
        self._detail_desc.configure(state="disabled")

    def _action_btn(self, parent, text, bg, fg, command):
        return tk.Button(parent, text=text, command=command,
                         bg=bg, fg=fg, relief="flat", bd=0,
                         padx=10, pady=6, cursor="hand2",
                         font=("Segoe UI", 9, "bold"),
                         activebackground=BG_CANVAS, activeforeground=TEXT_PRIMARY,
                         anchor="w")

    def _detail_kv(self, parent, label: str, default: str) -> tk.Label:
        row = tk.Frame(parent, bg=BG_PANEL)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label + ":", bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Segoe UI", 8), width=10, anchor="w").pack(side="left")
        val = tk.Label(row, text=default, bg=BG_PANEL, fg=TEXT_BODY,
                       font=("Segoe UI", 9), anchor="w", wraplength=170, justify="left")
        val.pack(side="left", fill="x", expand=True)
        return val

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_data(self):
        self._tree = _build_org_tree()
        _assign_positions(self._tree, 0, 0)

        self._all_nodes = []
        self._all_edges = []
        _collect_nodes(self._tree, self._all_nodes)
        _collect_edges(self._tree, self._all_edges)

        # Build lookup maps
        self._node_by_id = {n["id"]: n for n in self._all_nodes}
        self._parent_map = {}
        for parent, child in self._all_edges:
            self._parent_map[child["id"]] = parent["id"]

        # Load agent DB records
        self._agent_db = {}
        if DB_OK:
            try:
                agents = hub_db.list_agents()
                self._agent_db = {a["agent_id"]: a for a in agents if a.get("agent_id")}
            except Exception:
                pass

        self._collapsed.clear()
        self._fit_view()

    # ── Visibility helpers (respects collapse state) ──────────────────────────

    def _is_visible(self, node: dict) -> bool:
        """Return True if all ancestors are expanded."""
        nid = node["id"]
        pid = self._parent_map.get(nid)
        while pid:
            if pid in self._collapsed:
                return False
            pid = self._parent_map.get(pid)
        return True

    def _visible_nodes(self) -> list[dict]:
        return [n for n in self._all_nodes if self._is_visible(n)]

    def _visible_edges(self) -> list[tuple]:
        return [(p, c) for p, c in self._all_edges
                if self._is_visible(p) and self._is_visible(c)
                and p["id"] not in self._collapsed]

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        return (wx * self._zoom + self._offset_x,
                wy * self._zoom + self._offset_y)

    def _screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        return ((sx - self._offset_x) / self._zoom,
                (sy - self._offset_y) / self._zoom)

    def _render(self):
        self._canvas.delete("all")
        vis_nodes = self._visible_nodes()
        if not vis_nodes:
            return

        search = self._search_var.get().strip().lower()

        # Draw edges first (behind nodes)
        for parent, child in self._visible_edges():
            px, py = self._world_to_screen(parent["_x"], parent["_y"] + NODE_H / 2)
            cx, cy = self._world_to_screen(child["_x"],  child["_y"]  - NODE_H / 2)
            mid_y  = (py + cy) / 2
            self._canvas.create_line(
                px, py, px, mid_y, cx, mid_y, cx, cy,
                fill=BORDER, width=1, smooth=False,
            )

        for node in vis_nodes:
            self._draw_node(node, search)

        # Update scroll region
        all_x = [n["_x"] for n in vis_nodes]
        all_y = [n["_y"] for n in vis_nodes]
        if all_x:
            mx = max(abs(min(all_x)), abs(max(all_x))) + NODE_W
            my = max(all_y) + NODE_H + 40
            sx1, sy1 = self._world_to_screen(-mx, -40)
            sx2, sy2 = self._world_to_screen(mx, my)
            self._canvas.configure(scrollregion=(sx1, sy1, sx2, sy2))

    def _draw_node(self, node: dict, search: str):
        nx, ny   = node["_x"], node["_y"]
        nid      = node["id"]
        div      = node.get("division", "agent")
        fill, border = DIV_COLORS.get(div, DIV_COLORS["agent"])
        selected = (nid == self._selected_id)
        label    = node["label"]
        role     = node.get("role", "")
        has_kids = bool(node.get("children"))
        collapsed = nid in self._collapsed

        match_search = (search and (search in label.lower() or search in role.lower()
                        or search in nid.lower()))
        if search and not match_search:
            fill   = "#1a1a2e"
            border = "#2a3a5c"

        x1, y1 = self._world_to_screen(nx - NODE_W / 2, ny - NODE_H / 2)
        x2, y2 = self._world_to_screen(nx + NODE_W / 2, ny + NODE_H / 2)
        r       = 8 * self._zoom

        pts = [
            x1+r, y1,  x2-r, y1,
            x2,   y1,  x2,   y1+r,
            x2,   y2-r,x2,   y2,
            x2-r, y2,  x1+r, y2,
            x1,   y2,  x1,   y2-r,
            x1,   y1+r,x1,   y1,
        ]
        outline_w = 3 if selected else (2 if match_search else 1)
        outline_c = ACCENT if selected else ("#fff" if match_search else border)
        tag     = f"node_{nid}"
        box_tag = f"box_{nid}"
        self._canvas.create_polygon(
            pts, fill=fill, outline=outline_c, width=outline_w,
            smooth=True, tags=(tag, box_tag, "node"),
        )

        # Status dot for agents
        if node.get("agent_id") and DB_OK:
            db_a   = self._agent_db.get(node["agent_id"], {})
            status = db_a.get("status", "")
            dot_c  = SUCCESS if status == "active" else (WARNING if status == "idle" else "#555")
            dx, dy = self._world_to_screen(nx + NODE_W / 2 - 8, ny - NODE_H / 2 + 8)
            r2 = 5 * self._zoom
            self._canvas.create_oval(dx-r2, dy-r2, dx+r2, dy+r2,
                                      fill=dot_c, outline="", tags=(tag,))

        # Expand/collapse triangle badge on parent nodes
        if has_kids and self._zoom > 0.3:
            tx, ty = self._world_to_screen(nx + NODE_W / 2 - 10, ny + NODE_H / 2 - 10)
            tri_size = max(6, 8 * self._zoom)
            tri_sym  = "▸" if collapsed else "▾"
            tri_tag  = f"toggle_{nid}"
            self._canvas.create_text(
                tx, ty, text=tri_sym, fill=ACCENT if not collapsed else WARNING,
                font=("Segoe UI", int(tri_size)), anchor="center",
                tags=(tri_tag, tag),
            )
            self._canvas.tag_bind(tri_tag, "<Button-1>",
                                   lambda e, n=node: (self._toggle_collapse(n), "break"))
            self._canvas.tag_bind(tri_tag, "<Enter>",
                                   lambda e: self._canvas.configure(cursor="hand2"))
            self._canvas.tag_bind(tri_tag, "<Leave>",
                                   lambda e: self._canvas.configure(cursor="fleur"))

        # Collapsed count badge
        if collapsed and has_kids:
            hidden = self._count_descendants(node)
            bx, by = self._world_to_screen(nx - NODE_W / 2 + 10, ny + NODE_H / 2 - 8)
            self._canvas.create_text(
                bx, by, text=f"+{hidden}", fill=TEXT_MUTED,
                font=("Segoe UI", max(6, int(8 * self._zoom))), anchor="w",
                tags=(tag,),
            )

        # Label text
        font_size = max(6, int(10 * self._zoom))
        role_size = max(5, int(8  * self._zoom))
        cx, cy = self._world_to_screen(nx, ny - 5)
        self._canvas.create_text(
            cx, cy, text=_truncate(label, 18), fill=TEXT_PRIMARY,
            font=("Segoe UI", font_size, "bold"), anchor="center", tags=(tag,),
        )
        if role and self._zoom > 0.45:
            rx, ry = self._world_to_screen(nx, ny + 10)
            self._canvas.create_text(
                rx, ry, text=_truncate(role, 22), fill=TEXT_MUTED,
                font=("Segoe UI", role_size), anchor="center", tags=(tag,),
            )

        # Hover + click bindings
        self._canvas.tag_bind(tag, "<Button-1>",
                               lambda e, n=node: self._on_node_click(n))
        self._canvas.tag_bind(tag, "<Enter>",
                               lambda e, t=box_tag: (
                                   self._canvas.itemconfigure(t, outline=ACCENT),
                                   self._canvas.configure(cursor="hand2")))
        self._canvas.tag_bind(tag, "<Leave>",
                               lambda e, t=box_tag, n=node, s=search: (
                                   self._canvas.itemconfigure(
                                       t, outline=ACCENT if n["id"] == self._selected_id else
                                       ("#fff" if s and s in n["label"].lower() else
                                        DIV_COLORS.get(n.get("division", "agent"),
                                                        DIV_COLORS["agent"])[1])),
                                   self._canvas.configure(cursor="fleur")))

    def _count_descendants(self, node: dict) -> int:
        return sum(1 + self._count_descendants(c) for c in node.get("children", []))

    # ── Node interaction ──────────────────────────────────────────────────────

    def _on_node_click(self, node: dict):
        self._selected_id   = node["id"]
        self._selected_node = node
        self._update_detail(node)
        self._update_breadcrumb(node)
        self._render()

    def _toggle_collapse(self, node: dict):
        if not node.get("children"):
            return
        nid = node["id"]
        if nid in self._collapsed:
            self._collapsed.discard(nid)
        else:
            self._collapsed.add(nid)
        self._render()

    def _expand_all(self):
        self._collapsed.clear()
        self._render()

    def _collapse_all(self):
        """Collapse all non-root parent nodes."""
        for n in self._all_nodes:
            if n.get("children") and n["id"] != self._tree["id"]:
                self._collapsed.add(n["id"])
        self._render()

    def _update_detail(self, node: dict):
        try:
            self._detail_name.configure(text=node["label"])
            self._detail_role.configure(text=node.get("role", ""))
            div = node.get("division", "agent")
            self._detail_div.configure(text=div.replace("_", " ").title())

            is_agent = bool(node.get("agent_id"))
            child_count = len(node.get("children", []))

            # Show/hide action buttons
            if is_agent:
                self._action_frame.pack(fill="x", padx=14, pady=(0, 6))
            else:
                self._action_frame.pack_forget()

            # DB record for agents
            aid  = node.get("agent_id", "")
            db_a = self._agent_db.get(aid, {}) if aid else {}

            self._detail_status.configure(
                text=db_a.get("status", "—") or "—",
                fg=SUCCESS if db_a.get("status") == "active" else TEXT_BODY,
            )
            self._detail_project.configure(text=db_a.get("project_slug", "—") or "—")
            self._detail_children.configure(
                text=f"{child_count} sub-nodes" if child_count else "Leaf node"
            )

            desc = (db_a.get("description", "") or
                    db_a.get("system_prompt", "") or
                    node.get("role", "") or "No description available.")
            self._detail_desc.configure(state="normal")
            self._detail_desc.delete("1.0", "end")
            self._detail_desc.insert("1.0", desc[:800])
            self._detail_desc.configure(state="disabled")
        except Exception as e:
            logger.debug("detail update error: %s", e)

    def _update_breadcrumb(self, node: dict):
        path = []
        nid  = node["id"]
        while nid:
            n = self._node_by_id.get(nid)
            if not n:
                break
            path.insert(0, n["label"])
            nid = self._parent_map.get(nid)
        crumb = "  ›  ".join(path) if path else node["label"]
        try:
            self._breadcrumb_label.configure(text=crumb)
        except Exception:
            pass

    # ── Action button handlers ────────────────────────────────────────────────

    def _action_run_agent(self):
        n = self._selected_node
        if n and n.get("agent_id"):
            cb = self._cbs.get("run_agent")
            if cb:
                cb(n["agent_id"], n["label"])

    def _action_ask_inez(self):
        n = self._selected_node
        if n and n.get("agent_id"):
            cb = self._cbs.get("ask_inez")
            if cb:
                cb(n["agent_id"], n["label"])

    def _action_view_runs(self):
        n = self._selected_node
        if n and n.get("agent_id"):
            cb = self._cbs.get("view_runs")
            if cb:
                cb(n["agent_id"])

    def _action_view_skill(self):
        n = self._selected_node
        if n and n.get("agent_id"):
            cb = self._cbs.get("view_skill")
            if cb:
                cb(n["agent_id"], n["label"])
            else:
                self._show_skill_popup(n["agent_id"], n["label"])

    def _show_skill_popup(self, agent_id: str, agent_label: str):
        """Fallback: show skill file content in a popup if no callback provided."""
        import importlib
        try:
            import hub_db as _db
            HERE2 = Path(__file__).parent
            AGENTS_DIR2 = HERE2.parent.parent.parent
            skill_dirs = [
                AGENTS_DIR2 / "agents" / "projects",
            ]
            content = None
            for d in skill_dirs:
                for f in d.rglob("*.md"):
                    if agent_id.replace("-", "_") in f.stem or agent_id in f.stem:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        break
                if content:
                    break
        except Exception:
            content = None

        popup = tk.Toplevel(self)
        popup.title(f"Skill File — {agent_label}")
        popup.configure(bg=BG_PANEL)
        popup.geometry("720x540")
        tk.Label(popup, text=f"📄 {agent_label}  ({agent_id})",
                 bg=BG_PANEL, fg=ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        txt_frame = tk.Frame(popup, bg=BG_CARD)
        txt_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        vsb = tk.Scrollbar(txt_frame)
        vsb.pack(side="right", fill="y")
        txt = tk.Text(txt_frame, bg=BG_CARD, fg=TEXT_BODY,
                      font=("Courier New", 9), relief="flat",
                      wrap="word", yscrollcommand=vsb.set, padx=10, pady=8)
        txt.pack(fill="both", expand=True)
        vsb.config(command=txt.yview)
        txt.insert("1.0", content or f"Skill file not found for agent: {agent_id}")
        txt.configure(state="disabled")
        tk.Button(popup, text="Close", command=popup.destroy,
                  bg=BG_CARD, fg=TEXT_BODY, relief="flat", padx=12, pady=6,
                  cursor="hand2").pack(pady=(0, 10))

    # ── Keyboard & mouse navigation ───────────────────────────────────────────

    def _on_mouse_press(self, event):
        self._drag_start        = (event.x, event.y)
        self._drag_offset_start = (self._offset_x, self._offset_y)
        self._drag_dist         = 0.0

    def _on_drag(self, event):
        if self._drag_start is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._drag_dist = (dx**2 + dy**2) ** 0.5
        self._offset_x  = self._drag_offset_start[0] + dx
        self._offset_y  = self._drag_offset_start[1] + dy
        self._render()

    def _on_mouse_release(self, event):
        self._drag_start = None

    def _on_double_click(self, event):
        """Double-click on an agent node = Run Agent immediately."""
        n = self._selected_node
        if n and n.get("agent_id"):
            self._action_run_agent()

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_step(1.1, event.x, event.y)
        else:
            self._zoom_step(0.9, event.x, event.y)

    def _zoom_step(self, factor: float, pivot_sx: float | None = None,
                   pivot_sy: float | None = None):
        old_zoom = self._zoom
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self._zoom * factor))
        if new_zoom == old_zoom:
            return
        if pivot_sx is None:
            pivot_sx = self._canvas.winfo_width()  / 2
            pivot_sy = self._canvas.winfo_height() / 2
        wx = (pivot_sx - self._offset_x) / old_zoom
        wy = (pivot_sy - self._offset_y) / old_zoom
        self._zoom      = new_zoom
        self._offset_x  = pivot_sx - wx * new_zoom
        self._offset_y  = pivot_sy - wy * new_zoom
        self._zoom_lbl.configure(text=f"{int(new_zoom*100)}%")
        self._render()

    def _zoom_in(self):  self._zoom_step(1.2)
    def _zoom_out(self): self._zoom_step(0.8)

    def _fit_view(self):
        self.update_idletasks()
        vis = self._visible_nodes()
        if not vis:
            return
        all_x  = [n["_x"] for n in vis]
        all_y  = [n["_y"] for n in vis]
        min_x, max_x = min(all_x) - NODE_W, max(all_x) + NODE_W
        min_y, max_y = min(all_y) - NODE_H, max(all_y) + NODE_H + 20
        tree_w = max_x - min_x
        tree_h = max_y - min_y
        cw = max(self._canvas.winfo_width(),  800)
        ch = max(self._canvas.winfo_height(), 600)
        zoom_x = cw / tree_w if tree_w else 1
        zoom_y = ch / tree_h if tree_h else 1
        self._zoom      = max(self.MIN_ZOOM, min(self.MAX_ZOOM, min(zoom_x, zoom_y) * 0.9))
        self._offset_x  = cw / 2 - ((min_x + max_x) / 2) * self._zoom
        self._offset_y  = 20 - min_y * self._zoom
        self._zoom_lbl.configure(text=f"{int(self._zoom*100)}%")
        self._render()

    def _jump_to_node(self, node_id: str):
        """Pan canvas to centre on the given node, select it."""
        node = self._node_by_id.get(node_id)
        if not node:
            return
        # Ensure all ancestors are expanded
        pid = self._parent_map.get(node_id)
        while pid:
            self._collapsed.discard(pid)
            pid = self._parent_map.get(pid)
        self._selected_id   = node_id
        self._selected_node = node
        self._update_detail(node)
        self._update_breadcrumb(node)
        # Centre canvas on the node
        self.update_idletasks()
        cw = max(self._canvas.winfo_width(),  800)
        ch = max(self._canvas.winfo_height(), 600)
        self._offset_x = cw / 2 - node["_x"] * self._zoom
        self._offset_y = ch / 2 - node["_y"] * self._zoom
        self._render()

    # ── Search ────────────────────────────────────────────────────────────────

    def _on_search(self, *_):
        self._render()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _btn(self, parent, text, command):
        return tk.Button(parent, text=text, command=command,
                         bg=BG_CARD, fg=TEXT_BODY, relief="flat",
                         padx=8, pady=3, cursor="hand2",
                         font=("Segoe UI", 9),
                         activebackground=BG_CANVAS, activeforeground=TEXT_PRIMARY)


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n-1] + "…"

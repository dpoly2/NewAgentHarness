"""
markets_tab.py — ArchonHub Markets Dashboard
=============================================
Hedge-fund style markets dashboard for the ArchonHub desktop app.

Surfaces:
  • Live ticker bar  — indices + macro tickers refreshing every 60s
  • Positions grid   — open equity/options positions with live P&L
  • Watchlist panel  — tracked tickers with live price + signal indicators
  • Reports panel    — latest markets agent reports (briefings, picks, P&L)
  • Quick-add dialogs for positions and watchlist items

Live data: yfinance (Yahoo Finance, free, no API key).
Fallback: Yahoo Finance JSON API via urllib if yfinance unavailable.
"""

from __future__ import annotations

import json
import queue
import threading
import time
import tkinter as tk
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tkinter import ttk
from typing import Any

import sys
HERE = Path(__file__).parent
HARNESS = HERE.parent.parent
AGENTS_DIR = HARNESS.parent
for _p in (HERE, HARNESS, AGENTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import hub_db

try:
    from ah_logging import get_logger
    logger = get_logger("markets_tab")
except Exception:
    import logging
    logger = logging.getLogger("markets_tab")

# ── Color palette (matches main_m365 theme) ──────────────────────────────────
BG_RAIL    = "#1A1A2E"
BG_PANEL   = "#16213E"
BG_CANVAS  = "#0F3460"
BG_CARD    = "#1E2A45"
BG_DARK    = "#0D1117"
TEXT_PRIMARY = "#E8EAF0"
TEXT_BODY    = "#B0B8C8"
TEXT_MUTED   = "#6B7A99"
ACCENT       = "#00B8FF"
ACCENT_LIGHT = "#33CAFF"
SUCCESS      = "#00C864"
ERROR        = "#FF4444"
WARNING      = "#F5A623"
BORDER_CARD  = "#2A3A5C"
GREEN        = "#00C864"
RED          = "#FF4444"

# Tickers in the live ticker bar
INDEX_TICKERS   = ["SPY", "QQQ", "IWM", "DIA"]
MACRO_TICKERS   = ["TLT", "GLD", "^VIX"]

# ── Live quote fetcher ────────────────────────────────────────────────────────

def _fetch_quote(ticker: str) -> dict:
    """Fetch a single live quote. Returns {"ticker", "price", "change", "change_pct", "prev_close", "state"}."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = float(info.last_price or 0)
        prev  = float(info.previous_close or price)
        chg   = price - prev
        pct   = (chg / prev * 100) if prev else 0.0
        return {
            "ticker":     ticker.replace("^", ""),
            "price":      price,
            "change":     round(chg, 2),
            "change_pct": round(pct, 2),
            "prev_close": prev,
            "state":      getattr(info, "market_state", "UNKNOWN"),
            "ok":         True,
        }
    except Exception:
        pass
    # Fallback via Yahoo Finance JSON
    try:
        import urllib.request, urllib.parse
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        meta  = data["chart"]["result"][0]["meta"]
        price = float(meta.get("regularMarketPrice") or 0)
        prev  = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price)
        chg   = price - prev
        pct   = (chg / prev * 100) if prev else 0.0
        return {
            "ticker": ticker.replace("^", ""),
            "price": price, "change": round(chg, 2),
            "change_pct": round(pct, 2), "prev_close": prev,
            "state": meta.get("marketState", "UNKNOWN"), "ok": True,
        }
    except Exception as e:
        return {"ticker": ticker.replace("^",""), "price":0, "change":0,
                "change_pct":0, "prev_close":0, "state":"ERR", "ok": False, "error": str(e)}


def _fetch_quotes(tickers: list[str]) -> dict[str, dict]:
    """Fetch multiple quotes, returning {ticker: quote_dict}."""
    results = {}
    try:
        import yfinance as yf
        cleaned = [t.replace("^", "") if not t.startswith("^") else t for t in tickers]
        batch = yf.download(tickers, period="1d", interval="1d", progress=False, auto_adjust=True)
        # yfinance batch may fail — fall through to per-ticker
        if batch.empty:
            raise ValueError("empty batch")
    except Exception:
        pass
    for t in tickers:
        results[t.replace("^", "")] = _fetch_quote(t)
    return results


# ── Main Markets Tab Widget ───────────────────────────────────────────────────

class MarketsTab(tk.Frame):
    """
    Full-screen markets dashboard. Embed in the main content area.
    Call .start_feed() after packing to begin live data refresh.
    Call .stop_feed() before destroying.
    """

    REFRESH_INTERVAL_S = 60   # live quote refresh rate

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._quotes: dict[str, dict] = {}          # live quote cache
        self._running = False
        self._feed_thread: threading.Thread | None = None
        self._queue: queue.Queue = queue.Queue()    # feed → UI updates

        self._build_ui()
        self._load_db_data()

    # ── Build layout ─────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_RAIL)
        hdr.pack(fill="x", padx=0, pady=0)
        tk.Label(hdr, text="📈  MARKETS DESK", bg=BG_RAIL, fg=ACCENT,
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=10)
        self._market_status_lbl = tk.Label(hdr, text="● Loading...", bg=BG_RAIL,
                                           fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._market_status_lbl.pack(side="left", padx=8)
        self._last_update_lbl = tk.Label(hdr, text="", bg=BG_RAIL, fg=TEXT_MUTED,
                                         font=("Segoe UI", 9))
        self._last_update_lbl.pack(side="right", padx=16)
        self._btn(hdr, "⟳ Refresh", self._manual_refresh).pack(side="right", padx=4, pady=8)
        self._btn(hdr, "+ Position", self._open_add_position).pack(side="right", padx=4, pady=8)
        self._btn(hdr, "+ Watchlist", self._open_add_watchlist).pack(side="right", padx=4, pady=8)
        self._btn(hdr, "▶ Run Brief", lambda: self._run_report("markets_daily_premarket_brief")).pack(side="right", padx=4, pady=8)

        # ── Ticker tape ───────────────────────────────────────────────────
        tape_frame = tk.Frame(self, bg=BG_PANEL, pady=6)
        tape_frame.pack(fill="x")
        self._ticker_labels: dict[str, tk.Label] = {}
        for sym in INDEX_TICKERS + MACRO_TICKERS:
            clean = sym.replace("^", "")
            lbl = tk.Label(tape_frame, text=f"{clean}  --", bg=BG_PANEL,
                           fg=TEXT_MUTED, font=("Consolas", 10, "bold"),
                           padx=12, pady=2)
            lbl.pack(side="left")
            tk.Label(tape_frame, text="|", bg=BG_PANEL,
                     fg=BORDER_CARD).pack(side="left")
            self._ticker_labels[clean] = lbl

        tk.Frame(self, bg=BORDER_CARD, height=1).pack(fill="x")

        # ── Sub-tab notebook ─────────────────────────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Markets.TNotebook",          background=BG_DARK, borderwidth=0)
        style.configure("Markets.TNotebook.Tab",      background=BG_RAIL, foreground=TEXT_BODY,
                         padding=(14,6), font=("Segoe UI",10))
        style.map("Markets.TNotebook.Tab",
                  background=[("selected", BG_CANVAS)],
                  foreground=[("selected", TEXT_PRIMARY)])

        self._notebook = ttk.Notebook(self, style="Markets.TNotebook")
        self._notebook.pack(fill="both", expand=True)

        # ── Tab 1: Live Market ────────────────────────────────────────────
        live_frame = tk.Frame(self._notebook, bg=BG_DARK)
        self._notebook.add(live_frame, text="📊  Live Market")
        self._build_live_market(live_frame)

        # ── Tab 2: Paper Trading ──────────────────────────────────────────
        paper_frame = tk.Frame(self._notebook, bg=BG_DARK)
        self._notebook.add(paper_frame, text="🧪  Paper Trading")
        self._paper_panel: "PaperTradingPanel | None" = None
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._paper_frame = paper_frame

    def _on_tab_changed(self, _event):
        """Lazy-load the paper trading panel on first switch to that tab."""
        sel = self._notebook.index("current")
        if sel == 1 and self._paper_panel is None:
            try:
                from paper_trading import PaperTradingPanel
                self._paper_panel = PaperTradingPanel(self._paper_frame,
                                                       ui_queue=self._queue)
                self._paper_panel.pack(fill="both", expand=True)
            except Exception as e:
                tk.Label(self._paper_frame,
                         text=f"Paper trading panel failed to load:\n{e}",
                         bg=BG_DARK, fg=ERROR,
                         font=("Segoe UI",10)).pack(expand=True)

    def _build_live_market(self, parent):
        """Build the existing positions/watchlist/reports layout inside parent."""
        # ── Main body split: left (positions+watchlist) | right (reports) ─
        body = tk.Frame(parent, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left  = tk.Frame(body, bg=BG_DARK)
        right = tk.Frame(body, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        # ── Left: Positions ───────────────────────────────────────────────
        self._build_positions_panel(left)

        # ── Left: Watchlist below positions ──────────────────────────────
        self._build_watchlist_panel(left)

        # ── Right: Reports ────────────────────────────────────────────────
        self._build_reports_panel(right)

    def _build_positions_panel(self, parent):
        hdr = tk.Frame(parent, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="💼  OPEN POSITIONS", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        self._pnl_summary_lbl = tk.Label(hdr, text="P&L: --", bg=BG_DARK,
                                         fg=TEXT_MUTED, font=("Segoe UI", 10))
        self._pnl_summary_lbl.pack(side="right")

        cols = ("Ticker", "Type", "Shares", "Entry", "Current", "P&L", "P&L%", "Target", "Stop")
        self._pos_tree = ttk.Treeview(parent, columns=cols, show="headings",
                                       height=8, selectmode="browse")
        widths = (60, 60, 60, 65, 70, 75, 60, 65, 65)
        for col, w in zip(cols, widths):
            self._pos_tree.heading(col, text=col)
            self._pos_tree.column(col, width=w, anchor="e" if col not in ("Ticker","Type") else "w")
        self._pos_tree.tag_configure("gain",   foreground=GREEN)
        self._pos_tree.tag_configure("loss",   foreground=RED)
        self._pos_tree.tag_configure("flat",   foreground=TEXT_BODY)
        self._pos_tree.pack(fill="x")

        # Scrollbar
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self._pos_tree.yview)
        self._pos_tree.configure(yscroll=vsb.set)

        # Context menu
        self._pos_tree.bind("<Button-3>", self._pos_right_click)
        self._pos_tree.bind("<Double-1>", lambda e: self._open_edit_position())

        btn_bar = tk.Frame(parent, bg=BG_DARK)
        btn_bar.pack(fill="x", pady=(4, 12))
        self._btn(btn_bar, "+ Add",  self._open_add_position, accent=True).pack(side="left", padx=2)
        self._btn(btn_bar, "Close",  self._close_selected_position).pack(side="left", padx=2)
        self._btn(btn_bar, "Edit",   self._open_edit_position).pack(side="left", padx=2)
        self._btn(btn_bar, "Delete", self._delete_selected_position).pack(side="left", padx=2)

    def _build_watchlist_panel(self, parent):
        hdr = tk.Frame(parent, bg=BG_DARK)
        hdr.pack(fill="x", pady=(4, 4))
        tk.Label(hdr, text="👁  WATCHLIST", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        cols = ("Ticker", "Name", "Price", "Chg%", "Target", "Signal")
        self._watch_tree = ttk.Treeview(parent, columns=cols, show="headings",
                                         height=7, selectmode="browse")
        w2 = (60, 160, 75, 65, 70, 80)
        for col, w in zip(cols, w2):
            self._watch_tree.heading(col, text=col)
            self._watch_tree.column(col, width=w,
                                     anchor="w" if col in ("Ticker","Name","Signal") else "e")
        self._watch_tree.tag_configure("up",   foreground=GREEN)
        self._watch_tree.tag_configure("down", foreground=RED)
        self._watch_tree.tag_configure("flat", foreground=TEXT_BODY)
        self._watch_tree.pack(fill="x")

        btn_bar = tk.Frame(parent, bg=BG_DARK)
        btn_bar.pack(fill="x", pady=(4, 8))
        self._btn(btn_bar, "+ Add",   self._open_add_watchlist, accent=True).pack(side="left", padx=2)
        self._btn(btn_bar, "Remove",  self._remove_watchlist_item).pack(side="left", padx=2)

    def _build_reports_panel(self, parent):
        tk.Label(parent, text="📊  LATEST REPORTS", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self._btn(parent, "▶ Run Weekly Picks", lambda: self._run_report("markets_weekly_picks_digest"),
                  accent=True).pack(anchor="w", pady=(0, 6))

        report_outer = tk.Frame(parent, bg=BG_DARK)
        report_outer.pack(fill="both", expand=True)
        vsb = tk.Scrollbar(report_outer)
        vsb.pack(side="right", fill="y")
        self._reports_canvas = tk.Canvas(report_outer, bg=BG_DARK,
                                          yscrollcommand=vsb.set, highlightthickness=0)
        self._reports_canvas.pack(side="left", fill="both", expand=True)
        vsb.config(command=self._reports_canvas.yview)
        self._reports_inner = tk.Frame(self._reports_canvas, bg=BG_DARK)
        self._reports_canvas.create_window((0, 0), window=self._reports_inner, anchor="nw")
        self._reports_inner.bind("<Configure>",
            lambda e: self._reports_canvas.configure(
                scrollregion=self._reports_canvas.bbox("all")))

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_db_data(self):
        self._refresh_positions()
        self._refresh_watchlist()
        self._refresh_reports_panel()

    def _refresh_positions(self):
        self._pos_tree.delete(*self._pos_tree.get_children())
        positions = hub_db.list_positions("open")
        total_pnl = 0.0
        for pos in positions:
            pnl     = pos.get("pnl", 0) or 0
            pnl_pct = pos.get("pnl_pct", 0) or 0
            cur     = pos.get("current_price", 0) or 0
            entry   = pos.get("entry_price", 0) or 0
            tag     = "gain" if pnl > 0 else ("loss" if pnl < 0 else "flat")
            pnl_str = f"${pnl:+,.2f}" if pnl else "--"
            pct_str = f"{pnl_pct:+.2f}%" if pnl_pct else "--"
            self._pos_tree.insert("", "end", iid=pos["id"], tags=(tag,), values=(
                pos.get("ticker",""),
                pos.get("position_type",""),
                f"{pos.get('shares',0):,.0f}",
                f"${entry:.2f}" if entry else "--",
                f"${cur:.2f}"   if cur   else "--",
                pnl_str,
                pct_str,
                f"${pos.get('target_price',0):.2f}" if pos.get("target_price") else "--",
                f"${pos.get('stop_price',0):.2f}"   if pos.get("stop_price")   else "--",
            ))
            total_pnl += pnl
        color = GREEN if total_pnl > 0 else (RED if total_pnl < 0 else TEXT_MUTED)
        try:
            self._pnl_summary_lbl.configure(
                text=f"Total P&L: ${total_pnl:+,.2f}", fg=color)
        except Exception:
            pass

    def _refresh_watchlist(self):
        self._watch_tree.delete(*self._watch_tree.get_children())
        items = hub_db.list_watchlist()
        for item in items:
            ticker = item.get("ticker", "")
            quote  = self._quotes.get(ticker, {})
            price  = quote.get("price", 0)
            pct    = quote.get("change_pct", 0)
            target = item.get("target_price", 0)
            tag    = "up" if pct > 0 else ("down" if pct < 0 else "flat")
            signal = self._compute_signal(ticker, price, target)
            self._watch_tree.insert("", "end", iid=ticker, tags=(tag,), values=(
                ticker,
                item.get("name", ""),
                f"${price:.2f}" if price else "--",
                f"{pct:+.2f}%" if price else "--",
                f"${target:.2f}" if target else "--",
                signal,
            ))

    def _refresh_reports_panel(self):
        for child in self._reports_inner.winfo_children():
            child.destroy()
        try:
            reports = hub_db.list_reports(project_slug="markets", limit=10)
        except Exception:
            reports = []
        if not reports:
            tk.Label(self._reports_inner,
                     text="No markets reports yet.\nRun a report job to generate data.",
                     bg=BG_DARK, fg=TEXT_MUTED, justify="left").pack(anchor="w", padx=8, pady=20)
            return
        for r in reports:
            self._render_report_card(r)

    def _render_report_card(self, report: dict):
        card = tk.Frame(self._reports_inner, bg=BG_CARD,
                        highlightbackground=BORDER_CARD, highlightthickness=1)
        card.pack(fill="x", padx=4, pady=4)
        status = report.get("status", "complete")
        badge_color = SUCCESS if status == "complete" else (WARNING if status == "partial" else ERROR)

        top = tk.Frame(card, bg=BG_CARD)
        top.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(top, text=report.get("title", "")[:60], bg=BG_CARD, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(top, text=f"● {status}", bg=BG_CARD, fg=badge_color,
                 font=("Segoe UI", 8)).pack(side="right")

        gen_at = report.get("generated_at", "")[:16].replace("T", " ")
        tk.Label(card, text=gen_at, bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=10)

        summary = (report.get("summary") or "")[:200]
        if summary and summary not in ("Generating...", "Running..."):
            tk.Label(card, text=summary, bg=BG_CARD, fg=TEXT_BODY,
                     wraplength=380, justify="left",
                     font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 2))

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", padx=10, pady=(4, 8))
        self._btn(btn_row, "View",
                  lambda r=report: self._view_report(r)).pack(side="left", padx=2)

    # ── Live feed ─────────────────────────────────────────────────────────────

    def start_feed(self):
        """Start background ticker refresh thread."""
        if self._running:
            return
        self._running = True
        self._feed_thread = threading.Thread(target=self._feed_loop, daemon=True)
        self._feed_thread.start()
        self._poll_queue()

    def stop_feed(self):
        """Stop the live feed thread."""
        self._running = False

    def _feed_loop(self):
        """Background thread: fetch quotes, put updates in queue."""
        all_tickers = INDEX_TICKERS + MACRO_TICKERS
        # Also pull watchlist tickers
        try:
            wl_tickers = [w["ticker"] for w in hub_db.list_watchlist()]
            all_tickers = list(dict.fromkeys(all_tickers + wl_tickers))
        except Exception:
            pass
        while self._running:
            quotes: dict[str, dict] = {}
            for ticker in all_tickers:
                if not self._running:
                    break
                quotes[ticker.replace("^", "")] = _fetch_quote(ticker)
                time.sleep(0.2)   # throttle to avoid rate-limit
            if quotes:
                self._queue.put(("quotes", quotes))
            # Sleep for interval, checking for stop
            for _ in range(self.REFRESH_INTERVAL_S * 2):
                if not self._running:
                    break
                time.sleep(0.5)

    def _poll_queue(self):
        """Process feed updates on the main thread via after()."""
        try:
            while True:
                kind, data = self._queue.get_nowait()
                if kind == "quotes":
                    self._apply_quotes(data)
                elif kind == "refresh_all":
                    self._load_db_data()
        except queue.Empty:
            pass
        if self._running:
            try:
                self.after(500, self._poll_queue)
            except Exception:
                pass

    def _apply_quotes(self, quotes: dict[str, dict]):
        """Apply fetched quotes to UI and DB."""
        self._quotes.update(quotes)
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        # Update ticker tape
        for sym, q in quotes.items():
            if sym not in self._ticker_labels:
                continue
            price = q.get("price", 0)
            pct   = q.get("change_pct", 0)
            chg   = q.get("change", 0)
            arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "—")
            color = GREEN if chg > 0 else (RED if chg < 0 else TEXT_BODY)
            text  = f"{sym}  ${price:,.2f} {arrow}{pct:+.2f}%"
            try:
                self._ticker_labels[sym].configure(text=text, fg=color)
            except Exception:
                pass

        # Update open position prices in DB
        for sym, q in quotes.items():
            if q.get("price"):
                try:
                    hub_db.update_position_price(sym, q["price"])
                except Exception:
                    pass

        # Determine market state
        states = [q.get("state", "") for q in quotes.values()]
        if "REGULAR" in states:
            market_state = "● Market Open"
            state_color  = GREEN
        elif "PRE" in states:
            market_state = "○ Pre-Market"
            state_color  = WARNING
        elif "POST" in states:
            market_state = "○ After-Hours"
            state_color  = ACCENT
        else:
            market_state = "● Market Closed"
            state_color  = TEXT_MUTED

        try:
            self._market_status_lbl.configure(text=market_state, fg=state_color)
            self._last_update_lbl.configure(text=f"Updated {now_str}")
        except Exception:
            pass

        # Refresh grids
        self._refresh_positions()
        self._refresh_watchlist()

        # Forward live prices to paper trading panel
        if self._paper_panel is not None:
            for sym, q in quotes.items():
                if q.get("price"):
                    try:
                        self._paper_panel.inject_quote(sym, q["price"])
                    except Exception:
                        pass

    def _manual_refresh(self):
        """Force an immediate quote fetch."""
        threading.Thread(
            target=lambda: self._queue.put(("quotes", _fetch_quotes(
                INDEX_TICKERS + MACRO_TICKERS +
                [w["ticker"] for w in hub_db.list_watchlist()]
            ))),
            daemon=True,
        ).start()

    # ── Signal logic ──────────────────────────────────────────────────────────

    @staticmethod
    def _compute_signal(ticker: str, price: float, target: float) -> str:
        if not price:
            return "—"
        if target and price >= target * 0.98:
            return "🎯 AT TARGET"
        if target and price <= target * 1.05:
            return "📈 BUY ZONE"
        return "MONITOR"

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _open_add_position(self):
        self._open_position_dialog(None)

    def _open_edit_position(self):
        sel = self._pos_tree.selection()
        if not sel:
            return
        pos = hub_db.get_position(sel[0])
        if pos:
            self._open_position_dialog(pos)

    def _open_position_dialog(self, pos: dict | None):
        dlg = tk.Toplevel(self)
        dlg.title("Position" if not pos else f"Edit {pos.get('ticker','')}")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("420x580")
        dlg.transient(self)
        dlg.grab_set()

        fields = {
            "ticker":        tk.StringVar(value=pos.get("ticker","") if pos else ""),
            "name":          tk.StringVar(value=pos.get("name","") if pos else ""),
            "shares":        tk.StringVar(value=str(pos.get("shares",0)) if pos else ""),
            "entry_price":   tk.StringVar(value=str(pos.get("entry_price",0)) if pos else ""),
            "target_price":  tk.StringVar(value=str(pos.get("target_price",0)) if pos else ""),
            "stop_price":    tk.StringVar(value=str(pos.get("stop_price",0)) if pos else ""),
            "position_type": tk.StringVar(value=pos.get("position_type","equity") if pos else "equity"),
            "action":        tk.StringVar(value=pos.get("action","long") if pos else "long"),
        }

        row = 0
        labels = [
            ("Ticker *",    "ticker"),
            ("Name",        "name"),
            ("Shares",      "shares"),
            ("Entry Price", "entry_price"),
            ("Target",      "target_price"),
            ("Stop Loss",   "stop_price"),
        ]
        for lbl_text, key in labels:
            tk.Label(dlg, text=lbl_text, bg=BG_PANEL, fg=TEXT_BODY,
                     font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=16, pady=(8 if row==0 else 4, 2))
            entry = tk.Entry(dlg, textvariable=fields[key], bg=BG_CANVAS, fg=TEXT_PRIMARY,
                             font=("Segoe UI", 10), relief="flat",
                             insertbackground=TEXT_PRIMARY)
            entry.grid(row=row+1, column=0, sticky="ew", padx=16)
            row += 2

        tk.Label(dlg, text="Type", bg=BG_PANEL, fg=TEXT_BODY).grid(row=row, column=0, sticky="w", padx=16, pady=(4,2))
        ttk.Combobox(dlg, textvariable=fields["position_type"],
                     values=["equity","options","etf","crypto","other"],
                     state="readonly").grid(row=row+1, column=0, sticky="ew", padx=16)
        row += 2

        tk.Label(dlg, text="Direction", bg=BG_PANEL, fg=TEXT_BODY).grid(row=row, column=0, sticky="w", padx=16, pady=(4,2))
        ttk.Combobox(dlg, textvariable=fields["action"],
                     values=["long","short"], state="readonly").grid(row=row+1, column=0, sticky="ew", padx=16)
        row += 2

        def _save():
            t = fields["ticker"].get().strip().upper()
            if not t:
                return
            hub_db.upsert_position(
                ticker=t,
                name=fields["name"].get().strip(),
                shares=float(fields["shares"].get() or 0),
                entry_price=float(fields["entry_price"].get() or 0),
                target_price=float(fields["target_price"].get() or 0),
                stop_price=float(fields["stop_price"].get() or 0),
                position_type=fields["position_type"].get(),
                action=fields["action"].get(),
                id=pos.get("id") if pos else None,
            )
            dlg.destroy()
            self._refresh_positions()

        btn_row = tk.Frame(dlg, bg=BG_PANEL)
        btn_row.grid(row=row, column=0, sticky="e", padx=16, pady=16)
        self._btn(btn_row, "Cancel", dlg.destroy).pack(side="left", padx=4)
        self._btn(btn_row, "Save", _save, accent=True).pack(side="left", padx=4)
        dlg.columnconfigure(0, weight=1)

    def _close_selected_position(self):
        sel = self._pos_tree.selection()
        if sel:
            hub_db.close_position(sel[0])
            self._refresh_positions()

    def _delete_selected_position(self):
        sel = self._pos_tree.selection()
        if sel:
            hub_db.delete_position(sel[0])
            self._refresh_positions()

    def _pos_right_click(self, event):
        item = self._pos_tree.identify_row(event.y)
        if not item:
            return
        self._pos_tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=TEXT_PRIMARY,
                       activebackground=ACCENT, activeforeground=BG_RAIL)
        menu.add_command(label="Edit",   command=self._open_edit_position)
        menu.add_command(label="Close Position", command=self._close_selected_position)
        menu.add_separator()
        menu.add_command(label="Delete", command=self._delete_selected_position)
        menu.post(event.x_root, event.y_root)

    def _open_add_watchlist(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add to Watchlist")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("340x360")
        dlg.transient(self)
        dlg.grab_set()

        fields = {
            "ticker":       tk.StringVar(),
            "name":         tk.StringVar(),
            "category":     tk.StringVar(value="watchlist"),
            "target_price": tk.StringVar(value="0"),
            "notes":        tk.StringVar(),
        }
        labels = [("Ticker *","ticker"),("Name","name"),("Target Price","target_price"),("Notes","notes")]
        row = 0
        for lbl_text, key in labels:
            tk.Label(dlg, text=lbl_text, bg=BG_PANEL, fg=TEXT_BODY).grid(
                row=row, column=0, sticky="w", padx=16, pady=(8 if row==0 else 4, 2))
            tk.Entry(dlg, textvariable=fields[key], bg=BG_CANVAS, fg=TEXT_PRIMARY,
                     relief="flat", insertbackground=TEXT_PRIMARY).grid(
                row=row+1, column=0, sticky="ew", padx=16)
            row += 2

        tk.Label(dlg, text="Category", bg=BG_PANEL, fg=TEXT_BODY).grid(
            row=row, column=0, sticky="w", padx=16, pady=(4,2))
        ttk.Combobox(dlg, textvariable=fields["category"],
                     values=["watchlist","index","macro","core","options","sector"],
                     state="readonly").grid(row=row+1, column=0, sticky="ew", padx=16)
        row += 2

        def _save():
            t = fields["ticker"].get().strip().upper()
            if not t:
                return
            hub_db.upsert_watchlist(
                ticker=t, name=fields["name"].get().strip(),
                category=fields["category"].get(),
                target_price=float(fields["target_price"].get() or 0),
                notes=fields["notes"].get().strip(),
            )
            dlg.destroy()
            self._refresh_watchlist()

        btn_row = tk.Frame(dlg, bg=BG_PANEL)
        btn_row.grid(row=row, column=0, sticky="e", padx=16, pady=16)
        self._btn(btn_row, "Cancel", dlg.destroy).pack(side="left", padx=4)
        self._btn(btn_row, "Add", _save, accent=True).pack(side="left", padx=4)
        dlg.columnconfigure(0, weight=1)

    def _remove_watchlist_item(self):
        sel = self._watch_tree.selection()
        if sel:
            hub_db.remove_from_watchlist(sel[0])
            self._refresh_watchlist()

    def _view_report(self, report: dict):
        dlg = tk.Toplevel(self)
        dlg.title(report.get("title","Report"))
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("860x680")
        dlg.transient(self)

        tk.Label(dlg, text=report.get("title",""), bg=BG_PANEL, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(12,2))
        gen_at = report.get("generated_at","")[:16].replace("T"," ")
        tk.Label(dlg, text=f"Generated: {gen_at}  |  By: {report.get('generated_by','')[:50]}",
                 bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI",9)).pack(anchor="w", padx=16, pady=(0,8))
        tk.Frame(dlg, bg=BORDER_CARD, height=1).pack(fill="x", padx=16, pady=4)

        frame = tk.Frame(dlg, bg=BG_PANEL)
        frame.pack(fill="both", expand=True, padx=16, pady=(0,12))
        vsb = tk.Scrollbar(frame)
        vsb.pack(side="right", fill="y")
        txt = tk.Text(frame, bg=BG_DARK, fg=TEXT_BODY, font=("Consolas",10),
                      relief="flat", wrap="word", yscrollcommand=vsb.set, padx=12, pady=8)
        txt.pack(fill="both", expand=True)
        vsb.config(command=txt.yview)
        txt.insert("1.0", report.get("content","") or report.get("summary","No content."))
        txt.configure(state="disabled")
        self._btn(dlg, "Close", dlg.destroy, accent=True).pack(pady=(0,12))

    def _run_report(self, job_id: str):
        """Trigger a report job — calls report_monitor directly (no HTTP auth needed)."""
        def _do():
            try:
                from report_monitor import run_report_job_sync
                run_report_job_sync(job_id)
                # Refresh after job completes
                self._queue.put(("refresh_all", None))
            except Exception as e:
                logger.warning("Report job failed: %s", e)
        threading.Thread(target=_do, daemon=True).start()

    # ── Helper widgets ────────────────────────────────────────────────────────

    def _btn(self, parent, text, command, accent=False):
        bg = ACCENT if accent else BG_CARD
        fg = BG_RAIL if accent else TEXT_BODY
        b = tk.Button(parent, text=text, command=command,
                      bg=bg, fg=fg, relief="flat", padx=8, pady=3,
                      cursor="hand2", font=("Segoe UI", 9),
                      activebackground=ACCENT_LIGHT if accent else BG_CANVAS,
                      activeforeground=BG_RAIL)
        return b

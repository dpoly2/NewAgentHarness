"""
paper_trading.py — ArchonHub Paper Trading Panel
=================================================
Simulates trades with dummy money to test agent-suggested strategies.

Features:
  • Theories — named hypotheses (e.g. "High-IV CSP Income", "Momentum Breakouts")
    each with a configurable starting balance (default $100k)
  • Paper Trades — open/close positions against a theory's balance
    trades auto-loaded from agent suggestions or entered manually
  • Live P&L — prices update from the live ticker feed
  • Auto-analysis — when a trade closes, markets-equity-analyst or
    markets-options-strategist runs via agent_runner to analyse the outcome
  • Stats dashboard — win rate, avg win/loss, R:R ratio, total return %
  • Export summary — generate a full theory report via agent
"""

from __future__ import annotations

import json
import queue
import threading
import time
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import ttk
from typing import Any, Callable

import sys
HERE = Path(__file__).parent
for _p in [HERE, HERE.parent.parent, HERE.parent.parent.parent]:
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import hub_db

try:
    from ah_logging import get_logger
    logger = get_logger("paper_trading")
except Exception:
    import logging
    logger = logging.getLogger("paper_trading")

# ── Theme ─────────────────────────────────────────────────────────────────────
BG_DARK    = "#0D1117"
BG_PANEL   = "#16213E"
BG_CANVAS  = "#0F3460"
BG_CARD    = "#1E2A45"
BG_RAIL    = "#1A1A2E"
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PaperTradingPanel(tk.Frame):
    """
    Embeddable paper trading panel. Place inside a ttk.Notebook tab.
    Call inject_quote(ticker, price) from the live feed to update P&L.
    """

    def __init__(self, parent, ui_queue: queue.Queue | None = None, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._selected_theory_id: str | None = None
        self._ui_queue = ui_queue  # shared queue back to main app for notifications
        self._build_ui()
        self._load_theories()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Top: Theory selector + controls ───────────────────────────────
        ctrl = tk.Frame(self, bg=BG_RAIL)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="🧪  THEORY:", bg=BG_RAIL, fg=ACCENT,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(12,4), pady=8)

        self._theory_var = tk.StringVar()
        self._theory_combo = ttk.Combobox(ctrl, textvariable=self._theory_var,
                                           state="readonly", width=40,
                                           font=("Segoe UI", 10))
        self._theory_combo.pack(side="left", padx=(0,8))
        self._theory_combo.bind("<<ComboboxSelected>>", self._on_theory_select)

        self._btn(ctrl, "+ New Theory", self._open_new_theory_dialog, accent=True).pack(side="left", padx=4, pady=6)
        self._btn(ctrl, "Edit",         self._open_edit_theory_dialog).pack(side="left", padx=2, pady=6)
        self._btn(ctrl, "Archive",      self._archive_theory).pack(side="left", padx=2, pady=6)
        self._btn(ctrl, "🗑 Delete",    self._delete_theory).pack(side="left", padx=2, pady=6)
        self._btn(ctrl, "📊 Full Report", self._run_theory_report, accent=True).pack(side="right", padx=12, pady=6)

        # ── Stats bar ─────────────────────────────────────────────────────
        stats_bar = tk.Frame(self, bg=BG_CARD)
        stats_bar.pack(fill="x")
        self._stat_labels: dict[str, tk.Label] = {}
        stats_defs = [
            ("balance",   "Balance",    "$100,000"),
            ("pnl",       "Total P&L",  "$0"),
            ("ret",       "Return",     "0.00%"),
            ("trades",    "Trades",     "0"),
            ("win_rate",  "Win Rate",   "--"),
            ("rr",        "R:R",        "--"),
            ("avg_win",   "Avg Win",    "--"),
            ("avg_loss",  "Avg Loss",   "--"),
        ]
        for key, label, default in stats_defs:
            cell = tk.Frame(stats_bar, bg=BG_CARD)
            cell.pack(side="left", padx=16, pady=6)
            tk.Label(cell, text=label, bg=BG_CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 8)).pack()
            lbl = tk.Label(cell, text=default, bg=BG_CARD, fg=TEXT_PRIMARY,
                           font=("Consolas", 11, "bold"))
            lbl.pack()
            self._stat_labels[key] = lbl

        tk.Frame(self, bg=BORDER_CARD, height=1).pack(fill="x")

        # ── Main split: left=open trades, right=closed+analysis ───────────
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left  = tk.Frame(body, bg=BG_DARK)
        right = tk.Frame(body, bg=BG_DARK)
        left.grid(row=0, column=0, sticky="nsew", padx=(8,4), pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(4,8), pady=8)

        self._build_open_trades(left)
        self._build_history_panel(right)

    def _build_open_trades(self, parent):
        hdr = tk.Frame(parent, bg=BG_DARK)
        hdr.pack(fill="x", pady=(0,4))
        tk.Label(hdr, text="📂  OPEN PAPER TRADES", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        cols = ("Ticker","Dir","Shares","Entry","Current","P&L","P&L%","Target","Stop","Thesis")
        self._open_tree = ttk.Treeview(parent, columns=cols, show="headings",
                                        height=9, selectmode="browse")
        widths = (60,45,60,68,72,80,62,68,65,160)
        for col, w in zip(cols, widths):
            self._open_tree.heading(col, text=col)
            self._open_tree.column(col, width=w,
                                    anchor="w" if col in ("Ticker","Dir","Thesis") else "e")
        self._open_tree.tag_configure("gain",     foreground=GREEN)
        self._open_tree.tag_configure("loss",     foreground=RED)
        self._open_tree.tag_configure("neutral",  foreground=TEXT_BODY)
        self._open_tree.tag_configure("near_target", foreground=ACCENT)
        self._open_tree.tag_configure("near_stop",   foreground=WARNING)
        self._open_tree.pack(fill="x")
        self._open_tree.bind("<Button-3>", self._open_trade_right_click)

        btn_bar = tk.Frame(parent, bg=BG_DARK)
        btn_bar.pack(fill="x", pady=(4,12))
        self._btn(btn_bar, "+ Open Trade",    self._open_add_trade_dialog, accent=True).pack(side="left", padx=2)
        self._btn(btn_bar, "Close at Market", self._close_at_market).pack(side="left", padx=2)
        self._btn(btn_bar, "Close at Price",  self._close_at_price).pack(side="left", padx=2)
        self._btn(btn_bar, "Edit",            self._open_edit_trade).pack(side="left", padx=2)
        self._btn(btn_bar, "Delete",          self._delete_trade).pack(side="left", padx=2)

        # ── Hypothesis display ─────────────────────────────────────────────
        tk.Label(parent, text="THEORY HYPOTHESIS", bg=BG_DARK, fg=TEXT_MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8,2))
        self._hypothesis_text = tk.Text(parent, bg=BG_CARD, fg=TEXT_BODY,
                                         font=("Segoe UI", 9), relief="flat",
                                         height=4, wrap="word", padx=8, pady=4)
        self._hypothesis_text.pack(fill="x")
        self._hypothesis_text.configure(state="disabled")

    def _build_history_panel(self, parent):
        tk.Label(parent, text="📋  CLOSED TRADES & ANALYSIS", bg=BG_DARK, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,4))

        cols = ("Ticker","Dir","Entry","Exit","P&L","P&L%","Status")
        self._hist_tree = ttk.Treeview(parent, columns=cols, show="headings",
                                        height=10, selectmode="browse")
        widths = (60,45,68,68,80,62,90)
        for col, w in zip(cols, widths):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w,
                                    anchor="w" if col in ("Ticker","Dir","Status") else "e")
        self._hist_tree.tag_configure("win",  foreground=GREEN)
        self._hist_tree.tag_configure("loss", foreground=RED)
        self._hist_tree.tag_configure("flat", foreground=TEXT_BODY)
        self._hist_tree.pack(fill="x")
        self._hist_tree.bind("<<TreeviewSelect>>", self._on_closed_trade_select)

        # Analysis display
        tk.Label(parent, text="TRADE ANALYSIS", bg=BG_DARK, fg=TEXT_MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10,2))

        analysis_frame = tk.Frame(parent, bg=BG_CARD)
        analysis_frame.pack(fill="both", expand=True)
        vsb = tk.Scrollbar(analysis_frame)
        vsb.pack(side="right", fill="y")
        self._analysis_text = tk.Text(analysis_frame, bg=BG_CARD, fg=TEXT_BODY,
                                       font=("Segoe UI", 9), relief="flat",
                                       wrap="word", yscrollcommand=vsb.set,
                                       padx=8, pady=6)
        self._analysis_text.pack(fill="both", expand=True)
        vsb.config(command=self._analysis_text.yview)
        self._analysis_text.configure(state="disabled")

        btn_bar = tk.Frame(parent, bg=BG_DARK)
        btn_bar.pack(fill="x", pady=4)
        self._btn(btn_bar, "🤖 Re-Analyse Selected",
                  self._reanalyse_selected, accent=True).pack(side="left", padx=2)
        self._btn(btn_bar, "Clear Analysis",
                  self._clear_analysis).pack(side="left", padx=2)

    # ── Theory CRUD ───────────────────────────────────────────────────────────

    def _load_theories(self):
        theories = hub_db.list_theories()
        names = [f"{t['name']}  [{t.get('status','')}]" for t in theories]
        self._theory_combo["values"] = names
        self._theory_objects = {n: t for n, t in zip(names, theories)}
        if theories:
            self._theory_combo.current(0)
            self._selected_theory_id = theories[0]["id"]
            self._on_theory_select(None)

    def _on_theory_select(self, _event):
        sel = self._theory_var.get()
        t = self._theory_objects.get(sel)
        if t:
            self._selected_theory_id = t["id"]
            self._update_stats()
            self._refresh_open_trades()
            self._refresh_history()
            self._update_hypothesis_display(t.get("hypothesis",""))

    def _update_hypothesis_display(self, text: str):
        self._hypothesis_text.configure(state="normal")
        self._hypothesis_text.delete("1.0", "end")
        self._hypothesis_text.insert("1.0", text or "No hypothesis defined.")
        self._hypothesis_text.configure(state="disabled")

    def _update_stats(self):
        if not self._selected_theory_id:
            return
        s = hub_db.theory_stats(self._selected_theory_id)
        bal     = s.get("current_balance", 0)
        pnl     = s.get("total_pnl", 0)
        ret     = s.get("total_return_pct", 0)
        trades  = s.get("total_trades", 0)
        win_rt  = s.get("win_rate_pct", 0)
        rr      = s.get("risk_reward", 0)
        avg_w   = s.get("avg_win", 0)
        avg_l   = s.get("avg_loss", 0)

        pnl_color = GREEN if pnl > 0 else (RED if pnl < 0 else TEXT_PRIMARY)
        ret_color = GREEN if ret > 0 else (RED if ret < 0 else TEXT_PRIMARY)
        wr_color  = GREEN if win_rt >= 50 else (RED if win_rt < 40 else WARNING)

        def _upd(key, text, color=TEXT_PRIMARY):
            try:
                self._stat_labels[key].configure(text=text, fg=color)
            except Exception:
                pass

        _upd("balance", f"${bal:,.0f}")
        _upd("pnl",     f"${pnl:+,.2f}", pnl_color)
        _upd("ret",     f"{ret:+.2f}%",  ret_color)
        _upd("trades",  str(trades))
        _upd("win_rate", f"{win_rt:.1f}%", wr_color)
        _upd("rr",      f"{rr:.2f}:1" if rr else "--")
        _upd("avg_win",  f"${avg_w:+,.2f}" if avg_w else "--", GREEN)
        _upd("avg_loss", f"${avg_l:+,.2f}" if avg_l else "--", RED)

    def _refresh_open_trades(self):
        self._open_tree.delete(*self._open_tree.get_children())
        if not self._selected_theory_id:
            return
        trades = hub_db.list_paper_trades(theory_id=self._selected_theory_id, status="open")
        for t in trades:
            pnl     = t.get("pnl", 0) or 0
            pnl_pct = t.get("pnl_pct", 0) or 0
            cur     = t.get("current_price", 0) or 0
            entry   = t.get("entry_price", 0) or 0
            target  = t.get("target_price", 0) or 0
            stop    = t.get("stop_price", 0) or 0
            # Determine tag
            if target and cur >= target * 0.97:
                tag = "near_target"
            elif stop and cur <= stop * 1.03:
                tag = "near_stop"
            elif pnl > 0:
                tag = "gain"
            elif pnl < 0:
                tag = "loss"
            else:
                tag = "neutral"
            thesis_short = (t.get("thesis","") or "")[:60]
            self._open_tree.insert("", "end", iid=t["id"], tags=(tag,), values=(
                t.get("ticker",""),
                t.get("direction","").upper()[:1] + ("↑" if t.get("direction")=="long" else "↓"),
                f"{t.get('shares',0):,.0f}",
                f"${entry:.2f}",
                f"${cur:.2f}" if cur else "--",
                f"${pnl:+,.2f}",
                f"{pnl_pct:+.2f}%",
                f"${target:.2f}" if target else "--",
                f"${stop:.2f}"   if stop   else "--",
                thesis_short,
            ))

    def _refresh_history(self):
        self._hist_tree.delete(*self._hist_tree.get_children())
        if not self._selected_theory_id:
            return
        trades = hub_db.list_paper_trades(theory_id=self._selected_theory_id)
        closed = [t for t in trades if t.get("status","").startswith("closed")]
        for t in sorted(closed, key=lambda x: x.get("closed_at",""), reverse=True):
            pnl     = t.get("pnl", 0) or 0
            pnl_pct = t.get("pnl_pct", 0) or 0
            tag     = "win" if pnl > 0 else ("loss" if pnl < 0 else "flat")
            status  = t.get("status","").replace("closed_","").upper()
            self._hist_tree.insert("", "end", iid=t["id"], tags=(tag,), values=(
                t.get("ticker",""),
                t.get("direction","").upper()[:1],
                f"${t.get('entry_price',0):.2f}",
                f"${t.get('exit_price',0):.2f}",
                f"${pnl:+,.2f}",
                f"{pnl_pct:+.2f}%",
                status,
            ))

    def _on_closed_trade_select(self, _event):
        sel = self._hist_tree.selection()
        if not sel:
            return
        trade = hub_db.get_paper_trade(sel[0])
        if not trade:
            return
        analysis = trade.get("analysis","") or ""
        self._set_analysis_text(
            analysis or "(No analysis yet — click 'Re-Analyse Selected' to generate.)"
        )

    def _set_analysis_text(self, text: str):
        self._analysis_text.configure(state="normal")
        self._analysis_text.delete("1.0", "end")
        self._analysis_text.insert("1.0", text)
        self._analysis_text.configure(state="disabled")

    def _clear_analysis(self):
        self._set_analysis_text("")

    # ── Trade CRUD ────────────────────────────────────────────────────────────

    def _open_add_trade_dialog(self, prefill: dict | None = None):
        if not self._selected_theory_id:
            self._show_msg("Select or create a theory first.")
            return
        theory = hub_db.get_theory(self._selected_theory_id)
        avail = theory.get("current_balance", 0) if theory else 0

        dlg = tk.Toplevel(self)
        dlg.title("Open Paper Trade")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("460x640")
        dlg.transient(self)
        dlg.grab_set()

        fields = {
            "ticker":       tk.StringVar(value=prefill.get("ticker","")        if prefill else ""),
            "name":         tk.StringVar(value=prefill.get("name","")          if prefill else ""),
            "shares":       tk.StringVar(value=str(prefill.get("shares",0))    if prefill else ""),
            "entry_price":  tk.StringVar(value=str(prefill.get("entry_price",0)) if prefill else ""),
            "target_price": tk.StringVar(value=str(prefill.get("target_price",0)) if prefill else ""),
            "stop_price":   tk.StringVar(value=str(prefill.get("stop_price",0))   if prefill else ""),
            "direction":    tk.StringVar(value=prefill.get("direction","long") if prefill else "long"),
            "position_type":tk.StringVar(value=prefill.get("position_type","equity") if prefill else "equity"),
            "source":       tk.StringVar(value="manual"),
            "agent_id":     tk.StringVar(value=prefill.get("agent_id","markets-equity-analyst") if prefill else "markets-equity-analyst"),
        }

        row = 0
        # Available balance display
        tk.Label(dlg, text=f"Available Balance: ${avail:,.2f}", bg=BG_PANEL,
                 fg=ACCENT, font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(12,4))
        row += 1

        field_defs = [
            ("Ticker *",      "ticker"),
            ("Name",          "name"),
            ("Shares",        "shares"),
            ("Entry Price $", "entry_price"),
            ("Target Price $","target_price"),
            ("Stop Loss $",   "stop_price"),
        ]
        for lbl_text, key in field_defs:
            tk.Label(dlg, text=lbl_text, bg=BG_PANEL, fg=TEXT_BODY).grid(
                row=row, column=0, sticky="w", padx=16, pady=(6,1))
            tk.Entry(dlg, textvariable=fields[key], bg=BG_CANVAS, fg=TEXT_PRIMARY,
                     relief="flat", insertbackground=TEXT_PRIMARY,
                     font=("Segoe UI", 10)).grid(row=row, column=1, sticky="ew", padx=(4,16))
            row += 1

        # Capital preview
        self._cap_preview_lbl = tk.Label(dlg, text="Capital used: $0", bg=BG_PANEL,
                                          fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._cap_preview_lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(2,6))
        row += 1

        def _update_cap(*_):
            try:
                cap = float(fields["shares"].get() or 0) * float(fields["entry_price"].get() or 0)
                color = WARNING if cap > avail else TEXT_MUTED
                self._cap_preview_lbl.configure(text=f"Capital used: ${cap:,.2f}", fg=color)
            except Exception:
                pass
        fields["shares"].trace_add("write", _update_cap)
        fields["entry_price"].trace_add("write", _update_cap)

        for lbl_text, key, values in [
            ("Direction",     "direction",     ["long","short"]),
            ("Type",          "position_type", ["equity","options","etf","crypto"]),
            ("Source",        "source",        ["manual","agent_suggestion","backtest"]),
        ]:
            tk.Label(dlg, text=lbl_text, bg=BG_PANEL, fg=TEXT_BODY).grid(
                row=row, column=0, sticky="w", padx=16, pady=(6,1))
            ttk.Combobox(dlg, textvariable=fields[key], values=values,
                         state="readonly").grid(row=row, column=1, sticky="ew", padx=(4,16))
            row += 1

        tk.Label(dlg, text="Thesis (why this trade)", bg=BG_PANEL, fg=TEXT_BODY).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=16, pady=(8,2))
        row += 1
        thesis_box = tk.Text(dlg, bg=BG_CANVAS, fg=TEXT_PRIMARY, font=("Segoe UI",9),
                              relief="flat", height=4, wrap="word",
                              insertbackground=TEXT_PRIMARY, padx=6, pady=4)
        thesis_box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=16)
        if prefill and prefill.get("thesis"):
            thesis_box.insert("1.0", prefill["thesis"])
        row += 1

        def _save():
            ticker = fields["ticker"].get().strip().upper()
            if not ticker:
                return
            shares     = float(fields["shares"].get() or 0)
            entry      = float(fields["entry_price"].get() or 0)
            capital    = shares * entry
            if capital > avail:
                self._show_msg(f"Insufficient paper balance.\nNeed ${capital:,.2f}, have ${avail:,.2f}")
                return
            hub_db.open_paper_trade(
                theory_id=self._selected_theory_id,
                ticker=ticker,
                name=fields["name"].get().strip(),
                shares=shares,
                entry_price=entry,
                target_price=float(fields["target_price"].get() or 0),
                stop_price=float(fields["stop_price"].get() or 0),
                direction=fields["direction"].get(),
                position_type=fields["position_type"].get(),
                thesis=thesis_box.get("1.0","end").strip(),
                agent_id=fields["agent_id"].get(),
                source=fields["source"].get(),
            )
            dlg.destroy()
            self._refresh_open_trades()
            self._update_stats()

        dlg.columnconfigure(1, weight=1)
        btn_row = tk.Frame(dlg, bg=BG_PANEL)
        btn_row.grid(row=row, column=0, columnspan=2, sticky="e", padx=16, pady=12)
        self._btn(btn_row, "Cancel", dlg.destroy).pack(side="left", padx=4)
        self._btn(btn_row, "Open Trade", _save, accent=True).pack(side="left", padx=4)

    def _open_edit_trade(self):
        sel = self._open_tree.selection()
        if not sel:
            return
        trade = hub_db.get_paper_trade(sel[0])
        if trade:
            self._open_add_trade_dialog(prefill=trade)

    def _delete_trade(self):
        sel = self._open_tree.selection()
        if not sel:
            return
        with hub_db.get_conn() as conn:
            trade = hub_db.get_paper_trade(sel[0])
            if trade and trade.get("status") == "open":
                # Return capital to theory
                conn.execute(
                    "UPDATE market_trade_theories SET current_balance=current_balance+?,updated_at=? WHERE id=?",
                    (trade.get("capital_used",0), _now(), trade.get("theory_id",""))
                )
            conn.execute("DELETE FROM market_paper_trades WHERE id=?", (sel[0],))
        self._refresh_open_trades()
        self._update_stats()

    def _close_at_market(self):
        """Close selected trade at its current price."""
        sel = self._open_tree.selection()
        if not sel:
            return
        trade = hub_db.get_paper_trade(sel[0])
        if not trade:
            return
        exit_price = trade.get("current_price") or trade.get("entry_price", 0)
        self._do_close_trade(trade, exit_price)

    def _close_at_price(self):
        """Prompt for an exit price then close."""
        sel = self._open_tree.selection()
        if not sel:
            return
        trade = hub_db.get_paper_trade(sel[0])
        if not trade:
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Close {trade.get('ticker','')}")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("300x180")
        dlg.transient(self)
        dlg.grab_set()

        cur = trade.get("current_price") or trade.get("entry_price",0)
        tk.Label(dlg, text=f"Current price: ${cur:.2f}", bg=BG_PANEL,
                 fg=TEXT_BODY).pack(padx=20, pady=(16,4), anchor="w")
        price_var = tk.StringVar(value=str(round(cur, 2)))
        tk.Label(dlg, text="Exit price:", bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=20)
        tk.Entry(dlg, textvariable=price_var, bg=BG_CANVAS, fg=TEXT_PRIMARY,
                 relief="flat", insertbackground=TEXT_PRIMARY,
                 font=("Segoe UI", 11)).pack(fill="x", padx=20, pady=4)

        def _close():
            try:
                exit_p = float(price_var.get())
            except ValueError:
                return
            dlg.destroy()
            self._do_close_trade(trade, exit_p)

        btn_row = tk.Frame(dlg, bg=BG_PANEL)
        btn_row.pack(anchor="e", padx=20, pady=8)
        self._btn(btn_row, "Cancel", dlg.destroy).pack(side="left", padx=4)
        self._btn(btn_row, "Close Trade", _close, accent=True).pack(side="left", padx=4)

    def _do_close_trade(self, trade: dict, exit_price: float):
        """Execute close and trigger analysis."""
        hub_db.close_paper_trade(trade["id"], exit_price)
        self._refresh_open_trades()
        self._refresh_history()
        self._update_stats()
        # Fire analysis in background
        threading.Thread(
            target=self._run_trade_analysis,
            args=(trade["id"],),
            daemon=True,
        ).start()

    def _open_trade_right_click(self, event):
        item = self._open_tree.identify_row(event.y)
        if not item:
            return
        self._open_tree.selection_set(item)
        menu = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=TEXT_PRIMARY,
                       activebackground=ACCENT, activeforeground=BG_RAIL)
        menu.add_command(label="Close at Market",  command=self._close_at_market)
        menu.add_command(label="Close at Price...", command=self._close_at_price)
        menu.add_separator()
        menu.add_command(label="Edit",   command=self._open_edit_trade)
        menu.add_command(label="Delete", command=self._delete_trade)
        menu.post(event.x_root, event.y_root)

    # ── Analysis engine ───────────────────────────────────────────────────────

    def _run_trade_analysis(self, trade_id: str):
        """Background: run agent analysis on a closed trade, save to DB, update UI."""
        trade = hub_db.get_paper_trade(trade_id)
        if not trade:
            return
        theory = hub_db.get_theory(trade.get("theory_id",""))
        stats = hub_db.theory_stats(trade.get("theory_id","")) if theory else {}

        pnl     = trade.get("pnl", 0)
        pnl_pct = trade.get("pnl_pct", 0)
        outcome = "WIN" if pnl > 0 else ("LOSS" if pnl < 0 else "FLAT")

        task = (
            f"Analyse this closed paper trade:\n\n"
            f"**Trade:** {trade.get('ticker','')} — {trade.get('direction','').upper()} "
            f"{trade.get('shares',0):,.0f} shares\n"
            f"**Entry:** ${trade.get('entry_price',0):.2f}  "
            f"**Exit:** ${trade.get('exit_price',0):.2f}\n"
            f"**P&L:** ${pnl:+,.2f} ({pnl_pct:+.2f}%) — **{outcome}**\n"
            f"**Target was:** ${trade.get('target_price',0):.2f}  "
            f"**Stop was:** ${trade.get('stop_price',0):.2f}\n"
            f"**Original thesis:** {trade.get('thesis','(none)')}\n\n"
            f"Theory context: {theory.get('name','') if theory else 'N/A'}\n"
            f"Theory stats: {stats.get('win_rate_pct',0):.1f}% win rate over "
            f"{stats.get('total_trades',0)} trades\n\n"
            "Provide:\n"
            "1. Was the thesis proven or disproven?\n"
            "2. What worked / what didn't?\n"
            "3. Was the entry timing correct? Stop/target placement?\n"
            "4. What would improve this setup?\n"
            "5. Verdict on the theory's effectiveness for this trade type.\n\n"
            "Be specific and data-driven. Format as structured markdown."
        )

        agent_id = trade.get("agent_id") or (
            "markets-options-strategist"
            if trade.get("position_type") == "options"
            else "markets-equity-analyst"
        )

        try:
            from agent_runner import run_agent
            result = run_agent(
                agent_id=agent_id,
                task=task,
                project="markets",
                extra_context=f"Theory: {theory.get('hypothesis','') if theory else ''}",
            )
            analysis = result.get("response", "Analysis unavailable.")
        except Exception as e:
            analysis = f"Analysis failed: {e}"

        # Save analysis to trade record
        with hub_db.get_conn() as conn:
            conn.execute(
                "UPDATE market_paper_trades SET analysis=?,updated_at=? WHERE id=?",
                (analysis, _now(), trade_id),
            )

        # Update UI on main thread
        def _update_ui():
            self._refresh_history()
            # If this trade is currently selected, show analysis immediately
            sel = self._hist_tree.selection()
            if sel and sel[0] == trade_id:
                self._set_analysis_text(analysis)

        try:
            self.after(0, _update_ui)
        except Exception:
            pass

    def _reanalyse_selected(self):
        sel = self._hist_tree.selection()
        if not sel:
            return
        self._set_analysis_text("⏳ Running analysis — please wait...")
        threading.Thread(target=self._run_trade_analysis, args=(sel[0],), daemon=True).start()

    # ── Theory dialogs ────────────────────────────────────────────────────────

    def _open_new_theory_dialog(self, existing: dict | None = None):
        dlg = tk.Toplevel(self)
        dlg.title("New Theory" if not existing else f"Edit: {existing.get('name','')}")
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("500x480")
        dlg.transient(self)
        dlg.grab_set()

        fields = {
            "name":             tk.StringVar(value=existing.get("name","")              if existing else ""),
            "starting_balance": tk.StringVar(value=str(existing.get("starting_balance",100000)) if existing else "100000"),
            "agent_id":         tk.StringVar(value=existing.get("agent_id","markets-project-lead") if existing else "markets-project-lead"),
        }

        row = 0
        for lbl_text, key in [("Theory Name *", "name"),("Starting Balance $","starting_balance"),("Lead Agent","agent_id")]:
            tk.Label(dlg, text=lbl_text, bg=BG_PANEL, fg=TEXT_BODY).grid(
                row=row, column=0, sticky="w", padx=16, pady=(10 if row==0 else 6, 2))
            tk.Entry(dlg, textvariable=fields[key], bg=BG_CANVAS, fg=TEXT_PRIMARY,
                     relief="flat", font=("Segoe UI",10),
                     insertbackground=TEXT_PRIMARY).grid(row=row+1, column=0, sticky="ew", padx=16)
            row += 2

        tk.Label(dlg, text="Description", bg=BG_PANEL, fg=TEXT_BODY).grid(
            row=row, column=0, sticky="w", padx=16, pady=(6,2))
        desc_box = tk.Text(dlg, bg=BG_CANVAS, fg=TEXT_PRIMARY, font=("Segoe UI",9),
                            relief="flat", height=3, wrap="word", insertbackground=TEXT_PRIMARY,
                            padx=6, pady=4)
        desc_box.grid(row=row+1, column=0, sticky="ew", padx=16)
        if existing:
            desc_box.insert("1.0", existing.get("description",""))
        row += 2

        tk.Label(dlg, text="Hypothesis — what are you testing?", bg=BG_PANEL, fg=TEXT_BODY).grid(
            row=row, column=0, sticky="w", padx=16, pady=(8,2))
        hyp_box = tk.Text(dlg, bg=BG_CANVAS, fg=TEXT_PRIMARY, font=("Segoe UI",9),
                           relief="flat", height=5, wrap="word", insertbackground=TEXT_PRIMARY,
                           padx=6, pady=4)
        hyp_box.grid(row=row+1, column=0, sticky="ew", padx=16)
        if existing:
            hyp_box.insert("1.0", existing.get("hypothesis",""))
        row += 2

        def _save():
            name = fields["name"].get().strip()
            if not name:
                return
            if existing:
                hub_db.update_theory(
                    existing["id"],
                    name=name,
                    description=desc_box.get("1.0","end").strip(),
                    hypothesis=hyp_box.get("1.0","end").strip(),
                    agent_id=fields["agent_id"].get().strip(),
                )
            else:
                hub_db.create_theory(
                    name=name,
                    description=desc_box.get("1.0","end").strip(),
                    hypothesis=hyp_box.get("1.0","end").strip(),
                    starting_balance=float(fields["starting_balance"].get() or 100000),
                    agent_id=fields["agent_id"].get().strip(),
                )
            dlg.destroy()
            self._load_theories()

        dlg.columnconfigure(0, weight=1)
        btn_row = tk.Frame(dlg, bg=BG_PANEL)
        btn_row.grid(row=row, column=0, sticky="e", padx=16, pady=12)
        self._btn(btn_row, "Cancel", dlg.destroy).pack(side="left", padx=4)
        self._btn(btn_row, "Save Theory", _save, accent=True).pack(side="left", padx=4)

    def _open_edit_theory_dialog(self):
        if not self._selected_theory_id:
            return
        theory = hub_db.get_theory(self._selected_theory_id)
        if theory:
            self._open_new_theory_dialog(existing=theory)

    def _archive_theory(self):
        if self._selected_theory_id:
            hub_db.update_theory(self._selected_theory_id, status="archived")
            self._load_theories()

    def _delete_theory(self):
        if self._selected_theory_id:
            hub_db.delete_theory(self._selected_theory_id)
            self._selected_theory_id = None
            self._load_theories()

    # ── Report generation ─────────────────────────────────────────────────────

    def _run_theory_report(self):
        if not self._selected_theory_id:
            return
        theory = hub_db.get_theory(self._selected_theory_id)
        stats  = hub_db.theory_stats(self._selected_theory_id)
        trades = hub_db.list_paper_trades(theory_id=self._selected_theory_id)
        closed = [t for t in trades if t.get("status","").startswith("closed")]

        trade_summary = "\n".join(
            f"- {t.get('ticker','')} {t.get('direction','').upper()}: "
            f"entry ${t.get('entry_price',0):.2f} → exit ${t.get('exit_price',0):.2f} "
            f"| P&L ${t.get('pnl',0):+,.2f} ({t.get('pnl_pct',0):+.2f}%)"
            for t in closed[:20]
        ) or "No closed trades."

        task = (
            f"Generate a full theory performance report for: **{theory.get('name','')}**\n\n"
            f"**Hypothesis:** {theory.get('hypothesis','')}\n\n"
            f"**Performance Stats:**\n"
            f"- Starting Balance: ${stats.get('starting_balance',0):,.2f}\n"
            f"- Current Balance: ${stats.get('current_balance',0):,.2f}\n"
            f"- Total Return: {stats.get('total_return_pct',0):+.2f}%\n"
            f"- Total P&L: ${stats.get('total_pnl',0):+,.2f}\n"
            f"- Total Trades: {stats.get('total_trades',0)}\n"
            f"- Win Rate: {stats.get('win_rate_pct',0):.1f}%\n"
            f"- Risk:Reward: {stats.get('risk_reward',0):.2f}:1\n"
            f"- Avg Win: ${stats.get('avg_win',0):+,.2f}  |  Avg Loss: ${stats.get('avg_loss',0):+,.2f}\n"
            f"- Largest Win: ${stats.get('largest_win',0):+,.2f}  |  Largest Loss: ${stats.get('largest_loss',0):+,.2f}\n\n"
            f"**Trade History:**\n{trade_summary}\n\n"
            "Provide:\n"
            "1. Executive verdict — is this theory profitable? Should we continue it?\n"
            "2. Pattern analysis — what types of trades performed best/worst?\n"
            "3. Risk management assessment\n"
            "4. Recommended refinements to the hypothesis\n"
            "5. Recommended position sizing adjustments\n"
            "6. Overall grade (A/B/C/D/F) with justification\n\n"
            "Format as a professional hedge fund performance memo."
        )

        def _do():
            try:
                from agent_runner import run_agent
                result = run_agent(
                    agent_id=theory.get("agent_id","markets-project-lead"),
                    task=task,
                    project="markets",
                )
                # Save as a report
                hub_db.create_report(
                    title=f"Theory Report: {theory.get('name','')} — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                    content=result.get("response",""),
                    summary=result.get("summary",""),
                    report_type="research",
                    project_slug="markets",
                    generated_by=theory.get("agent_id","markets-project-lead"),
                    job_id=f"theory_{self._selected_theory_id}",
                )
                if self._ui_queue:
                    self._ui_queue.put(("notification","Theory report generated","#00C864"))
            except Exception as e:
                logger.error("Theory report failed: %s", e)
        threading.Thread(target=_do, daemon=True).start()
        self._show_msg("Theory report generation started. Check Reports tab when complete.")

    # ── Live quote injection ──────────────────────────────────────────────────

    def inject_quote(self, ticker: str, price: float):
        """Called from the live feed with updated prices."""
        try:
            hub_db.update_paper_trade_price(ticker, price)
            if self._selected_theory_id:
                self.after(0, self._refresh_open_trades)
                self.after(0, self._update_stats)
        except Exception:
            pass

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _btn(self, parent, text, command, accent=False):
        bg = ACCENT if accent else BG_CARD
        fg = BG_RAIL if accent else TEXT_BODY
        return tk.Button(parent, text=text, command=command,
                         bg=bg, fg=fg, relief="flat", padx=8, pady=3,
                         cursor="hand2", font=("Segoe UI", 9),
                         activebackground=ACCENT_LIGHT if accent else BG_CANVAS,
                         activeforeground=BG_RAIL)

    def _show_msg(self, text: str):
        dlg = tk.Toplevel(self)
        dlg.configure(bg=BG_PANEL)
        dlg.geometry("360x140")
        dlg.transient(self)
        dlg.grab_set()
        tk.Label(dlg, text=text, bg=BG_PANEL, fg=TEXT_BODY,
                 wraplength=320, justify="center").pack(expand=True)
        self._btn(dlg, "OK", dlg.destroy, accent=True).pack(pady=(0,12))

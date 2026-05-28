"""
Sprint 5 — all 5 new feature method blocks.
This file is exec'd by the injector to get the METHOD_BLOCK string.
"""

METHOD_BLOCK = '''
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
            f.write(f"AgentHarness Notification Log\\n")
            f.write(f"Exported: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write("=" * 60 + "\\n\\n")
            for n in self._notif_history:
                f.write(f"[{n.get('timestamp','')}] [{n.get('category','').upper()}] {n.get('text','')}\\n")
        self._push_notif(f"Log exported: {fname}", SUCCESS)
        qlog(f"[Notifications] Log exported to {fpath}", SUCCESS)
'''

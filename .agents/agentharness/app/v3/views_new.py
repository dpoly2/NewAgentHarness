"""
AgentHarness v3 — New Views Extension
Paste this content at the END of main_m365.py (before the _poll_log method).
Adds: Tasks, Todos, Agents Directory, Clients views +
      Real LLM streaming for AgentMajesty chat +
      Push notification helpers + AI provider switcher + DDNS helpers
"""

# ═══════════════════════════════════════════════════════════════════════
# PATCH NOTE: inject these methods into AgentHarnessM365 class
# ═══════════════════════════════════════════════════════════════════════

TASKS_VIEW = '''
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
        self._todos_data = []

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
        self._refresh_todos()

    def _todo_delete(self, todo):
        self._todos_data = [t for t in self._todos_data if t["id"] != todo["id"]]
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
        txt.insert("1.0", proj_text or f"No PROJECT.md found for '{slug}'.\n\nCreate one at .agents/projects/{slug}/PROJECT.md")
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
                        data=b"AgentHarness test notification — Chief of Staff online.",
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
'''

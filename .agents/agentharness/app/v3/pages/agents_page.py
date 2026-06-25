"""Agents page mixin — orchestration, conversations, templates, feedback."""
import tkinter as tk
from tkinter import ttk
from pages.constants import *


class AgentsPageMixin:
    def show_agents(self):
        self._set_active_nav("Agents")
        self._clear_content()
        self._section_header(self.content, "🤖 Agents",
                             "Multi-agent orchestration, prompt templates, and feedback analysis.")

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        orch_tab = tk.Frame(notebook, bg=BG_CANVAS)
        conv_tab = tk.Frame(notebook, bg=BG_CANVAS)
        tmpl_tab = tk.Frame(notebook, bg=BG_CANVAS)
        feed_tab = tk.Frame(notebook, bg=BG_CANVAS)
        notebook.add(orch_tab, text="Orchestrate")
        notebook.add(conv_tab, text="💬 Conversations")
        notebook.add(tmpl_tab, text="Templates")
        notebook.add(feed_tab, text="Feedback")

        self._build_agents_orchestrate_tab(orch_tab)
        self._build_agents_conversations_tab(conv_tab)
        self._build_agents_templates_tab(tmpl_tab)
        self._build_agents_feedback_tab(feed_tab)

    def _build_agents_orchestrate_tab(self, parent):
        card = self._card(parent, "Multi-Agent Collaboration")
        card.pack(fill="x", padx=10, pady=10)

        tk.Label(card, text="Query — agents will collaborate to answer:",
                 bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=14, pady=(8, 4))
        self._orch_query_var = tk.StringVar()
        self._entry(card, self._orch_query_var).pack(fill="x", padx=14, pady=(0, 8))

        cap_row = tk.Frame(card, bg=BG_PANEL)
        cap_row.pack(fill="x", padx=14, pady=(0, 8))
        self._button(cap_row, "▶ Collaborate", self._run_agent_collaboration, accent=True).pack(side="left", padx=4)
        self._button(cap_row, "View Capabilities", self._show_agent_capabilities).pack(side="left", padx=4)

        res_card = self._card(parent, "Collaboration Result")
        res_card.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._orch_result_text = self._text_widget(res_card, height=20)
        self._orch_result_text.pack(fill="both", expand=True, padx=14, pady=14)
        self._orch_result_text.configure(state="disabled")

    def _run_agent_collaboration(self):
        query = getattr(self, "_orch_query_var", tk.StringVar()).get().strip()
        if not query:
            self._toast("Enter a query first.", WARNING)
            return
        import threading as _t

        self._toast("Collaborating…", ACCENT)

        def _run():
            try:
                result = self.hub.post_json("/api/agents/collaborate", {"query": query, "user_id": self.username})
                if result:
                    resp = result.get("response") or result.get("result") or str(result)
                    agents_used = result.get("agents_used", [])
                    header = f"Agents used: {', '.join(agents_used)}\n{'─' * 60}\n\n" if agents_used else ""
                    self._ui_queue.put(("set_text", self._orch_result_text, header + resp))
                else:
                    self._ui_queue.put(("toast", "No response from collaboration.", WARNING))
            except Exception as e:
                self._ui_queue.put(("toast", f"Collaboration error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _show_agent_capabilities(self):
        import threading as _t

        def _run():
            try:
                caps = self.hub._get("/api/agents/capabilities") or []
                lines = []
                for c in (caps if isinstance(caps, list) else []):
                    lines.append(f"• {c.get('agent_id', '')}: {c.get('description', '')}")
                    if c.get("capabilities"):
                        lines.append(f"  Skills: {', '.join(c['capabilities'][:5])}")
                text = "\n".join(lines) or "No capabilities data."
                self._ui_queue.put(("set_text", self._orch_result_text, text))
            except Exception as e:
                self._ui_queue.put(("toast", f"Error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _build_agents_conversations_tab(self, parent):
        top_row = tk.Frame(parent, bg=BG_CANVAS)
        top_row.pack(fill="x", padx=10, pady=(10, 4))
        self._button(top_row, "🔄 Refresh", self._refresh_agent_conversations).pack(side="left", padx=4)

        paned = tk.PanedWindow(parent, orient="horizontal", sashwidth=6, bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left: conversation list
        left = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(left, minsize=260)
        tk.Label(left, text="Conversations", bg=BG_CANVAS, fg=TEXT_BODY,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=6, pady=(4, 2))
        cols = ("goal", "agents", "status", "msgs", "created")
        self._conv_tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for col, txt, w in [("goal", "Goal", 180), ("agents", "Agents", 100),
                             ("status", "Status", 70), ("msgs", "#", 30), ("created", "Created", 100)]:
            self._conv_tree.heading(col, text=txt)
            self._conv_tree.column(col, width=w, anchor="w")
        sb_l = ttk.Scrollbar(left, orient="vertical", command=self._conv_tree.yview)
        self._conv_tree.configure(yscrollcommand=sb_l.set)
        self._conv_tree.pack(side="left", fill="both", expand=True)
        sb_l.pack(side="right", fill="y")
        self._conv_tree.bind("<<TreeviewSelect>>", self._on_conv_select)
        self._conv_data = {}

        # Right: message viewer
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(right, minsize=320)
        tk.Label(right, text="Messages", bg=BG_CANVAS, fg=TEXT_BODY,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self._conv_msg_text = self._text_widget(right, height=30)
        self._conv_msg_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self._conv_msg_text.configure(state="disabled")

        self._refresh_agent_conversations()

    def _refresh_agent_conversations(self):
        if not hasattr(self, "_conv_tree"):
            return
        import threading as _t

        def _fetch():
            try:
                resp = self.hub._get("/api/agents/conversations?limit=100") or {}
                convs = resp.get("conversations", resp) if isinstance(resp, dict) else resp
                if not isinstance(convs, list):
                    convs = []
                self._ui_queue.put(("call", lambda: self._populate_conv_tree(convs)))
            except Exception as e:
                self._ui_queue.put(("toast", f"Conversations error: {e}", ERROR))

        _t.Thread(target=_fetch, daemon=True).start()

    def _populate_conv_tree(self, convs):
        if not hasattr(self, "_conv_tree"):
            return
        self._conv_tree.delete(*self._conv_tree.get_children())
        self._conv_data = {}
        for c in convs:
            cid = c.get("conversation_id", "")
            agents = c.get("participant_agents", [])
            if isinstance(agents, list):
                agents_str = ", ".join(agents[:3])
            else:
                agents_str = str(agents)[:30]
            goal = str(c.get("goal", ""))[:50]
            status = c.get("status", "")
            msgs = c.get("message_count", 0)
            ts = str(c.get("created_at", ""))[:16]
            self._conv_tree.insert("", "end", iid=cid,
                                   values=(goal, agents_str, status, msgs, ts))
            self._conv_data[cid] = c

    def _on_conv_select(self, _event):
        if not hasattr(self, "_conv_tree") or not hasattr(self, "_conv_msg_text"):
            return
        sel = self._conv_tree.selection()
        if not sel:
            return
        cid = sel[0]
        import threading as _t

        def _fetch():
            try:
                resp = self.hub._get(f"/api/agents/conversations/{cid}") or {}
                conv = resp.get("conversation", {})
                messages = conv.get("messages", [])
                lines = [f"Goal: {conv.get('goal', '')}", f"Agents: {', '.join(conv.get('participant_agents', []))}", f"Status: {conv.get('status', '')} | Messages: {conv.get('message_count', 0)}", "─" * 60, ""]
                for m in messages:
                    payload = m.get("payload", {})
                    content = payload.get("response") or payload.get("query") or str(payload)[:200]
                    lines.append(f"[{m.get('sender_agent','?')} → {m.get('recipient_agent','?')}] ({m.get('status','?')})")
                    lines.append(f"  {content}")
                    lines.append("")
                text = "\n".join(lines) if len(lines) > 5 else "(no messages yet)"
                self._ui_queue.put(("set_text", self._conv_msg_text, text))
            except Exception as e:
                self._ui_queue.put(("toast", f"Load error: {e}", ERROR))

        _t.Thread(target=_fetch, daemon=True).start()

    def _build_agents_templates_tab(self, parent):
        top_row = tk.Frame(parent, bg=BG_CANVAS)
        top_row.pack(fill="x", padx=10, pady=(10, 4))
        self._button(top_row, "+ New Template", self._new_prompt_template, accent=True).pack(side="left", padx=4)
        self._button(top_row, "🔄 Refresh", self._refresh_prompt_templates).pack(side="left", padx=4)

        card = self._card(parent, "Prompt Templates")
        card.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = ("title", "category", "agent_id", "uses")
        self.tmpl_tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        for col, txt, w in [("title", "Title", 200), ("category", "Category", 100),
                            ("agent_id", "Agent", 120), ("uses", "Uses", 50)]:
            self.tmpl_tree.heading(col, text=txt)
            self.tmpl_tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(card, orient="vertical", command=self.tmpl_tree.yview)
        self.tmpl_tree.configure(yscrollcommand=sb.set)
        self.tmpl_tree.pack(side="left", fill="both", expand=True, padx=14, pady=(0, 10))
        sb.pack(side="right", fill="y", pady=(0, 10))
        btn_row = tk.Frame(card, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=14, pady=(0, 10))
        self._button(btn_row, "🗑 Delete Selected", self._delete_prompt_template).pack(side="left", padx=4)
        self._button(btn_row, "📋 Copy Text", self._copy_template_text).pack(side="left", padx=4)
        self._refresh_prompt_templates()

    def _refresh_prompt_templates(self):
        if not hasattr(self, "tmpl_tree"):
            return
        self.tmpl_tree.delete(*self.tmpl_tree.get_children())
        try:
            data = self.hub._get("/api/prompt-templates") or []
            templates = data if isinstance(data, list) else data.get("templates", [])
            for t in templates:
                self.tmpl_tree.insert("", "end", iid=str(t.get("id", "")),
                                      values=(t.get("title", t.get("name", "")), t.get("category", ""),
                                              t.get("agent_id", ""), t.get("usage_count", t.get("use_count", 0))))
        except Exception as e:
            self._toast(f"Templates load error: {e}", ERROR)

    def _new_prompt_template(self):
        win = tk.Toplevel(self.root)
        win.title("New Prompt Template")
        win.configure(bg=BG_PANEL)
        win.geometry("520x420")
        fields = {}
        for label, key, multiline in [("Title", "title", False), ("Category", "category", False),
                                      ("Agent ID", "agent_id", False), ("Prompt Text", "prompt_text", True)]:
            tk.Label(win, text=label, bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=20, pady=(10, 2))
            if multiline:
                t = tk.Text(win, bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                            font=("Segoe UI", 9), relief="flat", height=8)
                t.pack(fill="both", padx=20, expand=True)
                fields[key] = t
            else:
                var = tk.StringVar()
                self._entry(win, var).pack(fill="x", padx=20)
                fields[key] = var

        def _save():
            payload = {
                "title": fields["title"].get(),
                "category": fields["category"].get() or "general",
                "agent_id": fields["agent_id"].get() or "inez",
                "prompt_text": fields["prompt_text"].get("1.0", "end").strip(),
            }
            try:
                self.hub.post_json("/api/prompt-templates", payload)
                self._refresh_prompt_templates()
                self._toast("Template saved.", SUCCESS)
                win.destroy()
            except Exception as e:
                self._toast(f"Error: {e}", ERROR)

        self._button(win, "Save Template", _save, accent=True).pack(pady=12)

    def _delete_prompt_template(self):
        if not hasattr(self, "tmpl_tree"):
            return
        sel = self.tmpl_tree.selection()
        if not sel:
            self._toast("Select a template first.", WARNING)
            return
        try:
            self.hub.delete(f"/api/prompt-templates/{sel[0]}")
            self.tmpl_tree.delete(sel[0])
            self._toast("Template deleted.", SUCCESS)
        except Exception as e:
            self._toast(f"Delete error: {e}", ERROR)

    def _copy_template_text(self):
        if not hasattr(self, "tmpl_tree"):
            return
        sel = self.tmpl_tree.selection()
        if not sel:
            self._toast("Select a template first.", WARNING)
            return
        template_id = sel[0]
        try:
            data = self.hub.post_json(f"/api/prompt-templates/{template_id}/use", {}) or {}
            text = data.get("prompt_text", "")
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self._toast("Template text copied to clipboard!", SUCCESS)
            else:
                self._toast("No prompt text found.", WARNING)
        except Exception as e:
            self._toast(f"Error: {e}", ERROR)

    def _build_agents_feedback_tab(self, parent):
        top_row = tk.Frame(parent, bg=BG_CANVAS)
        top_row.pack(fill="x", padx=10, pady=(10, 4))
        self._button(top_row, "🔄 Load Feedback Stats", self._refresh_feedback, accent=True).pack(side="left", padx=4)

        stats_card = self._card(parent, "Feedback Summary")
        stats_card.pack(fill="x", padx=10, pady=(0, 8))
        self._feedback_stats_text = self._text_widget(stats_card, height=6)
        self._feedback_stats_text.pack(fill="both", expand=True, padx=14, pady=14)
        self._feedback_stats_text.configure(state="disabled")

        pref_card = self._card(parent, "Learned Style Preferences")
        pref_card.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = ("dimension", "preference", "confidence")
        self.pref_tree = ttk.Treeview(pref_card, columns=cols, show="headings")
        for col, txt, w in [("dimension", "Dimension", 160), ("preference", "Preference", 280), ("confidence", "Confidence", 90)]:
            self.pref_tree.heading(col, text=txt)
            self.pref_tree.column(col, width=w, anchor="w")
        self.pref_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._refresh_feedback()

    def _refresh_feedback(self):
        import threading as _t

        def _run():
            try:
                stats = self.hub._get("/api/feedback/stats") or {}
                prefs_result = self.hub._get("/api/feedback/preferences") or {}
                lines = []
                if stats:
                    s = stats.get("stats", stats)
                    lines.append(f"Total feedback items: {s.get('total_feedback', s.get('total', 0))}")
                    lines.append(f"Positive: {s.get('positive_count', s.get('positive', 0))}  |  Negative: {s.get('negative_count', s.get('negative', 0))}")
                    lines.append(f"Corrections: {s.get('correction_count', s.get('corrections', 0))}")
                    recent = stats.get("recent_feedback", [])
                    if recent:
                        lines.append("─" * 40)
                        lines.append("Recent feedback:")
                        for item in recent[:5]:
                            emoji = "👍" if item.get("rating") == 1 else "👎"
                            lines.append(f"  {emoji} [{item.get('category', '')}] {str(item.get('feedback_text',''))[:60]}")
                else:
                    lines.append("(no feedback data yet)")
                self._ui_queue.put(("set_text", self._feedback_stats_text, "\n".join(lines)))
                prefs = prefs_result.get("preferences", []) if isinstance(prefs_result, dict) else []

                def _load_prefs():
                    if not hasattr(self, "pref_tree"):
                        return
                    self.pref_tree.delete(*self.pref_tree.get_children())
                    for p in prefs:
                        self.pref_tree.insert("", "end", values=(
                            p.get("dimension", ""), p.get("preference", ""), f"{float(p.get('confidence', 0)):.2f}"))

                self._ui_queue.put(("call", _load_prefs))
            except Exception as e:
                self._ui_queue.put(("toast", f"Feedback error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

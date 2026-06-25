"""Morning brief page mixin."""
import tkinter as tk
from tkinter import ttk
from pages.constants import *
import hub_db


class BriefPageMixin:
    def show_brief(self):
        self._set_active_nav("Brief")
        self._clear_content()
        self._section_header(
            self.content, "📋 Morning Brief",
            "AI-generated daily briefing — email, todos, markets, deadlines.",
            actions=[("🔄 Generate Brief", self._generate_morning_brief)],
        )
        stats_row = tk.Frame(self.content, bg=BG_CANVAS)
        stats_row.pack(fill="x", padx=20, pady=(0, 10))
        self.brief_total_card = self._stat_card(stats_row, "Total Runs", "0")
        self.brief_total_card.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.brief_avg_card = self._stat_card(stats_row, "Avg Score", "0.00")
        self.brief_avg_card.pack(side="left", fill="x", expand=True, padx=8)
        self.brief_todo_card = self._stat_card(stats_row, "Pending Todos", "0")
        self.brief_todo_card.pack(side="left", fill="x", expand=True, padx=(8, 0))

        brief_card = self._card(self.content, "Today's Brief")
        brief_card.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self.brief_text = self._text_widget(brief_card, height=20)
        self.brief_text.pack(fill="both", expand=True, padx=14, pady=14)
        self.brief_text.configure(state="disabled")

        hist_card = self._card(self.content, "Briefing History")
        hist_card.pack(fill="x", padx=20, pady=(0, 20))
        self.brief_history_list = tk.Listbox(hist_card, bg=BG_INPUT, fg=TEXT_PRIMARY,
                                             relief="flat", height=5, font=("Segoe UI", 9))
        self.brief_history_list.pack(fill="x", padx=14, pady=(0, 10))
        self.brief_history_list.bind("<<ListboxSelect>>", self._on_brief_history_select)
        self._load_brief_content()

    def _generate_morning_brief(self):
        import threading as _t

        self._toast("Generating brief…", ACCENT)

        def _run():
            try:
                result = self.hub.post_json("/api/briefing/morning", {})
                if result:
                    content = (result.get("brief_text") or result.get("content")
                               or result.get("brief") or str(result))
                    self._ui_queue.put(("set_text", self.brief_text, content))
                    self._ui_queue.put(("call", self._load_brief_history))
                    self._ui_queue.put(("toast", "Brief generated!", SUCCESS))
                else:
                    self._ui_queue.put(("toast", "Hub offline — cannot generate brief.", WARNING))
            except Exception as e:
                self._ui_queue.put(("toast", f"Error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _load_brief_content(self):
        import threading as _t
        stats = hub_db.agent_stats()
        if hasattr(self, "brief_total_card"):
            self.brief_total_card.value_label.configure(text=str(stats.get("total_runs", 0)))
            avg = float(stats.get("avg_score", 0.0) or 0.0)
            self.brief_avg_card.value_label.configure(text=f"{avg:.2f}")
            self.brief_todo_card.value_label.configure(text=str(len(hub_db.list_todos(status="pending"))))

        def _fetch():
            try:
                result = self.hub._get("/api/briefing/morning")
                if result and result.get("success"):
                    content = (result.get("brief_text") or result.get("content")
                               or result.get("brief") or "")
                else:
                    cached = hub_db.get_briefing_cache()
                    content = (cached.get("content") if isinstance(cached, dict) else str(cached or ""))
                self._ui_queue.put(("set_text", self.brief_text,
                                    content or "(no brief yet — click Generate Brief)"))
            except Exception:
                self._ui_queue.put(("set_text", self.brief_text, "(no brief yet — click Generate Brief)"))
            self._ui_queue.put(("call", self._load_brief_history))

        _t.Thread(target=_fetch, daemon=True).start()

    def _load_brief_history(self):
        if not hasattr(self, "brief_history_list"):
            return
        try:
            response = self.hub._get("/api/briefing/history") or {}
            items = response.get("briefs", response) if isinstance(response, dict) else response
            if not isinstance(items, list):
                items = []
            self.brief_history_list.delete(0, "end")
            self._brief_history_data = []
            for item in items:
                ts = item.get("created_at", "")[:16]
                preview = str(item.get("brief_text") or item.get("content") or "")[:60]
                self.brief_history_list.insert("end", f"{ts}  —  {preview}…")
                self._brief_history_data.append(item)
        except Exception:
            pass

    def _on_brief_history_select(self, _event):
        if not hasattr(self, "_brief_history_data"):
            return
        sel = self.brief_history_list.curselection()
        if sel and sel[0] < len(self._brief_history_data):
            item = self._brief_history_data[sel[0]]
            content = item.get("brief_text") or item.get("content") or str(item)
            self._set_text(self.brief_text, content)

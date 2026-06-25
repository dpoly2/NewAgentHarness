"""Memory page mixin."""
import tkinter as tk
import urllib.parse
from tkinter import ttk
from pages.constants import *


class MemoryPageMixin:
    def show_memory(self):
        self._set_active_nav("Memory")
        self._clear_content()
        self._section_header(self.content, "🧠 Global Memory",
                             "Persistent facts and preferences remembered across all sessions.")

        top_row = tk.Frame(self.content, bg=BG_CANVAS)
        top_row.pack(fill="x", padx=20, pady=(0, 10))
        self._mem_search_var = tk.StringVar()
        search_entry = self._entry(top_row, self._mem_search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        search_entry.insert(0, "Search facts…")
        search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, "end") if search_entry.get() == "Search facts…" else None)
        # UX: Enter key triggers search
        search_entry.bind("<Return>", lambda _e: self._search_memory_facts())
        self._button(top_row, "Search", self._search_memory_facts).pack(side="left", padx=(0, 8))
        self._button(top_row, "+ Add Fact", self._add_memory_fact, accent=True).pack(side="left")

        card = self._card(self.content, "Facts")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        cols = ("category", "subject", "value", "confidence", "usage", "updated")
        self.mem_tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        for col, txt, w in [("category", "Category", 110), ("subject", "Subject", 140), ("value", "Value", 280),
                            ("confidence", "Conf.", 60), ("usage", "Used", 50), ("updated", "Updated", 120)]:
            self.mem_tree.heading(col, text=txt)
            self.mem_tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(card, orient="vertical", command=self.mem_tree.yview)
        self.mem_tree.configure(yscrollcommand=sb.set)
        self.mem_tree.pack(side="left", fill="both", expand=True, padx=14, pady=(0, 10))
        sb.pack(side="right", fill="y", pady=(0, 10))

        btn_row = tk.Frame(card, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=14, pady=(0, 10))
        self._button(btn_row, "🔄 Refresh", self._refresh_memory_facts).pack(side="left", padx=4)
        self._button(btn_row, "🗑 Delete Selected", self._delete_memory_fact).pack(side="left", padx=4)

        # Pagination controls
        self._mem_offset = 0
        self._mem_total = 0
        PAGE = 50
        self._mem_page_lbl = tk.Label(btn_row, text="Loading…", bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._mem_page_lbl.pack(side="left", padx=(12, 4))
        self._button(btn_row, "◀ Prev", lambda: self._refresh_memory_facts(
            offset=max(0, getattr(self, "_mem_offset", 0) - PAGE))).pack(side="left", padx=2)
        self._button(btn_row, "Next ▶", lambda: self._refresh_memory_facts(
            offset=getattr(self, "_mem_offset", 0) + PAGE)).pack(side="left", padx=2)

        self._refresh_memory_facts()

    def _refresh_memory_facts(self, query="", offset=0):
        if not hasattr(self, "mem_tree"):
            return
        PAGE = 50
        self.mem_tree.delete(*self.mem_tree.get_children())
        try:
            if query:
                # Bug fix: URL-encode query string
                data = self.hub._get(f"/api/memory/global/search?q={urllib.parse.quote(query)}") or []
                facts = data if isinstance(data, list) else data.get("results", [])
                self._mem_total = len(facts)
            else:
                data = self.hub._get(f"/api/memory/global?limit={PAGE}&offset={offset}") or []
                facts = data if isinstance(data, list) else data.get("facts", [])
                counts = (data.get("counts") or {}) if isinstance(data, dict) else {}
                self._mem_total = sum(counts.values()) if counts else len(facts)
                self._mem_offset = offset
            for f in facts:
                self.mem_tree.insert("", "end", iid=str(f.get("id", "")),
                                     values=(f.get("category", ""), f.get("key", f.get("subject", "")), str(f.get("value", ""))[:80],
                                             f"{float(f.get('confidence', 0)):.2f}", f.get("usage_count", 0),
                                             str(f.get("updated_at", ""))[:16]))
            if hasattr(self, "_mem_page_lbl"):
                shown = len(facts)
                start = offset + 1
                end = offset + shown
                self._mem_page_lbl.config(text=f"Showing {start}–{end} of {self._mem_total}")
        except Exception as e:
            self._toast(f"Memory load error: {e}", ERROR)

    def _search_memory_facts(self):
        q = self._mem_search_var.get().strip()
        if q and q != "Search facts…":
            self._refresh_memory_facts(query=q)

    def _add_memory_fact(self):
        win = tk.Toplevel(self.root)
        win.title("Add Memory Fact")
        win.configure(bg=BG_PANEL)
        win.geometry("420x300")
        for label, key in [("Category", "category"), ("Subject", "subject"), ("Value", "value")]:
            tk.Label(win, text=label, bg=BG_PANEL, fg=TEXT_BODY).pack(anchor="w", padx=20, pady=(10, 2))
            var = tk.StringVar()
            setattr(win, f"_{key}_var", var)
            self._entry(win, var).pack(fill="x", padx=20)

        def _save():
            payload = {
                "category": win._category_var.get(),
                "subject": win._subject_var.get(),
                "value": win._value_var.get(),
            }
            try:
                self.hub.post_json("/api/memory/global", payload)
                self._refresh_memory_facts()
                self._toast("Fact saved.", SUCCESS)
                win.destroy()
            except Exception as e:
                self._toast(f"Error: {e}", ERROR)

        self._button(win, "Save Fact", _save, accent=True).pack(pady=16)

    def _delete_memory_fact(self):
        if not hasattr(self, "mem_tree"):
            return
        sel = self.mem_tree.selection()
        if not sel:
            self._toast("Select a fact first.", WARNING)
            return
        fact_id = sel[0]
        try:
            self.hub.delete(f"/api/memory/global/{fact_id}")
            self.mem_tree.delete(fact_id)
            self._toast("Fact deleted.", SUCCESS)
        except Exception as e:
            self._toast(f"Error: {e}", ERROR)

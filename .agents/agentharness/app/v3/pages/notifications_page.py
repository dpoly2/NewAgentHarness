"""Notifications page mixin."""
import tkinter as tk
from tkinter import ttk
from pages.constants import *


class NotificationsPageMixin:
    def show_notifications(self):
        self._set_active_nav("Notifs")
        self._clear_content()
        self._section_header(self.content, "🔔 Notifications",
                             "System alerts and proactive monitoring notifications.")

        top_row = tk.Frame(self.content, bg=BG_CANVAS)
        top_row.pack(fill="x", padx=20, pady=(0, 10))
        self._button(top_row, "🔄 Refresh", self._refresh_notifications).pack(side="left", padx=(0, 8))
        self._button(top_row, "✓ Mark All Read", self._mark_notifs_read).pack(side="left", padx=(0, 8))
        self._button(top_row, "🗑 Clear All", self._clear_notifications, accent=False).pack(side="left")

        card = self._card(self.content, "Notifications")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        cols = ("category", "text", "color", "created")
        self.notif_tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")
        for col, txt, w in [("category", "Category", 100), ("text", "Message", 420),
                             ("color", "Level", 70), ("created", "When", 130)]:
            self.notif_tree.heading(col, text=txt)
            self.notif_tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(card, orient="vertical", command=self.notif_tree.yview)
        self.notif_tree.configure(yscrollcommand=sb.set)
        self.notif_tree.pack(side="left", fill="both", expand=True, padx=14, pady=(0, 10))
        sb.pack(side="right", fill="y", pady=(0, 10))
        self._refresh_notifications()

    def _refresh_notifications(self):
        if not hasattr(self, "notif_tree"):
            return
        self.notif_tree.delete(*self.notif_tree.get_children())
        try:
            data = self.hub._get("/api/notifications") or []
            items = data if isinstance(data, list) else data.get("notifications", [])
            for n in items:
                tag = "unread" if not n.get("read") else ""
                self.notif_tree.insert("", "end", iid=str(n.get("id", "")),
                                       values=(n.get("category", ""), n.get("text", ""),
                                               n.get("color", ""), str(n.get("created_at", ""))[:16]),
                                       tags=(tag,))
            self.notif_tree.tag_configure("unread", foreground=ACCENT)
        except Exception as e:
            self._toast(f"Notifications load error: {e}", ERROR)

    def _mark_notifs_read(self):
        try:
            self.hub.post_json("/api/notifications/read", {})
            self._refresh_notifications()
            self._toast("All marked read.", SUCCESS)
        except Exception as e:
            self._toast(f"Error: {e}", ERROR)

    def _clear_notifications(self):
        try:
            self.hub.delete("/api/notifications")
            self._refresh_notifications()
            self._toast("Notifications cleared.", SUCCESS)
        except Exception as e:
            self._toast(f"Error: {e}", ERROR)

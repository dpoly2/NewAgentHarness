"""Email connectors page mixin."""
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk
from pages.constants import *
import hub_db


class ConnectorsPageMixin:

    _PROVIDER_PRESETS = {
        "gmail":   {"imap_host": "imap.gmail.com",          "imap_port": "993",
                    "smtp_host": "smtp.gmail.com",           "smtp_port": "587", "oauth": True},
        "outlook": {"imap_host": "outlook.office365.com",   "imap_port": "993",
                    "smtp_host": "smtp.office365.com",       "smtp_port": "587", "oauth": True},
        "imap":    {"imap_host": "",    "imap_port": "993",
                    "smtp_host": "",    "smtp_port": "587",  "oauth": False},
        "zoho":    {"imap_host": "imap.zoho.com",            "imap_port": "993",
                    "smtp_host": "smtp.zoho.com",            "smtp_port": "587", "oauth": False},
        "yahoo":   {"imap_host": "imap.mail.yahoo.com",      "imap_port": "993",
                    "smtp_host": "smtp.mail.yahoo.com",      "smtp_port": "587", "oauth": False},
    }

    def show_connectors(self):
        self._set_active_nav("Connect")
        self._clear_content()
        self._section_header(self.content, "Email Connectors", "Manage Gmail, Outlook, and IMAP accounts.")

        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        connectors_tab = tk.Frame(notebook, bg=BG_CANVAS)
        cleanup_tab = tk.Frame(notebook, bg=BG_CANVAS)
        notebook.add(connectors_tab, text="Connectors")
        notebook.add(cleanup_tab, text="📧 Email Cleanup")

        paned = tk.PanedWindow(connectors_tab, orient="horizontal", sashwidth=6, bg=BG_CANVAS, relief="flat")
        paned.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        left = tk.Frame(paned, bg=BG_CANVAS, width=540)
        right = tk.Frame(paned, bg=BG_CANVAS)
        paned.add(left, minsize=500)
        paned.add(right, minsize=360)

        # ── Left: Account List ────────────────────────────────────────────
        list_card = self._card(left, "Connected Accounts")
        list_card.pack(fill="both", expand=True)

        columns = ("label", "email", "provider", "auth", "status")
        self.connectors_tree = ttk.Treeview(list_card, columns=columns, show="headings", selectmode="browse", height=14)
        for col, text, width in (
            ("label",    "Label",    140),
            ("email",    "Email",    200),
            ("provider", "Provider",  90),
            ("auth",     "Auth",      90),
            ("status",   "Status",   100),
        ):
            self.connectors_tree.heading(col, text=text)
            self.connectors_tree.column(col, width=width, anchor="w")
        vsb = ttk.Scrollbar(list_card, orient="vertical", command=self.connectors_tree.yview)
        self.connectors_tree.configure(yscrollcommand=vsb.set)
        self.connectors_tree.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=(0, 10))
        vsb.pack(side="left", fill="y", pady=(0, 10), padx=(0, 6))
        self.connectors_tree.bind("<<TreeviewSelect>>", self._on_connector_select)

        action_bar = tk.Frame(list_card, bg=BG_PANEL)
        action_bar.pack(fill="x", padx=14, pady=(0, 14))
        self._button(action_bar, "🔌 Test",     self._test_selected_connector, accent=True).pack(side="left", padx=4)
        self._button(action_bar, "🔄 Re-Auth",  self._reauth_selected_connector).pack(side="left", padx=4)
        self._button(action_bar, "🗑 Delete",   self._delete_selected_connector).pack(side="left", padx=4)
        self._button(action_bar, "↻ Refresh",   self._refresh_connectors).pack(side="right", padx=4)

        # ── Right: Notebook (Add / Details) ──────────────────────────────
        right_nb = ttk.Notebook(right, style="Dark.TNotebook")
        right_nb.pack(fill="both", expand=True)

        add_frame = tk.Frame(right_nb, bg=BG_PANEL)
        detail_frame = tk.Frame(right_nb, bg=BG_PANEL)
        right_nb.add(add_frame,    text="  ➕ Add Account  ")
        right_nb.add(detail_frame, text="  🔍 Details  ")

        # ── Add Account tab ──────────────────────────────────────────────
        self._connector_vars = {
            "label":              tk.StringVar(),
            "email_address":      tk.StringVar(),
            "provider":           tk.StringVar(value="gmail"),
            "oauth_client_id":    tk.StringVar(),
            "oauth_client_secret":tk.StringVar(),
            "imap_host":          tk.StringVar(),
            "imap_port":          tk.StringVar(value="993"),
            "smtp_host":          tk.StringVar(),
            "smtp_port":          tk.StringVar(value="587"),
            "username":           tk.StringVar(),
            "password":           tk.StringVar(),
        }

        add_scroll = tk.Frame(add_frame, bg=BG_PANEL)
        add_scroll.pack(fill="both", expand=True, padx=14, pady=12)

        for lbl, key in [("Label *", "label"), ("Email Address *", "email_address")]:
            tk.Label(add_scroll, text=lbl, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
            self._entry(add_scroll, self._connector_vars[key]).pack(fill="x")

        tk.Label(add_scroll, text="Provider *", bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
        provider_combo = self._combo(add_scroll, self._connector_vars["provider"],
                                     ["gmail", "outlook", "imap", "zoho", "yahoo"])
        provider_combo.pack(fill="x")

        self._connector_dyn_frame = tk.Frame(add_scroll, bg=BG_PANEL)
        self._connector_dyn_frame.pack(fill="x")
        self._connector_add_btn_frame = tk.Frame(add_scroll, bg=BG_PANEL)
        self._connector_add_btn_frame.pack(fill="x", pady=(12, 0))

        self._connector_vars["provider"].trace_add("write", lambda *_: self._rebuild_connector_form())
        self._rebuild_connector_form()

        # ── Details tab ──────────────────────────────────────────────────
        self._connector_detail_vars = {
            "label":    tk.StringVar(value="—"),
            "email":    tk.StringVar(value="—"),
            "provider": tk.StringVar(value="—"),
            "auth":     tk.StringVar(value="—"),
            "status":   tk.StringVar(value="—"),
            "token":    tk.StringVar(value="—"),
            "synced":   tk.StringVar(value="—"),
            "error":    tk.StringVar(value=""),
        }
        self._connector_selected_id = None

        det = detail_frame
        for label, key in [
            ("Label",          "label"),
            ("Email",          "email"),
            ("Provider",       "provider"),
            ("Auth Type",      "auth"),
            ("Status",         "status"),
            ("Token / Auth",   "token"),
            ("Last Synced",    "synced"),
        ]:
            tk.Label(det, text=label, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(8, 2))
            tk.Label(det, textvariable=self._connector_detail_vars[key],
                     bg=BG_PANEL, fg=TEXT_BODY, font=("Segoe UI", 10, "bold"), wraplength=280, justify="left").pack(anchor="w", padx=14)

        tk.Label(det, text="Last Error", bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(8, 2))
        self._connector_err_label = tk.Label(det, textvariable=self._connector_detail_vars["error"],
                                              bg=BG_PANEL, fg=ERROR, font=("Segoe UI", 9), wraplength=280, justify="left")
        self._connector_err_label.pack(anchor="w", padx=14)

        det_btns = tk.Frame(det, bg=BG_PANEL)
        det_btns.pack(anchor="w", padx=14, pady=(16, 0))
        self._button(det_btns, "🔌 Test Connection", self._test_selected_connector, accent=True).pack(side="left", padx=(0, 8))
        self._button(det_btns, "🔄 Re-Authorize",    self._reauth_selected_connector).pack(side="left")

        self._right_nb_connectors = right_nb
        self._refresh_connectors()
        self._build_email_cleanup_tab(cleanup_tab)

    def _build_email_cleanup_tab(self, parent):
        top = tk.Frame(parent, bg=BG_CANVAS)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Connector:", bg=BG_CANVAS, fg=TEXT_BODY).pack(side="left")
        self._cleanup_connector_var = tk.StringVar()
        connectors = []
        try:
            connectors = self.hub._get("/api/connectors") or []
            connectors = connectors if isinstance(connectors, list) else connectors.get("connectors", [])
        except Exception:
            pass
        connector_names = [f"{c.get('label', '')} ({c.get('email', '')})" for c in connectors]
        self._cleanup_connectors_data = connectors
        combo = self._combo(top, self._cleanup_connector_var, connector_names or ["(no connectors)"])
        combo.pack(side="left", padx=(8, 16))
        if connector_names:
            self._cleanup_connector_var.set(connector_names[0])

        self._button(top, "🔍 Analyze Inbox", self._analyze_email_cleanup, accent=True).pack(side="left")

        self._cleanup_status_lbl = tk.Label(parent, text="Select a connector and click Analyze.",
                                            bg=BG_CANVAS, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._cleanup_status_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        plan_card = self._card(parent, "Cleanup Plan")
        plan_card.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        cols = ("category", "count", "action", "status")
        self.cleanup_tree = ttk.Treeview(plan_card, columns=cols, show="headings", selectmode="browse")
        for col, txt, w in [("category", "Category", 160), ("count", "Count", 70),
                            ("action", "Suggested Action", 200), ("status", "Status", 100)]:
            self.cleanup_tree.heading(col, text=txt)
            self.cleanup_tree.column(col, width=w, anchor="w")
        self.cleanup_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._cleanup_plan_id = None

        btn_row = tk.Frame(plan_card, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=14, pady=(0, 10))
        self._button(btn_row, "✅ Approve Plan", self._approve_cleanup_plan, accent=True).pack(side="left", padx=4)
        self._button(btn_row, "▶ Execute Plan", self._execute_cleanup_plan).pack(side="left", padx=4)
        self._button(btn_row, "↩ Rollback", self._rollback_cleanup_plan).pack(side="left", padx=4)

    def _analyze_email_cleanup(self):
        idx = 0
        try:
            for i, c in enumerate(getattr(self, "_cleanup_connectors_data", [])):
                if f"{c.get('label', '')} ({c.get('email', '')})" == self._cleanup_connector_var.get():
                    idx = i
                    break
        except Exception:
            pass
        connectors = getattr(self, "_cleanup_connectors_data", [])
        if not connectors:
            self._toast("No connectors available.", WARNING)
            return
        connector_id = connectors[idx].get("id") if idx < len(connectors) else None
        if not connector_id:
            self._toast("Could not resolve connector ID.", WARNING)
            return
        import threading as _t

        self._toast("Analyzing inbox…", ACCENT)
        if hasattr(self, "_cleanup_status_lbl"):
            self._cleanup_status_lbl.configure(text="Analyzing inbox… this may take 30-60 seconds.")

        def _run():
            try:
                result = self.hub.post_json("/api/email/cleanup/analyze", {"connector_id": connector_id, "limit": 200})
                if result and result.get("success"):
                    plan_id = result.get("plan_id")
                    summary = result.get("summary", {})
                    self._cleanup_plan_id = plan_id
                    plan_detail = self.hub._get(f"/api/email/cleanup/plans/{plan_id}") or {}
                    plan = plan_detail.get("plan", {})
                    categories = plan.get("categories", {})
                    cat_rows = []
                    for cat_name, items in categories.items():
                        cat_rows.append({
                            "category": cat_name,
                            "count": len(items),
                            "action": items[0].get("action", "archive") if items else "archive",
                            "status": "pending",
                            "_item_ids": [i.get("id") for i in items],
                        })
                    self._cleanup_item_ids_by_cat = {r["category"]: r["_item_ids"] for r in cat_rows}
                    self._ui_queue.put(("call_with_arg", self._populate_cleanup_plan, cat_rows))
                    total = summary.get("total_suggested", 0)
                    mb = summary.get("estimated_space_mb", 0)
                    self._ui_queue.put(("toast", f"Analysis complete — {total} emails, ~{mb} MB.", SUCCESS))
                    self._ui_queue.put(("configure", self._cleanup_status_lbl,
                                        {"text": f"Plan ready (ID: {plan_id}). Approve then Execute."}))
                else:
                    self._ui_queue.put(("toast", "Analysis returned no data.", WARNING))
            except Exception as e:
                self._ui_queue.put(("toast", f"Analysis error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _populate_cleanup_plan(self, categories):
        if not hasattr(self, "cleanup_tree"):
            return
        self.cleanup_tree.delete(*self.cleanup_tree.get_children())
        for cat in (categories if isinstance(categories, list) else []):
            self.cleanup_tree.insert("", "end", values=(
                cat.get("category", cat.get("name", "")),
                cat.get("count", 0),
                cat.get("action", cat.get("suggested_action", "")),
                cat.get("status", "pending"),
            ))

    def _approve_cleanup_plan(self):
        if not self._cleanup_plan_id:
            self._toast("No plan to approve. Run analysis first.", WARNING)
            return
        item_ids = []
        for ids in getattr(self, "_cleanup_item_ids_by_cat", {}).values():
            item_ids.extend(ids)
        if not item_ids:
            try:
                plan = (self.hub._get(f"/api/email/cleanup/plans/{self._cleanup_plan_id}") or {}).get("plan", {})
                item_ids = [i.get("id") for i in plan.get("items", []) if i.get("id")]
            except Exception as e:
                self._toast(f"Could not load items: {e}", ERROR)
                return
        try:
            self.hub.put_json(f"/api/email/cleanup/plans/{self._cleanup_plan_id}/approve",
                              {"item_ids": item_ids})
            self._toast(f"Approved {len(item_ids)} items.", SUCCESS)
        except Exception as e:
            self._toast(f"Approve error: {e}", ERROR)

    def _execute_cleanup_plan(self):
        if not self._cleanup_plan_id:
            self._toast("Approve a plan first.", WARNING)
            return
        import threading as _t

        self._toast("Executing cleanup…", ACCENT)

        def _run():
            try:
                result = self.hub.post_json(f"/api/email/cleanup/plans/{self._cleanup_plan_id}/execute", {})
                executed = result.get("executed", 0) if result else 0
                self._ui_queue.put(("toast", f"Cleanup done — {executed} actions.", SUCCESS))
            except Exception as e:
                self._ui_queue.put(("toast", f"Execute error: {e}", ERROR))

        _t.Thread(target=_run, daemon=True).start()

    def _rollback_cleanup_plan(self):
        if not self._cleanup_plan_id:
            self._toast("No plan to rollback.", WARNING)
            return
        try:
            self.hub.post_json(f"/api/email/cleanup/plans/{self._cleanup_plan_id}/rollback", {})
            self._toast("Rollback complete.", SUCCESS)
        except Exception as e:
            self._toast(f"Rollback error: {e}", ERROR)

    def _rebuild_connector_form(self):
        """Destroy and rebuild the dynamic form section based on selected provider."""
        for w in self._connector_dyn_frame.winfo_children():
            w.destroy()
        for w in self._connector_add_btn_frame.winfo_children():
            w.destroy()

        provider = self._connector_vars["provider"].get()
        preset = self._PROVIDER_PRESETS.get(provider, self._PROVIDER_PRESETS["imap"])

        self._connector_vars["imap_host"].set(preset["imap_host"])
        self._connector_vars["imap_port"].set(preset["imap_port"])
        self._connector_vars["smtp_host"].set(preset["smtp_host"])
        self._connector_vars["smtp_port"].set(preset["smtp_port"])

        f = self._connector_dyn_frame

        if preset["oauth"]:
            provider_name = "Google" if provider == "gmail" else "Microsoft"
            console_name  = "Google Cloud Console" if provider == "gmail" else "Azure App Registration"
            help_url = (
                "https://console.cloud.google.com/apis/credentials"
                if provider == "gmail"
                else "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps"
            )

            last_provider = getattr(self, "_connector_oauth_provider", None)
            if last_provider != provider:
                self._connector_vars["oauth_client_id"].set("")
                self._connector_vars["oauth_client_secret"].set("")
                self._connector_oauth_provider = provider

            saved_id  = hub_db.get_config(f"oauth_{provider}_client_id")  or ""
            saved_sec = hub_db.get_config(f"oauth_{provider}_client_secret") or ""
            if saved_id:
                self._connector_vars["oauth_client_id"].set(saved_id)
                self._connector_vars["oauth_client_secret"].set(saved_sec)

            note = (
                f"One {console_name} app works for ALL your {provider_name} accounts.\n"
                f"Create credentials once — then add as many emails as you like."
            )
            tk.Label(f, text=note, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9),
                     wraplength=280, justify="left").pack(anchor="w", pady=(10, 6))

            if saved_id:
                saved_row = tk.Frame(f, bg=BG_PANEL)
                saved_row.pack(fill="x", pady=(0, 4))
                tk.Label(saved_row, text=f"✅ Using saved {provider_name} credentials",
                         bg=BG_PANEL, fg=SUCCESS, font=("Segoe UI", 9)).pack(side="left")
                clr = tk.Label(saved_row, text="  🔄 Change", bg=BG_PANEL,
                               fg=ACCENT, font=("Segoe UI", 9, "underline"), cursor="hand2")
                clr.pack(side="left")
                clr.bind("<Button-1>", lambda _e, p=provider: self._clear_oauth_defaults(p))

            secret_lbl = f"{provider_name} Client Secret {'*' if provider == 'gmail' else '(optional)'}"
            for lbl, key in [(f"{provider_name} Client ID *", "oauth_client_id"),
                             (secret_lbl, "oauth_client_secret")]:
                tk.Label(f, text=lbl, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 2))
                show = "*" if "secret" in key else None
                self._entry(f, self._connector_vars[key], show=show).pack(fill="x")

            btn_row = tk.Frame(f, bg=BG_PANEL)
            btn_row.pack(fill="x", pady=(6, 0))
            self._button(btn_row, "💾 Save as defaults",
                         lambda p=provider: self._save_oauth_defaults(p)).pack(side="left")
            lnk = tk.Label(btn_row, text=f"📋 {provider_name} Console →",
                           bg=BG_PANEL, fg=ACCENT, font=("Segoe UI", 9, "underline"), cursor="hand2")
            lnk.pack(side="right")
            lnk.bind("<Button-1>", lambda _e: webbrowser.open(help_url))

            redirect_note = tk.Label(
                f,
                text=f"Redirect URI:  http://localhost:8765/api/connectors/oauth/{provider}/callback",
                bg=BG_PANEL, fg="#6b7a99", font=("Segoe UI", 8),
            )
            redirect_note.pack(anchor="w", pady=(4, 8))

            self._button(self._connector_add_btn_frame,
                         f"🔐 Authorize with {provider_name}",
                         lambda p=provider: self._create_and_authorize(p),
                         accent=True).pack(fill="x", pady=(0, 4))

            if provider == "outlook":
                self._button(self._connector_add_btn_frame,
                             "🖥 Device Code (no browser redirect)",
                             self._start_device_code_flow).pack(fill="x")

        else:
            self._connector_oauth_provider = None
            for lbl, key, show in [
                ("IMAP Host",  "imap_host",  None),
                ("IMAP Port",  "imap_port",  None),
                ("SMTP Host",  "smtp_host",  None),
                ("SMTP Port",  "smtp_port",  None),
                ("Username",   "username",   None),
                ("Password",   "password",   "*"),
            ]:
                tk.Label(f, text=lbl, bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 2))
                self._entry(f, self._connector_vars[key], show=show).pack(fill="x")

            self._button(self._connector_add_btn_frame, "➕ Add Connector",
                         self._add_password_connector, accent=True).pack(fill="x")

    def _create_and_authorize(self, provider: str):
        """Save connector then open browser for OAuth authorization."""
        data = {k: v.get().strip() for k, v in self._connector_vars.items()}
        if not data["label"] or not data["email_address"]:
            self.show_toast("Label and email are required.", WARNING)
            return

        if not data["oauth_client_id"]:
            data["oauth_client_id"]     = hub_db.get_config(f"oauth_{provider}_client_id")  or ""
            data["oauth_client_secret"] = hub_db.get_config(f"oauth_{provider}_client_secret") or ""

        if not data["oauth_client_id"]:
            self.show_toast("Client ID is required.", WARNING)
            return
        if provider == "gmail" and not data["oauth_client_secret"]:
            self.show_toast("Client Secret is required for Gmail.", WARNING)
            return

        preset = self._PROVIDER_PRESETS.get(provider, {})
        connector = hub_db.create_connector(
            label=data["label"],
            email_address=data["email_address"],
            provider=provider,
            auth_type="oauth2",
            imap_host=preset.get("imap_host", ""),
            imap_port=int(preset.get("imap_port", 993)),
            smtp_host=preset.get("smtp_host", ""),
            smtp_port=int(preset.get("smtp_port", 587)),
            username=data["email_address"],
            oauth_client_id=data["oauth_client_id"],
            oauth_client_secret=data["oauth_client_secret"],
        )
        connector_id = connector["id"]
        self._refresh_connectors()
        self.show_toast(f"Connector created — opening browser for authorization…", ACCENT)
        self._start_oauth_flow(connector_id, provider)

    def _add_password_connector(self):
        """Save a plain-password IMAP connector."""
        data = {k: v.get().strip() for k, v in self._connector_vars.items()}
        if not data["label"] or not data["email_address"]:
            self.show_toast("Label and email are required.", WARNING)
            return
        hub_db.create_connector(
            label=data["label"],
            email_address=data["email_address"],
            provider=data["provider"],
            auth_type="password",
            imap_host=data["imap_host"],
            imap_port=int(data["imap_port"] or 993),
            smtp_host=data["smtp_host"],
            smtp_port=int(data["smtp_port"] or 587),
            username=data["username"],
            credentials={"password": data["password"]},
        )
        for key, var in self._connector_vars.items():
            if key not in ("provider",):
                var.set("")
        self._refresh_connectors()
        self.show_toast("Connector added.", SUCCESS)

    # ── OAuth credential helpers ───────────────────────────────────────────────

    def _save_oauth_defaults(self, provider: str):
        """Persist current Client ID/Secret to hub_config for reuse across accounts."""
        client_id  = self._connector_vars["oauth_client_id"].get().strip()
        client_sec = self._connector_vars["oauth_client_secret"].get().strip()
        if not client_id:
            self.show_toast("Enter a Client ID first.", WARNING)
            return
        hub_db.set_config(f"oauth_{provider}_client_id", client_id)
        hub_db.set_config(f"oauth_{provider}_client_secret", client_sec)
        self.show_toast(f"✅ {provider.title()} credentials saved — will auto-fill for future accounts.", SUCCESS)
        self._rebuild_connector_form()

    def _clear_oauth_defaults(self, provider: str):
        """Remove saved default credentials so the user can enter new ones."""
        hub_db.set_config(f"oauth_{provider}_client_id", "")
        hub_db.set_config(f"oauth_{provider}_client_secret", "")
        self._connector_vars["oauth_client_id"].set("")
        self._connector_vars["oauth_client_secret"].set("")
        self._connector_oauth_provider = None
        self._rebuild_connector_form()

    def _start_device_code_flow(self):
        """Create a Microsoft connector then initiate Device Code flow (no browser redirect)."""
        data = {k: v.get().strip() for k, v in self._connector_vars.items()}
        if not data["label"] or not data["email_address"]:
            self.show_toast("Label and email are required.", WARNING)
            return
        client_id  = (data["oauth_client_id"]
                      or hub_db.get_config("oauth_outlook_client_id") or "")
        client_sec = (data["oauth_client_secret"]
                      or hub_db.get_config("oauth_outlook_client_secret") or "")
        if not client_id:
            self.show_toast("Client ID is required for Device Code flow.", WARNING)
            return

        preset = self._PROVIDER_PRESETS.get("outlook", {})
        connector = hub_db.create_connector(
            label=data["label"],
            email_address=data["email_address"],
            provider="outlook",
            auth_type="oauth2",
            imap_host=preset.get("imap_host", ""),
            imap_port=int(preset.get("imap_port", 993)),
            smtp_host=preset.get("smtp_host", ""),
            smtp_port=int(preset.get("smtp_port", 587)),
            username=data["email_address"],
            oauth_client_id=client_id,
            oauth_client_secret=client_sec,
        )
        connector_id = connector["id"]
        self._refresh_connectors()
        self.show_toast("Initiating device code flow…", ACCENT)

        def _do():
            try:
                from oauth_connector import MicrosoftOAuth
                m    = MicrosoftOAuth(client_id, client_sec, connector_id)
                flow = m.get_device_code_flow()
                self._ui_queue.put(("device_code_dialog", flow, m, connector_id))
            except ImportError:
                self._ui_queue.put(("toast", "msal not installed. Run: pip install msal", ERROR))
            except Exception as exc:
                self._ui_queue.put(("toast", f"Device code error: {exc}", ERROR))

        threading.Thread(target=_do, daemon=True).start()

    def _device_code_dialog(self, flow: dict, ms_oauth, connector_id: str):
        """Show a dialog with the device code + poll for completion in background."""
        import time as _t

        user_code = flow.get("user_code", "")
        verify_uri = flow.get("verification_uri", "https://microsoft.com/devicelogin")
        expires_in = flow.get("expires_in", 900)

        dlg = tk.Toplevel(self.root)
        dlg.title("Microsoft Device Code Authorization")
        dlg.configure(bg=BG_DARK)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="🖥  Authorize ArchonHub — Microsoft Device Code",
                 bg=BG_DARK, fg=TEXT_PRIMARY, font=("Segoe UI", 13, "bold")).pack(pady=(20, 8))

        tk.Label(dlg, text="1. Open your browser and go to:",
                 bg=BG_DARK, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=24)

        uri_lbl = tk.Label(dlg, text=verify_uri, bg=BG_DARK, fg=ACCENT,
                           font=("Segoe UI", 10, "underline"), cursor="hand2")
        uri_lbl.pack(anchor="w", padx=24)
        uri_lbl.bind("<Button-1>", lambda _: webbrowser.open(verify_uri))

        tk.Label(dlg, text="2. Enter this code when prompted:",
                 bg=BG_DARK, fg=TEXT_MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(10, 4))

        code_frame = tk.Frame(dlg, bg="#1a0f3a", bd=0, highlightthickness=2,
                              highlightbackground=ACCENT)
        code_frame.pack(padx=24, pady=(0, 12))
        tk.Label(code_frame, text=user_code, bg="#1a0f3a", fg="#c4b5fd",
                 font=("Courier New", 24, "bold"), padx=20, pady=10).pack()

        def _copy():
            dlg.clipboard_clear()
            dlg.clipboard_append(user_code)
            copy_btn.configure(text="✅ Copied!")
            dlg.after(2000, lambda: copy_btn.configure(text="📋 Copy Code"))
        copy_btn = self._button(dlg, "📋 Copy Code", _copy)
        copy_btn.pack(pady=(0, 8))

        status_var = tk.StringVar(value=f"⏳ Waiting for authorization… (expires in {expires_in//60} min)")
        status_lbl = tk.Label(dlg, textvariable=status_var, bg=BG_DARK, fg=TEXT_MUTED,
                              font=("Segoe UI", 9), wraplength=340)
        status_lbl.pack(padx=24, pady=(0, 16))

        cancel_var = [False]
        def _cancel():
            cancel_var[0] = True
            dlg.destroy()
        self._button(dlg, "Cancel", _cancel).pack(pady=(0, 16))

        def _poll():
            try:
                token = ms_oauth.poll_device_code(flow)
                if cancel_var[0]:
                    return
                email = token.get("id_token_claims", {}).get("email", "") or ""
                self._ui_queue.put(("toast", f"✅ Microsoft account authorized! {email}", SUCCESS))
                self._ui_queue.put(("refresh_connectors",))
                try:
                    dlg.after(0, dlg.destroy)
                except Exception:
                    pass
            except Exception as exc:
                if not cancel_var[0]:
                    self._ui_queue.put(("toast", f"Device code failed: {exc}", ERROR))

        threading.Thread(target=_poll, daemon=True).start()

    def _start_oauth_flow(self, connector_id: str, provider: str):
        """Call hub server to get OAuth URL, open browser, then poll for completion."""
        import urllib.request as _ur
        import json as _json

        def _do():
            try:
                url = f"http://localhost:8765/api/connectors/oauth/{provider}/init?connector_id={connector_id}"
                req = _ur.Request(url, headers={"Accept": "application/json"})
                token = getattr(self, "_hub_token", None)
                if token:
                    req.add_header("Authorization", f"Bearer {token}")
                try:
                    with _ur.urlopen(req, timeout=8) as resp:
                        payload = _json.loads(resp.read())
                    auth_url = payload.get("auth_url", "")
                except Exception:
                    auth_url = self._build_local_oauth_url(connector_id, provider)

                if not auth_url:
                    self._ui_queue.put(("toast", "Could not get OAuth URL. Is the Hub server running?", WARNING))
                    return

                webbrowser.open(auth_url)
                self._ui_queue.put(("toast", "Browser opened — complete authorization, then return here.", ACCENT))

                for _ in range(60):
                    import time as _t
                    _t.sleep(2)
                    fresh = hub_db.get_connector(connector_id)
                    if fresh and fresh.get("status") == "active":
                        self._ui_queue.put(("toast", f"✅ {fresh.get('email_address', '')} authorized!", SUCCESS))
                        self._ui_queue.put(("refresh_connectors",))
                        return
                self._ui_queue.put(("toast", "Authorization timed out. Check connector status.", WARNING))
                self._ui_queue.put(("refresh_connectors",))
            except Exception as exc:
                self._ui_queue.put(("toast", f"OAuth flow error: {exc}", ERROR))

        threading.Thread(target=_do, daemon=True).start()

    def _build_local_oauth_url(self, connector_id: str, provider: str) -> str:
        """Build OAuth URL directly using oauth_connector module (hub server fallback)."""
        try:
            connector = hub_db.get_connector(connector_id)
            if not connector:
                return ""
            client_id  = connector.get("oauth_client_id", "")
            client_sec = connector.get("oauth_client_secret", "")
            if provider == "gmail":
                from oauth_connector import GoogleOAuth, store_pending_state
                g = GoogleOAuth(client_id, client_sec, connector_id)
                url, state, verifier = g.get_authorization_url()
                store_pending_state(state, connector_id, "google", verifier)
                return url
            else:
                from oauth_connector import MicrosoftOAuth, store_pending_state
                m = MicrosoftOAuth(client_id, client_sec, connector_id)
                url, state = m.get_authorization_url()
                store_pending_state(state, connector_id, "microsoft")
                return url
        except Exception:
            return ""

    def _reauth_selected_connector(self):
        """Re-run OAuth for the selected connector."""
        if not self._connector_selected_id:
            self.show_toast("Select a connector first.", WARNING)
            return
        connector = hub_db.get_connector(self._connector_selected_id)
        if not connector:
            return
        provider = connector.get("provider", "")
        if provider not in ("gmail", "outlook"):
            self.show_toast("Re-authorization is only for OAuth connectors.", WARNING)
            return
        self.show_toast("Opening browser for re-authorization…", ACCENT)
        self._start_oauth_flow(self._connector_selected_id, provider)

    def _refresh_connectors(self):
        import time as _t
        rows = hub_db.list_connectors()
        self.connectors_tree.delete(*self.connectors_tree.get_children())
        self._connector_lookup = {}
        now_ts = _t.time()
        for row in rows:
            cid = row["id"]
            self._connector_lookup[cid] = row
            provider  = row.get("provider", "")
            auth_type = row.get("auth_type", "password")
            status    = row.get("status", "pending")

            if auth_type == "oauth2":
                exp_str = row.get("token_expires_at", "")
                if exp_str and exp_str.isdigit():
                    exp_ts = int(exp_str)
                    if exp_ts < now_ts:
                        auth_display = "⚠️ expired"
                        if status == "active":
                            status = "token_expired"
                    else:
                        hours_left = (exp_ts - now_ts) / 3600
                        auth_display = f"🔑 OAuth2 ({hours_left:.0f}h)"
                else:
                    auth_display = "🔑 OAuth2"
            else:
                auth_display = "🔒 password"

            status_tag = status
            self.connectors_tree.insert(
                "", "end", iid=cid,
                values=(row.get("label", ""), row.get("email_address", ""),
                        provider, auth_display, status),
                tags=(status_tag,),
            )

        from pages.constants import STATUS_COLORS as _SC
        for tag, color in {
            **_SC,
            "active":        SUCCESS,
            "token_expired": WARNING,
            "error":         ERROR,
            "pending":       TEXT_MUTED,
        }.items():
            self.connectors_tree.tag_configure(tag, foreground=color)

        if self._connector_selected_id and self._connector_selected_id in self._connector_lookup:
            self._load_connector_detail(self._connector_lookup[self._connector_selected_id])

    def _on_connector_select(self, _event=None):
        sel = self.connectors_tree.selection()
        self._connector_selected_id = sel[0] if sel else None
        if self._connector_selected_id and self._connector_selected_id in self._connector_lookup:
            self._load_connector_detail(self._connector_lookup[self._connector_selected_id])
            if hasattr(self, "_right_nb_connectors"):
                self._right_nb_connectors.select(1)

    def _load_connector_detail(self, row: dict):
        import time as _t
        now_ts = _t.time()
        auth_type = row.get("auth_type", "password")
        exp_str   = row.get("token_expires_at", "")

        if auth_type == "oauth2" and exp_str and exp_str.isdigit():
            exp_ts = int(exp_str)
            if exp_ts < now_ts:
                token_disp = "⚠️ Token expired — re-authorize required"
            else:
                left_secs = exp_ts - now_ts
                h = int(left_secs // 3600)
                m = int((left_secs % 3600) // 60)
                token_disp = f"🔑 Valid — expires in {h}h {m}m"
        elif auth_type == "oauth2":
            token_disp = "🔒 Not yet authorized"
        else:
            token_disp = "🔒 Password auth"

        synced = row.get("last_synced") or "Never"
        if synced != "Never":
            try:
                synced = datetime.fromisoformat(synced).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        self._connector_detail_vars["label"].set(row.get("label", "—"))
        self._connector_detail_vars["email"].set(row.get("email_address", "—"))
        self._connector_detail_vars["provider"].set(row.get("provider", "—"))
        self._connector_detail_vars["auth"].set(auth_type)
        self._connector_detail_vars["status"].set(row.get("status", "—"))
        self._connector_detail_vars["token"].set(token_disp)
        self._connector_detail_vars["synced"].set(synced)
        self._connector_detail_vars["error"].set(row.get("last_error") or "")

    def _set_selected_connector(self):
        self._on_connector_select()

    def _test_selected_connector(self):
        if not self._connector_selected_id or self._connector_selected_id not in self._connector_lookup:
            self.show_toast("Select a connector first.", WARNING)
            return
        connector = self._connector_lookup[self._connector_selected_id]

        def _thread():
            try:
                from oauth_connector import test_connector as _tc
                ok, msg = _tc(connector)
            except Exception as exc:
                ok, msg = False, str(exc)

            hub_db.update_connector(
                self._connector_selected_id,
                status="active" if ok else "error",
                last_error="" if ok else msg,
                last_synced=datetime.now().isoformat() if ok else None,
            )
            color = SUCCESS if ok else ERROR
            self._ui_queue.put(("toast", f"{'✅' if ok else '❌'} {msg}", color))
            self._ui_queue.put(("refresh_connectors",))

        threading.Thread(target=_thread, daemon=True).start()

    def _delete_selected_connector(self):
        if self._connector_selected_id:
            hub_db.delete_connector(self._connector_selected_id)
            self._connector_selected_id = None
            self._refresh_connectors()
            self.show_toast("Connector deleted.", SUCCESS)

"""Admin page mixin — hub control, config, models, users, scheduler, logs."""
import json
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk
from pages.constants import *
import hub_db
from ah_logging import LOG_DIR

# Resolve v3/ directory and project root from this file's location (pages/admin_page.py)
HERE = Path(__file__).parent.parent          # app/v3/
APP_ROOT = HERE.parent.parent.parent.parent  # project root (app/v3 -> app -> agentharness -> .agents -> root)


class AdminPageMixin:
    def show_admin(self):
        if not self.admin_unlocked:
            self.ask_pin(self._unlock_admin)
            return
        self._render_admin()

    def _unlock_admin(self):
        self.admin_unlocked = True
        self._render_admin()

    def _render_admin(self):
        self._set_active_nav("Admin")
        self._clear_content()
        self._section_header(self.content, "Admin", "Protected controls, users, config, scheduler, and logs.")
        notebook = ttk.Notebook(self.content)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        hub_tab = tk.Frame(notebook, bg=BG_CANVAS)
        config_tab = tk.Frame(notebook, bg=BG_CANVAS)
        models_tab = tk.Frame(notebook, bg=BG_CANVAS)
        users_tab = tk.Frame(notebook, bg=BG_CANVAS)
        scheduler_tab = tk.Frame(notebook, bg=BG_CANVAS)
        logs_tab = tk.Frame(notebook, bg=BG_CANVAS)
        notebook.add(hub_tab, text="Hub Control")
        notebook.add(config_tab, text="Providers")
        notebook.add(models_tab, text="Models")
        notebook.add(users_tab, text="Users")
        notebook.add(scheduler_tab, text="Scheduler")
        notebook.add(logs_tab, text="Logs")

        self._build_admin_hub_tab(hub_tab)
        self._build_admin_config_tab(config_tab)
        self._build_admin_models_tab(models_tab)
        self._build_admin_users_tab(users_tab)
        self._build_admin_scheduler_tab(scheduler_tab)
        self._build_admin_logs_tab(logs_tab)

    def _build_admin_hub_tab(self, parent):
        card = self._card(parent, "Hub Control")
        card.pack(fill="both", expand=True, padx=10, pady=10)
        health = {}
        try:
            if hasattr(self.hub, "get_health"):
                health = self.hub.get_health() or {}
        except Exception:
            health = {}
        info = tk.Frame(card, bg=BG_PANEL)
        info.pack(fill="x", padx=14, pady=(0, 14))
        rows = [
            ("Status", "online" if getattr(self.hub, "online", False) else "offline"),
            ("Port", str(health.get("port", 8765))),
            ("PID", str(health.get("pid", "n/a"))),
            ("Mode", str(health.get("mode", "desktop"))),
        ]
        for idx, (label, value) in enumerate(rows):
            tk.Label(info, text=label, bg=BG_PANEL, fg=TEXT_MUTED).grid(row=idx, column=0, sticky="w", pady=4)
            tk.Label(info, text=value, bg=BG_PANEL, fg=TEXT_PRIMARY).grid(row=idx, column=1, sticky="w", pady=4, padx=(12, 0))
        buttons = tk.Frame(card, bg=BG_PANEL)
        buttons.pack(fill="x", padx=14, pady=(0, 14))
        self._button(buttons, "Start Hub", self._start_hub_server, accent=True).pack(side="left", padx=4)
        self._button(buttons, "Stop Hub", self._stop_hub_server).pack(side="left", padx=4)
        self._button(buttons, "Open Web Dashboard", lambda: webbrowser.open("http://localhost:8765")).pack(side="left", padx=4)

    def _build_admin_config_tab(self, parent):
        """
        Providers tab — two sections:
          1. Active LLM: which provider/model ArchonHub currently uses
          2. API Keys: per-provider key entry with obfuscation + show/hide toggle
        """
        config = hub_db.get_config()
        config = config if isinstance(config, dict) else {}
        ai_cfg = self._load_ai_config_file()

        PROVIDERS = ["openai", "anthropic", "ollama", "github", "groq", "gemini", "perplexity"]
        MODELS_BY_PROVIDER = {
            "openai":      ["gpt-4.1", "gpt-4o", "gpt-4o-mini", "o3", "o4-mini", "gpt-3.5-turbo"],
            "anthropic":   ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5", "claude-3-5-sonnet-20241022"],
            "ollama":      ["llama3.2", "llama3.1", "mistral", "phi3", "gemma2", "codellama", "qwen2.5-coder"],
            "github":      ["gpt-4o", "gpt-4o-mini", "Meta-Llama-3.1-70B-Instruct", "Mistral-large"],
            "groq":        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
            "gemini":      ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            "perplexity":  ["sonar-pro", "sonar", "sonar-reasoning-pro", "sonar-reasoning"],
        }
        BASE_URLS = {
            "openai":      "https://api.openai.com/v1",
            "anthropic":   "https://api.anthropic.com/v1",
            "ollama":      "http://localhost:11434/v1",
            "github":      "https://models.inference.ai.azure.com",
            "groq":        "https://api.groq.com/openai/v1",
            "gemini":      "",
            "perplexity":  "https://api.perplexity.ai",
        }
        PROV_ICONS = {
            "openai": "⬡", "anthropic": "◈", "gemini": "◉", "groq": "⚡",
            "perplexity": "◎", "github": "⌥", "ollama": "◆",
        }

        # ── Section 1: Active LLM ─────────────────────────────────────────────
        active_card = self._card(parent, "Active LLM")
        active_card.pack(fill="x", padx=10, pady=(10, 4))

        cur_provider = config.get("llm_provider") or ai_cfg.get("provider", "openai")
        cur_model    = config.get("llm_model")    or ai_cfg.get("model",    "gpt-4o-mini")
        cur_url      = config.get("llm_base_url") or ai_cfg.get("baseUrl",  "")

        self.admin_provider_var = tk.StringVar(value=cur_provider)
        self.admin_model_var    = tk.StringVar(value=cur_model)
        self.admin_url_var      = tk.StringVar(value=cur_url or BASE_URLS.get(cur_provider, ""))
        self.admin_threads_var  = tk.IntVar(value=int(config.get("thread_pool_size", 3) or 3))
        self.admin_key_var = tk.StringVar(value=config.get(f"llm_key_{cur_provider}") or
                                          config.get("llm_api_key") or ai_cfg.get("apiKey", ""))

        form = tk.Frame(active_card, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 14))
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        form.grid_columnconfigure(2, weight=1)

        tk.Label(form, text="Active Provider", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w", pady=4)
        tk.Label(form, text="Model",           bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=1, sticky="w", pady=4, padx=(8, 0))
        tk.Label(form, text="Thread Pool",     bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=2, sticky="w", pady=4, padx=(8, 0))

        self._combo(form, self.admin_provider_var, PROVIDERS).grid(row=1, column=0, sticky="ew")
        self.admin_model_combo = self._combo(form, self.admin_model_var, MODELS_BY_PROVIDER.get(cur_provider, []))
        self.admin_model_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        tk.Spinbox(form, from_=1, to=32, textvariable=self.admin_threads_var,
                   bg=BG_INPUT, fg=TEXT_PRIMARY, relief="flat", width=6).grid(row=1, column=2, sticky="ew", padx=(8, 0))

        tk.Label(form, text="Base URL (leave blank for default)", bg=BG_PANEL, fg=TEXT_BODY).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(6, 2))
        self._entry(form, self.admin_url_var).grid(row=3, column=0, columnspan=2, sticky="ew")

        btn_row = tk.Frame(form, bg=BG_PANEL)
        btn_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        self._button(btn_row, "Save Active LLM", self._save_admin_config, accent=True).pack(side="left", padx=4)
        self._button(btn_row, "Test Connection", self._test_llm_connection).pack(side="left", padx=4)

        def _on_provider_change(*_):
            p = self.admin_provider_var.get()
            models = MODELS_BY_PROVIDER.get(p, [])
            self.admin_model_combo["values"] = models
            if models and self.admin_model_var.get() not in models:
                self.admin_model_var.set(models[0])
            default_url = BASE_URLS.get(p, "")
            if default_url:
                self.admin_url_var.set(default_url)
            stored = hub_db.get_config(f"llm_key_{p}") or ""
            self.admin_key_var.set(stored)
        self.admin_provider_var.trace_add("write", _on_provider_change)

        # ── Section 2: API Keys (one row per provider) ────────────────────────
        keys_card = self._card(parent, "Provider API Keys")
        keys_card.pack(fill="x", padx=10, pady=(4, 10))

        desc = tk.Label(keys_card, text="Enter and save each provider's API key independently. Keys are stored encrypted in the hub database.",
                        bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9), wraplength=620, justify="left")
        desc.pack(anchor="w", padx=14, pady=(0, 10))

        self._prov_key_vars: dict[str, tk.StringVar] = {}
        self._prov_enabled_vars: dict[str, tk.BooleanVar] = {}

        for prov in PROVIDERS:
            stored_key     = hub_db.get_config(f"llm_key_{prov}") or ""
            stored_enabled = hub_db.get_config(f"llm_enabled_{prov}")
            is_enabled = (stored_enabled == "1") if stored_enabled is not None else bool(stored_key)

            key_var  = tk.StringVar(value=stored_key)
            enb_var  = tk.BooleanVar(value=is_enabled)
            self._prov_key_vars[prov]     = key_var
            self._prov_enabled_vars[prov] = enb_var

            row = tk.Frame(keys_card, bg=BG_PANEL)
            row.pack(fill="x", padx=14, pady=3)

            tk.Checkbutton(row, variable=enb_var, bg=BG_PANEL, activebackground=BG_PANEL,
                           selectcolor=BG_INPUT, cursor="hand2").pack(side="left")

            icon = PROV_ICONS.get(prov, "•")
            tk.Label(row, text=f"{icon} {prov.upper()}", bg=BG_PANEL, fg=TEXT_PRIMARY,
                     font=("Segoe UI", 9, "bold"), width=14, anchor="w").pack(side="left", padx=(2, 8))

            badge_txt = "● key set" if stored_key else "○ no key"
            badge_clr = SUCCESS if stored_key else TEXT_MUTED
            badge_lbl = tk.Label(row, text=badge_txt, bg=BG_PANEL, fg=badge_clr,
                                 font=("Segoe UI", 8), width=9)
            badge_lbl.pack(side="left", padx=(0, 8))

            entry = tk.Entry(row, textvariable=key_var, show="*", bg=BG_INPUT, fg=TEXT_PRIMARY,
                             insertbackground=TEXT_PRIMARY, relief="flat", font=("Segoe UI", 9))
            entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

            eye_state = {"show": False}
            def _toggle_eye(e=entry, s=eye_state):
                s["show"] = not s["show"]
                e.configure(show="" if s["show"] else "*")
            self._button(row, "👁", _toggle_eye).pack(side="left", padx=(0, 4))

            def _save_prov_key(p=prov, kv=key_var, ev=enb_var, bl=badge_lbl):
                k = kv.get().strip()
                hub_db.update_config({
                    f"llm_key_{p}": k,
                    f"llm_enabled_{p}": "1" if ev.get() else "0",
                })
                bl.configure(text="● key set" if k else "○ no key",
                             fg=SUCCESS if k else TEXT_MUTED)
                if self.admin_provider_var.get() == p:
                    self.admin_key_var.set(k)
                self._toast(f"{p.upper()} saved.", SUCCESS)
            self._button(row, "Save", _save_prov_key, accent=True).pack(side="left")

        # ── Section 3: Free LLM Keys ──────────────────────────────────────────
        free_card = self._card(parent, "🆓 Free Daily LLM Keys")
        free_card.pack(fill="x", padx=10, pady=(4, 10))

        free_desc = tk.Label(free_card,
            text="Automatically fetch and activate free daily API keys from the open key registry "
                 "(aiapiv2.pekpik.com). Supports Claude, Gemini, GPT-5.5, DeepSeek, Grok, Kimi and more. "
                 "Keys refresh daily — budget $14-$100 per key, expires in 24-48h.",
            bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9), wraplength=620, justify="left")
        free_desc.pack(anchor="w", padx=14, pady=(0, 8))

        free_status_var = tk.StringVar(value="Checking last sync...")
        free_status_lbl = tk.Label(free_card, textvariable=free_status_var,
                                   bg=BG_PANEL, fg=TEXT_BODY, font=("Segoe UI", 9))
        free_status_lbl.pack(anchor="w", padx=14, pady=(0, 6))

        def _load_free_status():
            try:
                resp = self.hub._get("/api/providers/free-keys-status") or {}
                last_sync = resp.get("last_sync") or "Never"
                active = resp.get("active_free_providers") or {}
                if active:
                    pnames = ", ".join(f"{p}({v.get('model','?').split('/')[-1]})" for p, v in active.items())
                    free_status_var.set(f"Last sync: {last_sync}  |  Active: {pnames}")
                else:
                    free_status_var.set(f"Last sync: {last_sync}  |  No free keys active yet")
            except Exception:
                free_status_var.set("Status unavailable — hub offline?")

        _load_free_status()

        def _run_free_key_sync():
            free_status_var.set("⏳ Syncing keys — fetching README & testing providers...")
            free_card.update_idletasks()

            def _do_sync():
                try:
                    resp = self.hub._request("POST", "/api/providers/sync-free-keys",
                                             data={}, timeout=180) or {}
                    synced = resp.get("synced") or {}
                    failed = resp.get("failed") or []
                    total  = resp.get("total_keys_found", 0)
                    if synced:
                        pnames = ", ".join(synced.keys())
                        msg = f"✅ Synced {len(synced)} providers: {pnames}"
                        self._ui_queue.put(("set_text", free_status_var, msg))
                        self._ui_queue.put(("call", lambda: self._toast(
                            f"Free keys activated: {pnames}", SUCCESS)))
                    else:
                        self._ui_queue.put(("set_text", free_status_var,
                            f"⚠ No working keys found ({total} keys checked, {len(failed)} providers tried)"))
                        self._ui_queue.put(("call", lambda: self._toast("No free keys available right now", WARNING)))
                except Exception as e:
                    self._ui_queue.put(("set_text", free_status_var, f"❌ Sync error: {e}"))
                    self._ui_queue.put(("call", lambda: self._toast(f"Sync failed: {e}", ERROR)))

            import threading
            threading.Thread(target=_do_sync, daemon=True).start()

        btn_row = tk.Frame(free_card, bg=BG_PANEL)
        btn_row.pack(anchor="w", padx=14, pady=(0, 10))
        self._button(btn_row, "🔄 Sync Free Keys Now", _run_free_key_sync, accent=True).pack(side="left", padx=(0, 8))
        self._button(btn_row, "↺ Refresh Status", _load_free_status).pack(side="left")

    def _build_admin_models_tab(self, parent):
        """
        Models multiselect tab — shows full model catalog grouped by provider.
        Checkboxes enable/disable each model. Saves via /api/models/toggle.
        """
        catalog = []
        providers_info = {}
        try:
            raw_catalog = self.hub._get("/api/models")
            if isinstance(raw_catalog, list):
                catalog = raw_catalog
            raw_prov = self.hub._get("/api/models/providers")
            if isinstance(raw_prov, list):
                providers_info = {p["provider"]: p for p in raw_prov}
        except Exception:
            try:
                import sys as _sys, os as _os
                _sys.path.insert(0, _os.path.dirname(__file__))
                from model_catalog import get_catalog as _mc_get
                catalog = _mc_get()
            except Exception:
                pass

        grouped: dict[str, list] = {}
        for m in catalog:
            grouped.setdefault(m["provider"], []).append(m)

        wrapper, canvas, inner = self._scrollable_area(parent, bg=BG_CANVAS)
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        def _bind_scroll(widget):
            widget.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        _bind_scroll(inner)

        self._model_vars: dict[str, tk.BooleanVar] = {}
        self._model_initial: dict[str, bool] = {}

        TIER_COLORS = {"premium": "#f59e0b", "standard": ACCENT, "economy": TEXT_MUTED, "local": SUCCESS}
        PROV_ICONS = {
            "openai": "⬡", "anthropic": "◈", "gemini": "◉", "groq": "⚡",
            "perplexity": "◎", "github": "⌥", "ollama": "◆",
        }

        for provider, models in grouped.items():
            pinfo = providers_info.get(provider, {})
            has_key = pinfo.get("key_configured", False)
            enabled_count = pinfo.get("enabled_models", sum(1 for m in models if m.get("enabled")))
            total_count = pinfo.get("total_models", len(models))

            prov_frame = tk.Frame(inner, bg=BG_PANEL, relief="flat", bd=0)
            prov_frame.pack(fill="x", padx=6, pady=(8, 2))
            _bind_scroll(prov_frame)

            icon = PROV_ICONS.get(provider, "•")
            key_badge = ("✓ key set" if has_key else "✗ no key")
            key_color = SUCCESS if has_key else ERROR
            hdr = tk.Frame(prov_frame, bg=BG_PANEL)
            hdr.pack(fill="x", padx=10, pady=6)
            tk.Label(hdr, text=f"{icon}  {provider.upper()}", bg=BG_PANEL,
                     fg=TEXT_PRIMARY, font=("Segoe UI", 11, "bold")).pack(side="left")
            tk.Label(hdr, text=key_badge, bg=BG_PANEL, fg=key_color,
                     font=("Segoe UI", 9)).pack(side="left", padx=(10, 0))
            tk.Label(hdr, text=f"{enabled_count}/{total_count} enabled", bg=BG_PANEL,
                     fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="right")

            tk.Frame(prov_frame, bg=BG_HOVER, height=1).pack(fill="x", padx=10)

            for m in models:
                key = m.get("key", f"{provider}__{m['model_id']}")
                enabled = bool(m.get("enabled", False))
                var = tk.BooleanVar(value=enabled)
                self._model_vars[key] = var
                self._model_initial[key] = enabled

                row = tk.Frame(prov_frame, bg=BG_PANEL)
                row.pack(fill="x", padx=10, pady=2)
                _bind_scroll(row)

                cb = tk.Checkbutton(row, variable=var, bg=BG_PANEL,
                                    activebackground=BG_PANEL, selectcolor=BG_INPUT,
                                    fg=TEXT_PRIMARY, cursor="hand2")
                cb.pack(side="left")

                tk.Label(row, text=m.get("display", m["model_id"]),
                         bg=BG_PANEL, fg=TEXT_PRIMARY,
                         font=("Segoe UI", 9), width=28, anchor="w").pack(side="left")

                ctx = m.get("context_k", "")
                if ctx:
                    tk.Label(row, text=f"{ctx}k", bg=BG_PANEL, fg=TEXT_MUTED,
                             font=("Segoe UI", 8), width=6).pack(side="left")

                tier = m.get("tier", "")
                tk.Label(row, text=tier, bg=BG_PANEL,
                         fg=TIER_COLORS.get(tier, TEXT_MUTED),
                         font=("Segoe UI", 8), width=8).pack(side="left")

                caps = m.get("capabilities", [])[:3]
                for cap in caps:
                    tk.Label(row, text=cap, bg=BG_HOVER, fg=TEXT_MUTED,
                             font=("Segoe UI", 7), padx=4, pady=1,
                             relief="flat").pack(side="left", padx=2)

        btn_bar = tk.Frame(parent, bg=BG_CANVAS)
        btn_bar.pack(fill="x", padx=10, pady=(4, 10))

        def _save_model_toggles():
            changed = {k: v.get() for k, v in self._model_vars.items()
                       if v.get() != self._model_initial.get(k)}
            if not changed:
                self._toast("No changes to save.", INFO)
                return
            errors = 0
            for key, enabled in changed.items():
                parts = key.split("__", 1)
                if len(parts) != 2:
                    continue
                prov, mid = parts
                try:
                    self.hub.put_json("/api/models/toggle",
                                      {"provider": prov, "model_id": mid, "enabled": enabled})
                    self._model_initial[key] = enabled
                except Exception:
                    try:
                        import sys as _sys, os as _os
                        _sys.path.insert(0, _os.path.dirname(__file__))
                        from model_catalog import set_model_enabled
                        set_model_enabled(prov, mid, enabled)
                        self._model_initial[key] = enabled
                    except Exception:
                        errors += 1
            saved = len(changed) - errors
            msg = f"Saved {saved} model change(s)."
            if errors:
                msg += f" {errors} failed."
            self._toast(msg, SUCCESS if not errors else WARNING)

        def _select_provider_all(select: bool):
            for k, v in self._model_vars.items():
                v.set(select)

        self._button(btn_bar, "Save Changes", _save_model_toggles, accent=True).pack(side="left", padx=4)
        self._button(btn_bar, "Enable All", lambda: _select_provider_all(True)).pack(side="left", padx=4)
        self._button(btn_bar, "Disable All", lambda: _select_provider_all(False)).pack(side="left", padx=4)
        tk.Label(btn_bar, text="Toggle models then click Save Changes",
                 bg=BG_CANVAS, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="left", padx=12)

    def _build_admin_users_tab(self, parent):
        card = self._card(parent, "Users")
        card.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("id", "username", "email", "role", "is_active", "last_login")
        self.users_tree = ttk.Treeview(card, columns=columns, show="headings", selectmode="browse")
        for column, text, width in (
            ("id", "ID", 60),
            ("username", "Username", 150),
            ("email", "Email", 220),
            ("role", "Role", 100),
            ("is_active", "Active", 80),
            ("last_login", "Last Login", 160),
        ):
            self.users_tree.heading(column, text=text)
            self.users_tree.column(column, width=width, anchor="w")
        self.users_tree.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.users_tree.bind("<<TreeviewSelect>>", lambda _e: self._set_selected_user())

        form = tk.Frame(card, bg=BG_PANEL)
        form.pack(fill="x", padx=14, pady=(0, 14))
        self.user_username_var = tk.StringVar()
        self.user_email_var = tk.StringVar()
        self.user_password_var = tk.StringVar()
        self.user_role_var = tk.StringVar(value="user")
        tk.Label(form, text="Username", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=0, sticky="w")
        self._entry(form, self.user_username_var).grid(row=1, column=0, sticky="ew")
        tk.Label(form, text="Email", bg=BG_PANEL, fg=TEXT_BODY).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self._entry(form, self.user_email_var).grid(row=1, column=1, sticky="ew", padx=(10, 0))
        tk.Label(form, text="Password", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=0, sticky="w", pady=4)
        self._entry(form, self.user_password_var, show="*").grid(row=3, column=0, sticky="ew")
        tk.Label(form, text="Role", bg=BG_PANEL, fg=TEXT_BODY).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=4)
        self._combo(form, self.user_role_var, ["user", "admin"]).grid(row=3, column=1, sticky="ew", padx=(10, 0))
        buttons = tk.Frame(form, bg=BG_PANEL)
        buttons.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self._button(buttons, "Add User", self._add_user, accent=True).pack(side="left", padx=4)
        self._button(buttons, "Delete Selected", self._delete_selected_user).pack(side="left", padx=4)
        form.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)
        self._refresh_users()

    def _build_admin_scheduler_tab(self, parent):
        self.admin_schedule_tree = ttk.Treeview(parent, columns=("id", "agent_id", "project", "schedule", "status"), show="headings")
        for column, text, width in (
            ("id", "ID", 180),
            ("agent_id", "Agent", 220),
            ("project", "Project", 120),
            ("schedule", "Schedule", 260),
            ("status", "Status", 100),
        ):
            self.admin_schedule_tree.heading(column, text=text)
            self.admin_schedule_tree.column(column, width=width, anchor="w")
        self.admin_schedule_tree.pack(fill="both", expand=True, padx=10, pady=10)
        for row in self._schedule_rows():
            self.admin_schedule_tree.insert("", "end", values=(row["id"], row["agent_id"], row["project"], row["schedule"], row["status"]))

    def _build_admin_logs_tab(self, parent):
        controls = tk.Frame(parent, bg=BG_CANVAS)
        controls.pack(fill="x", padx=10, pady=(10, 6))
        files = [path.name for path in LOG_DIR.glob("*.log")] if LOG_DIR.exists() else []
        if files and not self.log_file_var.get():
            self.log_file_var.set(files[0])
        self._combo(controls, self.log_file_var, files or [""]).pack(side="left", fill="x", expand=True)
        self._button(controls, "Refresh", self._refresh_logs, accent=True).pack(side="left", padx=6)
        self.logs_text = self._text_widget(parent, height=30)
        self.logs_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.logs_text.configure(state="disabled")
        self._refresh_logs()

    def _save_admin_config(self):
        prov = self.admin_provider_var.get()
        key  = self.admin_key_var.get().strip()
        cfg = {
            "llm_provider":    prov,
            "llm_model":       self.admin_model_var.get(),
            "llm_api_key":     key,
            "llm_base_url":    self.admin_url_var.get(),
            "thread_pool_size": int(self.admin_threads_var.get() or 3),
        }
        if key:
            cfg[f"llm_key_{prov}"] = key
            cfg[f"llm_enabled_{prov}"] = "1"
        hub_db.update_config(cfg)
        self._save_ai_config_file({
            "provider": cfg["llm_provider"],
            "model":    cfg["llm_model"],
            "apiKey":   cfg["llm_api_key"],
            "baseUrl":  cfg["llm_base_url"],
            "enabled":  True,
        })
        self.show_toast("Active LLM saved.", SUCCESS)

    def _test_llm_connection(self):
        import threading as _t
        self.show_toast("Testing connection… (30s timeout)", ACCENT)
        def _run():
            import concurrent.futures
            def _do_test():
                from hub_nodes import _llm
                llm = _llm()
                from langchain_core.messages import HumanMessage
                resp = llm.invoke([HumanMessage(content="Reply with exactly: OK")])
                return getattr(resp, "content", str(resp))[:80]
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_do_test)
                try:
                    text = future.result(timeout=30)
                    self._ui_queue.put(("toast", f"✅ Connected — {text}", SUCCESS))
                except concurrent.futures.TimeoutError:
                    self._ui_queue.put(("toast", "❌ Test timed out (30s) — provider may be slow or offline", ERROR))
                except Exception as exc:
                    self._ui_queue.put(("toast", f"❌ {exc}", ERROR))
        _t.Thread(target=_run, daemon=True).start()

    def _load_ai_config_file(self) -> dict:
        paths = [
            APP_ROOT / ".agents" / "data" / "ai_config.json",
            APP_ROOT / "projects" / "agentharness-v2" / "data" / "ai_config.json",
        ]
        for p in paths:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        return {}

    def _save_ai_config_file(self, data: dict):
        dest = APP_ROOT / ".agents" / "data" / "ai_config.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _refresh_users(self):
        rows = hub_db.list_users()
        self.users_tree.delete(*self.users_tree.get_children())
        self.users_lookup = {}
        for row in rows:
            self.users_lookup[str(row["id"])] = row
            self.users_tree.insert("", "end", iid=str(row["id"]), values=(row["id"], row["username"], row.get("email", ""), row.get("role", ""), row.get("is_active", ""), self._human_time(row.get("last_login"))))

    def _set_selected_user(self):
        selected = self.users_tree.selection()
        self.selected_user_id = selected[0] if selected else None

    def _add_user(self):
        if not self.user_username_var.get().strip() or not self.user_password_var.get().strip():
            self.show_toast("Username and password required.", WARNING)
            return
        try:
            hub_db.create_user(self.user_username_var.get().strip(), self.user_email_var.get().strip() or None, self.user_password_var.get(), self.user_role_var.get())
            self.user_username_var.set("")
            self.user_email_var.set("")
            self.user_password_var.set("")
            self.user_role_var.set("user")
            self._refresh_users()
            self.show_toast("User added.", SUCCESS)
        except Exception as exc:
            self.show_toast(f"Add user failed: {exc}", ERROR)

    def _delete_selected_user(self):
        if self.selected_user_id:
            hub_db.delete_user(int(self.selected_user_id))
            self.selected_user_id = None
            self._refresh_users()

    def _refresh_logs(self):
        selected = self.log_file_var.get()
        if not selected:
            self._set_text(self.logs_text, "No log files found.")
            return
        path = LOG_DIR / selected
        if not path.exists():
            self._set_text(self.logs_text, f"Log file not found: {selected}")
            return
        content = path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        self._set_text(self.logs_text, "\n".join(lines[-2000:]))

    def _start_hub_server(self):
        candidates = [
            HERE / "hub_server.py",
            APP_ROOT / "_archive" / "agentharness-v3-app" / "hub_server.py",
        ]
        server_path = next((path for path in candidates if path.exists()), None)
        if server_path is None:
            self.show_toast("Hub server script not found.", WARNING)
            return
        if self.hub_process and self.hub_process.poll() is None:
            self.show_toast("Hub server already running.", WARNING)
            return
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        self.hub_process = subprocess.Popen([sys.executable, str(server_path)], cwd=str(server_path.parent), creationflags=flags)
        self.show_toast("Hub server launch requested.", SUCCESS)

    def _stop_hub_server(self):
        if self.hub_process and self.hub_process.poll() is None:
            try:
                self.hub_process.terminate()
                self.show_toast("Hub server stop requested.", WARNING)
                return
            except Exception as exc:
                self.show_toast(f"Stop failed: {exc}", ERROR)
                return
        self.show_toast("No managed hub server process.", WARNING)

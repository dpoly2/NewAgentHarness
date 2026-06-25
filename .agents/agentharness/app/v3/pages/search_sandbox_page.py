"""Web search and code sandbox page mixins."""
import tkinter as tk
from tkinter import ttk
from pages.constants import *


class SearchSandboxPageMixin:
    def show_web_search(self):
        self._set_active_nav("Search")
        self._clear_content()
        self._section_header(self.content, "🔍 Web Search",
                             "Real-time Google search via SerpAPI. Set SERPAPI_API_KEY in .env.")

        top_row = tk.Frame(self.content, bg=BG_CANVAS)
        top_row.pack(fill="x", padx=20, pady=(0, 10))
        self._ws_query_var = tk.StringVar()
        entry = self._entry(top_row, self._ws_query_var)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        entry.insert(0, "Search the web…")
        entry.bind("<FocusIn>", lambda e: entry.delete(0, "end") if entry.get() == "Search the web…" else None)
        entry.bind("<Return>", lambda _: self._run_web_search())
        self._ws_limit_var = tk.StringVar(value="5")
        limit_cb = ttk.Combobox(top_row, textvariable=self._ws_limit_var,
                                values=["3", "5", "10"], width=4, state="readonly")
        limit_cb.pack(side="left", padx=(0, 8))
        self._button(top_row, "🔍 Search", self._run_web_search, accent=True).pack(side="left")

        card = self._card(self.content, "Results")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._ws_result_text = self._text_widget(card, height=30)
        self._ws_result_text.pack(fill="both", expand=True, padx=14, pady=14)
        self._ws_result_text.configure(state="disabled")
        self._ws_result_text.tag_configure("url", foreground=ACCENT)
        self._ws_result_text.tag_configure("title", foreground=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
        self._ws_result_text.tag_configure("muted", foreground=TEXT_MUTED)

    def _run_web_search(self):
        q = self._ws_query_var.get().strip()
        if not q or q == "Search the web…":
            self._toast("Enter a search query.", WARNING)
            return
        limit = int(getattr(self, "_ws_limit_var", tk.StringVar(value="5")).get() or "5")
        import threading as _t, urllib.parse

        self._toast("Searching…", ACCENT)

        def _run():
            try:
                data = self.hub._get(f"/api/search/web?q={urllib.parse.quote(q)}&limit={limit}") or {}
                if not data.get("success"):
                    detail = data.get("detail", str(data))
                    self._ui_queue.put(("set_text", self._ws_result_text,
                                        f"Search failed: {detail}\n\nMake sure SERPAPI_API_KEY is set in .agents/.env"))
                    return
                results = data.get("results", [])
                lines = [f"Query: \"{q}\"  ({len(results)} results)  —  {data.get('search_timestamp','')[:19]}", "─"*60, ""]
                for r in results:
                    lines.append(f"[{r['id']}] {r['title']}")
                    lines.append(f"    {r['url']}")
                    lines.append(f"    {r.get('snippet','')}")
                    if r.get("published_date"):
                        lines.append(f"    📅 {r['published_date']}")
                    lines.append("")
                self._ui_queue.put(("set_text", self._ws_result_text, "\n".join(lines)))
            except Exception as e:
                self._ui_queue.put(("toast", f"Search error: {e}", ERROR))
                self._ui_queue.put(("set_text", self._ws_result_text, f"Error: {e}"))

        _t.Thread(target=_run, daemon=True).start()

    def show_sandbox(self):
        self._set_active_nav("Sandbox")
        self._clear_content()
        self._section_header(self.content, "⚡ Code Sandbox",
                             "Execute Python code securely. stdout, stderr, and generated files returned.")

        # Top: status
        status_row = tk.Frame(self.content, bg=BG_CANVAS)
        status_row.pack(fill="x", padx=20, pady=(0, 8))
        self._sandbox_status_lbl = tk.Label(status_row, text="Checking sandbox…", bg=BG_CANVAS,
                                             fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._sandbox_status_lbl.pack(side="left")
        self._refresh_sandbox_status()

        paned = tk.PanedWindow(self.content, orient="vertical", bg=BG_CANVAS, sashwidth=4)
        paned.pack(fill="both", expand=True, padx=20, pady=(0, 4))

        # Input pane
        in_card = self._card(paned, "Code (Python)")
        paned.add(in_card, minsize=120)
        self._sandbox_code = self._text_widget(in_card, height=12, font=("Consolas", 10))
        self._sandbox_code.pack(fill="both", expand=True, padx=14, pady=(0, 4))
        self._sandbox_code.insert("1.0", "# Write Python code here\nprint('Hello from sandbox!')\n")

        run_row = tk.Frame(in_card, bg=BG_PANEL)
        run_row.pack(fill="x", padx=14, pady=(0, 8))
        self._button(run_row, "▶ Run", self._run_sandbox, accent=True).pack(side="left", padx=(0, 8))
        self._button(run_row, "✗ Clear Code", lambda: (self._sandbox_code.delete("1.0", "end"),
                                                        self._sandbox_code.insert("1.0", ""))).pack(side="left")
        self._sandbox_run_lbl = tk.Label(run_row, text="", bg=BG_PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self._sandbox_run_lbl.pack(side="left", padx=8)

        # Output pane
        out_card = self._card(paned, "Output")
        paned.add(out_card, minsize=80)
        self._sandbox_output = self._text_widget(out_card, height=8, font=("Consolas", 10))
        self._sandbox_output.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._sandbox_output.configure(state="disabled")

    def _refresh_sandbox_status(self):
        import threading as _t
        def _run():
            try:
                s = self.hub._get("/api/sandbox/status") or {}
                mode = s.get("mode", "unknown")
                lang = ", ".join(s.get("supported_languages", ["python"]))
                self._ui_queue.put(("configure", self._sandbox_status_lbl,
                                    {"text": f"Mode: {mode} | Languages: {lang}", "fg": SUCCESS}))
            except Exception:
                self._ui_queue.put(("configure", self._sandbox_status_lbl,
                                    {"text": "Sandbox offline or unavailable", "fg": ERROR}))
        _t.Thread(target=_run, daemon=True).start()

    def _run_sandbox(self):
        code = self._sandbox_code.get("1.0", "end").strip()
        if not code:
            self._toast("Enter some code first.", WARNING)
            return
        import threading as _t, time
        self._sandbox_run_lbl.configure(text="Running…", fg=ACCENT)
        self._sandbox_output.configure(state="normal")
        self._sandbox_output.delete("1.0", "end")
        self._sandbox_output.insert("end", "Running…\n")
        self._sandbox_output.configure(state="disabled")

        def _run():
            t0 = time.time()
            try:
                result = self.hub.post_json("/api/sandbox/execute", {"code": code, "language": "python"})
                elapsed = int((time.time() - t0) * 1000)
                if result:
                    stdout = result.get("stdout", "")
                    stderr = result.get("stderr", "")
                    error = result.get("error", "")
                    exit_code = result.get("exit_code", 0)
                    ms = result.get("execution_time_ms", elapsed)
                    blocked = result.get("blocked_reason", "")
                    parts = []
                    if blocked:
                        parts.append(f"BLOCKED: {blocked}")
                    if stdout:
                        parts.append(f"--- stdout ---\n{stdout}")
                    if stderr:
                        parts.append(f"--- stderr ---\n{stderr}")
                    if error:
                        parts.append(f"--- error ---\n{error}")
                    text = "\n".join(parts) if parts else "(no output)"
                    self._ui_queue.put(("set_text", self._sandbox_output, text))
                    color = SUCCESS if exit_code == 0 and not blocked else ERROR
                    self._ui_queue.put(("configure", self._sandbox_run_lbl,
                                        {"text": f"Exit {exit_code} | {ms}ms", "fg": color}))
                else:
                    self._ui_queue.put(("set_text", self._sandbox_output, "No response from sandbox."))
            except Exception as e:
                self._ui_queue.put(("set_text", self._sandbox_output, f"Error: {e}"))
                self._ui_queue.put(("configure", self._sandbox_run_lbl, {"text": "Error", "fg": ERROR}))

        _t.Thread(target=_run, daemon=True).start()

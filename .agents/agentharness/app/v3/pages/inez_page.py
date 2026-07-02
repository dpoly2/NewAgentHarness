"""Inez chat page mixin — all show_inez and _chat_* methods."""
import threading
import tkinter as tk
import uuid
from datetime import datetime
from tkinter import ttk
from pages.constants import *


class InezPageMixin:

    def show_inez(self):
        self._clear_content()
        self._set_active_nav("Inez")
        self._build_inez_chat_panel(self.content)
        self._refresh_inez_memory_sidebar()
        self._fetch_inez_status()

    def _refresh_inez_memory_sidebar(self):
        if not hasattr(self, "_inez_mem_listbox"):
            return
        try:
            data = self.hub._get("/api/memory/global") or []
            facts = data if isinstance(data, list) else data.get("facts", [])
            self._inez_mem_listbox.configure(state="normal")
            self._inez_mem_listbox.delete("1.0", "end")
            for f in facts[:15]:
                line = f"[{f.get('category', '')}] {f.get('subject', '')}: {str(f.get('value', ''))[:60]}\n"
                self._inez_mem_listbox.insert("end", line)
            self._inez_mem_listbox.configure(state="disabled")
        except Exception:
            pass

    def _inez_with_search_context(self, message):
        if not getattr(self, "_inez_web_search_var", None) or not self._inez_web_search_var.get():
            return message
        try:
            import urllib.parse as _urlparse

            data = self.hub._get(f"/api/search?q={_urlparse.quote(message)}")
            rows = data if isinstance(data, list) else data.get("results", []) if isinstance(data, dict) else []
            lines = []
            for item in rows[:5]:
                title = item.get("title") or item.get("source") or item.get("filename") or item.get("url") or "Result"
                snippet = item.get("snippet") or item.get("content") or item.get("text") or ""
                url = item.get("url", "")
                lines.append(f"- {title}")
                if snippet:
                    lines.append(f"  {str(snippet)[:240]}")
                if url:
                    lines.append(f"  {url}")
            if lines:
                return "Web search context:\n" + "\n".join(lines) + f"\n\nUser message:\n{message}"
        except Exception:
            pass
        return message

    def _inez_send(self):
        task = (self._chat_input.get("1.0", "end") or "").strip()
        if not task:
            return
        self._chat_input.delete("1.0", "end")

        ts = datetime.now().strftime("%H:%M")

        user_msg = {"role": "user", "content": task, "ts": ts}
        self._chat_messages.append(user_msg)
        self._chat_render_bubble(user_msg)
        self._inez_history.append({"role": "user", "content": task})

        think_run_id = "inez-think-" + str(uuid.uuid4())[:8]
        inez_think_msg = {
            "role": "inez_thinking",
            "content": "Inez is analyzing your request...",
            "run_id": think_run_id,
            "ts": ts,
        }
        self._chat_messages.append(inez_think_msg)
        self._chat_render_bubble(inez_think_msg)

        def _on_inez_result(result):
            """Called in background thread when Inez finishes thinking."""
            self._ui_queue.put(("inez_result", think_run_id, result))

        try:
            from hub_client import LLM_TIMEOUT as _HUB_LLM_TIMEOUT
        except Exception:
            _HUB_LLM_TIMEOUT = 180.0
        if getattr(self.hub, "online", False):
            def _hub_think():
                try:
                    send_task = self._inez_with_search_context(task)
                    resp = self.hub.post_json("/api/inez/chat", {
                        "message": send_task,
                        "conversation_id": self._inez_conv_id,
                    }, timeout=_HUB_LLM_TIMEOUT)
                    if resp and "inez_message" in resp:
                        # Legacy synchronous server: the full answer is in the body.
                        self._inez_conv_id = resp.get("conversation_id", self._inez_conv_id)
                        _on_inez_result(resp)
                    elif resp and resp.get("run_id"):
                        # Async server: 202 Accepted. The answer arrives later as an
                        # `inez_response` WebSocket event; map the server run_id to
                        # this bubble so _handle_inez_response can render it here.
                        self._inez_conv_id = resp.get("conversation_id", self._inez_conv_id)
                        self._inez_pending[resp["run_id"]] = think_run_id
                    else:
                        _on_inez_result({"inez_message": "Inez did not respond. Please try again.",
                                         "dispatches": [], "needs_agents": False, "error": "no response"})
                except Exception as exc:
                    _on_inez_result({"inez_message": str(exc), "dispatches": [], "needs_agents": False, "error": str(exc)})
            threading.Thread(target=_hub_think, daemon=True).start()
        else:
            try:
                from inez_agent import think_async
                send_task = self._inez_with_search_context(task)
                think_async(send_task, self._inez_history, _on_inez_result)
            except ImportError:
                self._ui_queue.put(("inez_result", think_run_id, {
                    "inez_message": "Inez agent module not available. Check that inez_agent.py is in the app/v3 folder.",
                    "dispatches": [],
                    "needs_agents": False,
                    "error": "ImportError",
                }))

    def _inez_handle_result(self, think_run_id, result):
        """Process Inez's decision on the main thread (called from _poll_queue)."""
        inez_message = result.get("inez_message", "")
        dispatches   = result.get("dispatches", [])
        ts = datetime.now().strftime("%H:%M")

        self._chat_run_frames.pop(think_run_id, None)
        self._chat_dot_state.pop(think_run_id, None)

        status_lbl = self._chat_run_status_label.pop(think_run_id, None)
        if status_lbl:
            try:
                status_lbl.configure(text="✓  Done", fg=SUCCESS)
            except Exception:
                pass

        if inez_message:
            inez_msg = {"role": "inez", "content": inez_message, "ts": ts}
            self._chat_messages.append(inez_msg)
            self._inez_history.append({"role": "inez", "content": inez_message})
            self._chat_render_bubble(inez_msg)

        for dispatch in dispatches:
            agent_id = dispatch.get("agent_id", "")
            project  = dispatch.get("project", "")
            graph    = dispatch.get("graph", "reflexion")
            task_txt = dispatch.get("task", "")
            if not agent_id or not task_txt:
                continue

            run_id = str(uuid.uuid4())
            deploy_msg = {
                "role": "thinking",
                "content": task_txt,
                "agent_id": agent_id,
                "project": project,
                "graph": graph,
                "run_id": run_id,
                "ts": ts,
            }
            self._chat_messages.append(deploy_msg)
            self._chat_render_bubble(deploy_msg)

            config = {
                "agent_id": agent_id, "project": project,
                "graph": graph, "task": task_txt,
                "max_revisions": 2, "run_id": run_id,
            }
            self._submit_chat_run(config, run_id)
            self._chat_dot_state[run_id] = 0
            self._chat_animate_dots(run_id)

    def _submit_chat_run(self, config, run_id):
        if getattr(self.hub, "online", False):
            try:
                self.hub.submit_run(
                    agent_id=config["agent_id"], project=config["project"],
                    graph=config["graph"], task=config["task"],
                    max_revisions=config.get("max_revisions", 2),
                )
                return
            except Exception:
                pass
        cancel_flag = threading.Event()
        self.cancel_flags[run_id] = cancel_flag

        def _thread():
            try:
                from hub_nodes import run_graph
                def emit(event_type, **kwargs):
                    self._ui_queue.put(("run_event", event_type, {"run_id": run_id, **kwargs}))
                run_graph({**config, "cancel_flag": cancel_flag}, emit=emit)
            except Exception as exc:
                self._ui_queue.put(("run_event", "run_failed",
                                    {"run_id": run_id, "error": str(exc)}))
        threading.Thread(target=_thread, daemon=True).start()

    def _chat_render_bubble(self, msg):
        if self._chat_bubbles_frame is None:
            return
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        ts      = msg.get("ts", "")
        run_id  = msg.get("run_id", "")

        outer = tk.Frame(self._chat_bubbles_frame, bg=BG_CANVAS)
        outer.pack(fill="x", padx=18, pady=6, anchor="e" if role == "user" else "w")

        if role == "user":
            self._chat_user_bubble(outer, content, ts)
        elif role == "thinking":
            self._chat_thinking_bubble(outer, msg)
        elif role == "inez_thinking":
            self._inez_thinking_bubble(outer, msg)
        elif role in ("agent", "inez"):
            self._chat_agent_bubble(outer, msg)

        self._chat_scroll_bottom()

    def _chat_user_bubble(self, parent, content, ts):
        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="e")
        bubble = tk.Frame(wrap, bg=ACCENT_DARK,
                          highlightbackground=ACCENT, highlightthickness=1)
        bubble.pack(anchor="e")
        tk.Label(bubble, text=content, bg=ACCENT_DARK, fg="#ffffff",
                 font=("Segoe UI", 11), wraplength=520, justify="left",
                 padx=14, pady=10).pack()
        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="e", padx=4)

    def _chat_thinking_bubble(self, parent, msg):
        agent_id = msg.get("agent_id", "agent")
        graph    = msg.get("graph", "reflexion")
        run_id   = msg.get("run_id", "")
        ts       = msg.get("ts", "")

        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="w", fill="x")

        av = tk.Canvas(wrap, width=32, height=32, bg=BG_CANVAS, highlightthickness=0)
        av.create_oval(4, 4, 28, 28, fill=ACCENT, outline="")
        av.create_text(16, 16, text="⚡", fill="white", font=("Segoe UI", 12))
        av.pack(side="left", anchor="nw", pady=4)

        bubble = tk.Frame(wrap, bg=BG_CARD,
                          highlightbackground=BORDER_CARD, highlightthickness=1)
        bubble.pack(side="left", anchor="nw", fill="x", expand=True, padx=6)

        hdr = tk.Frame(bubble, bg=BG_CARD)
        hdr.pack(fill="x", padx=12, pady=(10,4))
        tk.Label(hdr, text=f"⚡  Deploying  ", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Label(hdr, text=agent_id, bg=BG_CARD, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(hdr, text=f"  ·  {graph}", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)

        steps_frame = tk.Frame(bubble, bg=BG_CARD)
        steps_frame.pack(fill="x", padx=12, pady=6)
        self._chat_run_step_labels[run_id] = []

        nodes = GRAPH_LAYOUTS.get(graph, ["load_memory", "act", "evaluate", "save_memory"])
        for node in nodes:
            row = tk.Frame(steps_frame, bg=BG_CARD)
            row.pack(anchor="w", pady=1)
            dot = tk.Label(row, text="○", bg=BG_CARD, fg=TEXT_MUTED,
                           font=("Segoe UI", 10))
            dot.pack(side="left")
            lbl = tk.Label(row, text=f"  {node}", bg=BG_CARD, fg=TEXT_MUTED,
                           font=("Segoe UI Mono", 9))
            lbl.pack(side="left")
            self._chat_run_step_labels[run_id].append((node, dot, lbl))

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)

        status_lbl = tk.Label(bubble, text="● Thinking...", bg=BG_CARD, fg=ACCENT,
                              font=("Segoe UI", 9, "italic"), padx=12, pady=8)
        status_lbl.pack(anchor="w")
        self._chat_run_status_label[run_id] = status_lbl

        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=42)

        self._chat_run_frames[run_id] = (parent, wrap, bubble, steps_frame, status_lbl)

    def _inez_thinking_bubble(self, parent, msg):
        """Inez's own thinking bubble — purple themed."""
        run_id = msg.get("run_id", "")
        ts     = msg.get("ts", "")

        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="w", fill="x")

        av = tk.Canvas(wrap, width=32, height=32, bg=BG_CANVAS, highlightthickness=0)
        av.create_oval(4, 4, 28, 28, fill="#7c3aed", outline="")
        av.create_text(16, 16, text="👑", font=("Segoe UI", 12))
        av.pack(side="left", anchor="nw", pady=4)

        bubble = tk.Frame(wrap, bg=BG_CARD,
                          highlightbackground="#7c3aed", highlightthickness=1)
        bubble.pack(side="left", anchor="nw", fill="x", expand=True, padx=6)

        hdr = tk.Frame(bubble, bg=BG_CARD)
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(hdr, text="Inez", bg=BG_CARD, fg="#c4b5fd",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(hdr, text="  ·  analyzing request", bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(side="left")

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)

        status_lbl = tk.Label(bubble, text="● Thinking...", bg=BG_CARD, fg="#c4b5fd",
                              font=("Segoe UI", 9, "italic"), padx=12, pady=8)
        status_lbl.pack(anchor="w")
        self._chat_run_status_label[run_id] = status_lbl

        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=42)

        self._chat_run_frames[run_id] = (parent, wrap, bubble, None, status_lbl)
        self._chat_dot_state[run_id] = 0
        self._chat_animate_dots(run_id)

    def _chat_agent_bubble(self, parent, msg):
        agent_id = msg.get("agent_id", "agent")
        content  = msg.get("content", "")
        score    = msg.get("score", None)
        graph    = msg.get("graph", "")
        ts       = msg.get("ts", "")
        run_id   = msg.get("run_id", "")
        is_inez  = agent_id in ("inez", "inez-chief-of-staff") or msg.get("role") == "inez"

        wrap = tk.Frame(parent, bg=BG_CANVAS)
        wrap.pack(anchor="w", fill="x")

        av = tk.Canvas(wrap, width=32, height=32, bg=BG_CANVAS, highlightthickness=0)
        if is_inez:
            av.create_oval(4, 4, 28, 28, fill="#7c3aed", outline="")
            av.create_text(16, 16, text="👑", font=("Segoe UI", 12))
        else:
            av.create_oval(4, 4, 28, 28, fill=SUCCESS, outline="")
            av.create_text(16, 16, text="✓", fill="white", font=("Segoe UI", 12, "bold"))
        av.pack(side="left", anchor="nw", pady=4)

        border_color = "#7c3aed" if is_inez else SUCCESS
        bubble = tk.Frame(wrap, bg=BG_PANEL,
                          highlightbackground=border_color, highlightthickness=1)
        bubble.pack(side="left", anchor="nw", fill="x", expand=True, padx=6)

        hdr = tk.Frame(bubble, bg=BG_PANEL)
        hdr.pack(fill="x", padx=12, pady=(8, 4))
        name_color = "#c4b5fd" if is_inez else SUCCESS
        display_name = "Inez" if is_inez else agent_id
        tk.Label(hdr, text=display_name, bg=BG_PANEL, fg=name_color,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        if graph and not is_inez:
            tk.Label(hdr, text=f"  ·  {graph}", bg=BG_PANEL, fg=TEXT_MUTED,
                     font=("Segoe UI", 9)).pack(side="left")
        if score is not None and not is_inez:
            sc = float(score)
            sc_color = SUCCESS if sc >= 0.75 else WARNING if sc >= 0.5 else ERROR
            tk.Label(hdr, text=f"  ·  score {sc:.2f}", bg=BG_PANEL, fg=sc_color,
                     font=("Segoe UI", 9, "bold")).pack(side="left")

        tk.Frame(bubble, bg=DIVIDER, height=1).pack(fill="x", padx=12)
        tk.Label(bubble, text=content, bg=BG_PANEL, fg=TEXT_PRIMARY,
                 font=("Segoe UI", 11), wraplength=580, justify="left",
                 padx=14, pady=12, anchor="w").pack(fill="x")
        tk.Label(wrap, text=ts, bg=BG_CANVAS, fg=TEXT_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=42)

    def _chat_animate_dots(self, run_id):
        if run_id not in self._chat_run_status_label:
            return
        if run_id not in self._chat_run_frames:
            return
        lbl = self._chat_run_status_label.get(run_id)
        if lbl is None:
            return
        try:
            lbl.winfo_exists()
        except Exception:
            return
        if not lbl.winfo_exists():
            return
        tick = self._chat_dot_state.get(run_id, 0)
        dots = "●" * (tick % 3 + 1) + "○" * (2 - tick % 3)
        current_node = self.run_state.get(run_id, {}).get("current_node", "")
        node_text = f"  Running {current_node}..." if current_node else "  Thinking..."
        try:
            lbl.configure(text=f"{dots}{node_text}")
        except Exception:
            return
        self._chat_dot_state[run_id] = tick + 1
        self.root.after(400, lambda: self._chat_animate_dots(run_id))

    def _chat_handle_run_event(self, event_type, data, run_id):
        stamp = datetime.now().strftime("%H:%M:%S")

        if event_type == "node_update":
            node   = data.get("node", "")
            status = data.get("status", "")
            for (n, dot_lbl, name_lbl) in self._chat_run_step_labels.get(run_id, []):
                try:
                    if n == node:
                        if status == "running":
                            dot_lbl.configure(text="▶", fg=ACCENT)
                            name_lbl.configure(fg=ACCENT)
                        elif status in ("done", "complete"):
                            dot_lbl.configure(text="✓", fg=SUCCESS)
                            name_lbl.configure(fg=SUCCESS)
                    elif self._node_is_done(run_id, n, node):
                        dot_lbl.configure(text="✓", fg=SUCCESS)
                        name_lbl.configure(fg=TEXT_BODY)
                except Exception:
                    pass
            status_lbl = self._chat_run_status_label.get(run_id)
            if status_lbl:
                try:
                    status_lbl.configure(
                        text=f"▶  Running  {node}  ·  {stamp}",
                        fg=ACCENT
                    )
                except Exception:
                    pass

        elif event_type in ("run_completed", "run_failed"):
            is_fail = event_type == "run_failed"
            for (n, dot_lbl, name_lbl) in self._chat_run_step_labels.get(run_id, []):
                try:
                    cur_text = dot_lbl.cget("text")
                    if cur_text not in ("✓", "✗"):
                        if is_fail:
                            dot_lbl.configure(text="✗", fg=ERROR)
                            name_lbl.configure(fg=ERROR)
                        else:
                            dot_lbl.configure(text="✓", fg=SUCCESS)
                            name_lbl.configure(fg=SUCCESS)
                except Exception:
                    pass

            status_lbl = self._chat_run_status_label.get(run_id)
            if status_lbl:
                try:
                    if is_fail:
                        status_lbl.configure(text=f"✗  Failed  ·  {stamp}", fg=ERROR)
                    else:
                        score = float(data.get("score", 0) or 0)
                        status_lbl.configure(
                            text=f"✓  Complete  ·  score {score:.2f}  ·  {stamp}",
                            fg=SUCCESS
                        )
                except Exception:
                    pass

            self._chat_run_frames.pop(run_id, None)
            self._chat_dot_state.pop(run_id, None)

            if not is_fail:
                output = data.get("output", "") or self._get_run_output(run_id)
                if output:
                    think_msg = next(
                        (m for m in self._chat_messages
                         if m.get("run_id") == run_id and m.get("role") == "thinking"),
                        {}
                    )
                    agent_msg = {
                        "role": "agent",
                        "content": output,
                        "agent_id": think_msg.get("agent_id", "agent"),
                        "graph": think_msg.get("graph", ""),
                        "score": data.get("score"),
                        "run_id": run_id,
                        "ts": datetime.now().strftime("%H:%M"),
                    }
                    self._chat_messages.append(agent_msg)
                    if self.current_view in ("Chat", "Inez") and self._chat_bubbles_frame:
                        outer = tk.Frame(self._chat_bubbles_frame, bg=BG_CANVAS)
                        outer.pack(fill="x", padx=18, pady=6, anchor="w")
                        self._chat_agent_bubble(outer, agent_msg)
                        self._chat_scroll_bottom()

            self._chat_run_step_labels.pop(run_id, None)
            self._chat_run_status_label.pop(run_id, None)

    def _node_is_done(self, run_id, node, current_node):
        """Return True if node comes before current_node in the graph layout."""
        run_msg = next(
            (m for m in self._chat_messages
             if m.get("run_id") == run_id and m.get("role") == "thinking"), {}
        )
        graph = run_msg.get("graph", "reflexion")
        layout = GRAPH_LAYOUTS.get(graph, [])
        try:
            return layout.index(node) < layout.index(current_node)
        except ValueError:
            return False

    def _get_run_output(self, run_id):
        try:
            import hub_db
            runs = hub_db.load_runs(limit=1, agent_id=None, project=None, status=None)
            for r in runs:
                if r.get("run_id") == run_id:
                    return r.get("output", "")
        except Exception:
            pass
        return ""

    def _chat_scroll_bottom(self):
        try:
            if self._chat_canvas:
                self._chat_canvas.update_idletasks()
                self._chat_canvas.yview_moveto(1.0)
        except Exception:
            pass

"""
AgentHarness Hub — Desktop Client
hub_client.py

HubClient: connects the desktop app (main_m365.py) to the Hub server.

- Tries to connect to ws://localhost:8765/ws on startup
- If Hub is online  → routes runs, todos, notifications, briefing through Hub
- If Hub is offline → app falls back to current embedded execution (no features lost)
- Reconnects automatically every 30 seconds
- Broadcasts WebSocket events to registered callbacks (UI updates in real time)
- All HTTP calls via httpx (sync wrapper — called from threads, safe for Tkinter)
"""

from __future__ import annotations

import json
import queue
import threading
import time
from typing import Callable, Dict, List, Optional

HUB_BASE  = "http://localhost:8765"
HUB_WS    = "ws://localhost:8765/ws"
TIMEOUT   = 5.0          # HTTP request timeout (seconds)
RECONNECT = 30           # seconds between reconnect attempts when offline


# ── Optional imports (gracefully degrade if not installed) ───────────────────
try:
    import httpx
    HTTPX_OK = True
except ImportError:
    HTTPX_OK = False

try:
    import websockets
    import asyncio
    WS_OK = True
except ImportError:
    WS_OK = False


# ════════════════════════════════════════════════════════════════════════════════
class HubClient:
    """
    Singleton-style client. Create one instance in AgentHarnessM365.__init__,
    then call hub.start() to begin background connection attempts.

    Usage:
        self.hub = HubClient(on_event=self._on_hub_event)
        self.hub.start()

        # Submit a run
        job = self.hub.submit_run(agent_id, project, task, graph, max_rev)
        # job is None if Hub offline → caller falls back to embedded mode

        # Check status
        if self.hub.online:
            ...
    """

    def __init__(self, on_event: Callable[[dict], None] = None):
        self.online       = False
        self._on_event    = on_event or (lambda e: None)
        self._ws_thread   = None
        self._http        = httpx.Client(base_url=HUB_BASE, timeout=TIMEOUT) if HTTPX_OK else None
        self._stop        = threading.Event()
        self._event_queue = queue.Queue()   # events from WS → main thread drains this

    # ── Public: start background connection ───────────────────────────────────
    def start(self):
        """Start the WebSocket listener + reconnect loop in a daemon thread."""
        if not HTTPX_OK or not WS_OK:
            return   # silently skip — app runs in offline/fallback mode
        t = threading.Thread(target=self._connection_loop, daemon=True, name="HubWSClient")
        t.start()
        self._ws_thread = t

    def stop(self):
        self._stop.set()
        if self._http:
            try: self._http.close()
            except Exception: pass

    # ── Public: event polling (call from Tkinter .after loop) ────────────────
    def poll_events(self) -> List[dict]:
        """Drain the event queue — call from Tkinter .after() every 100ms."""
        events = []
        while True:
            try:
                events.append(self._event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    # ── Internal: WebSocket reconnect loop ────────────────────────────────────
    def _connection_loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while not self._stop.is_set():
            try:
                loop.run_until_complete(self._ws_listen())
            except Exception:
                pass
            if not self._stop.is_set():
                self._set_online(False)
                time.sleep(RECONNECT)

    async def _ws_listen(self):
        import websockets.exceptions
        try:
            async with websockets.connect(HUB_WS, ping_interval=30, ping_timeout=10, open_timeout=5) as ws:
                self._set_online(True)
                while not self._stop.is_set():
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=35.0)
                        event = json.loads(raw)
                        self._event_queue.put(event)
                    except asyncio.TimeoutError:
                        await ws.pong()
                    except Exception:
                        break
        except (ConnectionRefusedError, OSError,
                websockets.exceptions.WebSocketException):
            pass

    def _set_online(self, state: bool):
        changed = (self.online != state)
        self.online = state
        if changed:
            self._event_queue.put({"type": "hub_status", "online": state})

    # ── Health check (sync) ───────────────────────────────────────────────────
    def health(self) -> Optional[dict]:
        return self._get("/api/health")

    # ── Run submission ────────────────────────────────────────────────────────
    def submit_run(self, agent_id: str, project: str, task: str,
                   graph: str = "reflexion", max_revisions: int = 2,
                   priority: str = "normal") -> Optional[dict]:
        """
        Submit an agent run to the Hub.
        Returns { job_id, status, position } or None if Hub is offline.
        """
        if not self.online:
            return None
        return self._post("/api/run/submit", {
            "agent_id":      agent_id,
            "project":       project,
            "task":          task,
            "graph":         graph,
            "max_revisions": max_revisions,
            "priority":      priority,
        })

    def cancel_run(self, job_id: str) -> bool:
        r = self._delete(f"/api/run/{job_id}")
        return r is not None

    def get_run(self, job_id: str) -> Optional[dict]:
        return self._get(f"/api/run/{job_id}")

    def list_runs(self, status=None, agent_id=None, project=None,
                  limit=50, skip=0) -> List[dict]:
        params = {"limit": limit, "skip": skip}
        if status:   params["status"]   = status
        if agent_id: params["agent_id"] = agent_id
        if project:  params["project"]  = project
        return self._get("/api/runs", params=params) or []

    def run_stats(self) -> dict:
        return self._get("/api/runs/stats") or {}

    def queue_jobs(self) -> List[dict]:
        return self._get("/api/queue/jobs") or []

    def pause_queue(self): self._post("/api/queue/pause", {})
    def resume_queue(self): self._post("/api/queue/resume", {})

    # ── Briefing ──────────────────────────────────────────────────────────────
    def get_briefing(self) -> Optional[dict]:
        return self._get("/api/runs/briefing")

    # ── Todos ─────────────────────────────────────────────────────────────────
    def list_todos(self, status=None, priority=None) -> List[dict]:
        params = {}
        if status:   params["status"]   = status
        if priority: params["priority"] = priority
        return self._get("/api/todos", params=params) or []

    def create_todo(self, title: str, priority: str = "medium",
                    project: str = None, due_date: str = None) -> Optional[dict]:
        return self._post("/api/todos", {
            "title": title, "priority": priority,
            "project": project, "due_date": due_date,
        })

    def update_todo(self, todo_id: str, **kwargs) -> Optional[dict]:
        return self._patch(f"/api/todos/{todo_id}", kwargs)

    def delete_todo(self, todo_id: str) -> bool:
        return self._delete(f"/api/todos/{todo_id}") is not None

    # ── Notifications ─────────────────────────────────────────────────────────
    def list_notifications(self, limit=100) -> List[dict]:
        return self._get("/api/notifications", params={"limit": limit}) or []

    def push_notification(self, text: str, color: str = "#60a5fa",
                          category: str = "system"):
        self._post("/api/notifications/push", {"text": text, "color": color, "category": category})

    def clear_notifications(self):
        self._delete("/api/notifications")

    # ── Skills ────────────────────────────────────────────────────────────────
    def get_skill(self, agent_id: str) -> Optional[dict]:
        return self._get(f"/api/skills/{agent_id}")

    def update_skill(self, agent_id: str, content: str, version: int):
        return self._put(f"/api/skills/{agent_id}", {"content": content, "version": version})

    def list_skills(self) -> List[dict]:
        return self._get("/api/skills") or []

    # ── Scheduler ─────────────────────────────────────────────────────────────
    def list_scheduler_jobs(self) -> List[dict]:
        return self._get("/api/scheduler/jobs") or []

    def add_scheduled_job(self, agent_id: str, task: str, run_type: str,
                          **kwargs) -> Optional[dict]:
        return self._post("/api/scheduler/add", {
            "agent_id": agent_id, "task": task, "run_type": run_type, **kwargs
        })

    def cancel_scheduled_job(self, job_id: str) -> bool:
        return self._delete(f"/api/scheduler/{job_id}") is not None

    # ── Config ────────────────────────────────────────────────────────────────
    def get_config(self) -> dict:
        return self._get("/api/config") or {}

    def update_config(self, **kwargs) -> dict:
        return self._patch("/api/config", kwargs) or {}

    # ── HTTP helpers ──────────────────────────────────────────────────────────
    def _get(self, path: str, params: dict = None) -> Optional[dict | list]:
        if not self._http: return None
        try:
            r = self._http.get(path, params=params)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _post(self, path: str, data: dict) -> Optional[dict]:
        if not self._http: return None
        try:
            r = self._http.post(path, json=data)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _patch(self, path: str, data: dict) -> Optional[dict]:
        if not self._http: return None
        try:
            r = self._http.patch(path, json=data)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _put(self, path: str, data: dict) -> Optional[dict]:
        if not self._http: return None
        try:
            r = self._http.put(path, json=data)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _delete(self, path: str) -> Optional[dict]:
        if not self._http: return None
        try:
            r = self._http.delete(path)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

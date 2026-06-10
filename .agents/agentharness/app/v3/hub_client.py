"""
hub_client.py — ArchonHub Desktop↔Hub connector
Gracefully degrades to offline mode when Hub is not running.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import threading
import time
from typing import Any

try:
    import httpx  # type: ignore
except ImportError:
    httpx = None

try:
    import requests  # type: ignore
except ImportError:
    requests = None

try:
    import websockets  # type: ignore
except ImportError:
    websockets = None

try:
    from ah_logging import logger  # type: ignore
except ImportError:
    logger = logging.getLogger(__name__)


HUB_BASE = "http://localhost:8765"
HUB_WS = "ws://localhost:8765/ws"
TIMEOUT = 5.0
RECONNECT_INTERVAL = 5   # seconds


class HubClient:
    def __init__(self):
        self.online: bool = False
        self.token: str = ""
        self.username: str = os.getenv("ARCHONHUB_USER", "admin")
        self.password: str = os.getenv("ARCHONHUB_PASSWORD", "ArchonHub2024!")
        self._event_queue = queue.Queue()
        self._ws_thread: threading.Thread | None = None
        self._running = False
        self._reconnect_interval = RECONNECT_INTERVAL

    def start(self):
        if self._running:
            return
        self._running = True
        self._ws_thread = threading.Thread(target=self._ws_loop, daemon=True, name="ArchonHubClient")
        self._ws_thread.start()

    def stop(self):
        self._running = False
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=self._reconnect_interval + 1)

    def poll_events(self) -> list:
        events: list = []
        while True:
            try:
                events.append(self._event_queue.get_nowait())
            except queue.Empty:
                break
        return events

    def _set_online(self, state: bool):
        changed = self.online != state
        self.online = state
        if not state:
            self.token = ""
        if changed:
            self._event_queue.put({"type": "hub_status", "online": state})

    def _sleep_or_stop(self, seconds: float):
        deadline = time.time() + seconds
        while self._running and time.time() < deadline:
            time.sleep(min(0.25, max(0.0, deadline - time.time())))

    def _login(self) -> bool:
        if httpx is None and requests is None:
            logger.warning("ArchonHub offline: neither httpx nor requests is available.")
            self._set_online(False)
            return False

        payload = {"username": self.username, "password": self.password}
        try:
            if httpx is not None:
                response = httpx.post(f"{HUB_BASE}/api/auth/login", json=payload, timeout=TIMEOUT)
                response.raise_for_status()
                data = response.json()
            else:
                response = requests.post(f"{HUB_BASE}/api/auth/login", json=payload, timeout=TIMEOUT)
                response.raise_for_status()
                data = response.json()
            token = (data or {}).get("access_token") or (data or {}).get("token") or ""
            if not token:
                logger.warning("ArchonHub login failed: no token returned.")
                self._set_online(False)
                return False
            self.token = token
            self._set_online(True)
            return True
        except Exception as exc:
            logger.debug("ArchonHub login failed: %s", exc)
            self._set_online(False)
            return False

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _public_get(self, path: str) -> dict | None:
        try:
            if httpx is not None:
                response = httpx.get(f"{HUB_BASE}{path}", timeout=TIMEOUT)
                response.raise_for_status()
                return response.json()
            elif requests is not None:
                response = requests.get(f"{HUB_BASE}{path}", timeout=TIMEOUT)
                response.raise_for_status()
                return response.json()
            else:
                return None
        except Exception as exc:
            logger.debug("ArchonHub public GET %s failed: %s", path, exc)
            return None

    def _health_check(self) -> bool:
        data = self._public_get("/api/health")
        if data is not None:
            self._set_online(True)
            return True
        self._set_online(False)
        return False

    async def _ws_connect_once(self):
        assert websockets is not None
        async with websockets.connect(HUB_WS, open_timeout=TIMEOUT, ping_interval=20, ping_timeout=20) as ws:
            await ws.send(json.dumps({"type": "auth", "token": self.token}))
            self._set_online(True)
            while self._running:
                raw = await ws.recv()
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="replace")
                try:
                    event = json.loads(raw)
                except Exception:
                    event = {"type": "message", "raw": raw}
                self._event_queue.put(event)

    def _ws_loop(self):
        while self._running:
            try:
                if not self._login():
                    self._sleep_or_stop(self._reconnect_interval)
                    continue

                if websockets is None:
                    while self._running:
                        self._health_check()
                        self._sleep_or_stop(self._reconnect_interval)
                    break

                asyncio.run(self._ws_connect_once())
            except Exception as exc:
                logger.debug("ArchonHub websocket loop error: %s", exc)
            self._set_online(False)
            if self._running:
                self._sleep_or_stop(self._reconnect_interval)

    def _request(self, method: str, path: str, *, data: dict | None = None, params: dict | None = None) -> Any | None:
        if not self.online or not self.token:
            return None
        try:
            url = f"{HUB_BASE}{path}"
            headers = self._headers()
            params = {key: value for key, value in (params or {}).items() if value is not None}
            if httpx is not None:
                response = httpx.request(method, url, headers=headers, json=data, params=params, timeout=TIMEOUT)
            elif requests is not None:
                response = requests.request(method, url, headers=headers, json=data, params=params, timeout=TIMEOUT)
            else:
                return None
            response.raise_for_status()
            if response.content:
                return response.json()
            return {}
        except Exception as exc:
            logger.debug("ArchonHub %s %s failed: %s", method, path, exc)
            self._set_online(False)
            return None

    def _get(self, path, **params) -> dict | list | None:
        return self._request("GET", path, params=params or None)

    def _post(self, path, data=None) -> dict | None:
        result = self._request("POST", path, data=data)
        return result if isinstance(result, dict) else None

    def post_json(self, path, data=None) -> dict | None:
        """Public alias for _post — used by desktop UI for arbitrary POST calls."""
        return self._post(path, data)

    def _put(self, path, data=None) -> dict | None:
        result = self._request("PUT", path, data=data)
        return result if isinstance(result, dict) else None

    def _delete(self, path) -> bool:
        return self._request("DELETE", path) is not None

    def submit_run(self, agent_id, project, graph, task, max_revisions=2, priority="normal") -> dict | None:
        return self._post(
            "/api/run/submit",
            {
                "agent_id": agent_id,
                "project": project,
                "graph": graph,
                "task": task,
                "max_revisions": max_revisions,
                "priority": priority,
            },
        )

    def list_runs(self, limit=50, agent_id=None, project=None, status=None) -> list:
        return self._get("/api/runs", limit=limit, agent_id=agent_id, project=project, status=status) or []

    def cancel_run(self, run_id) -> bool:
        return self._delete(f"/api/run/{run_id}")

    def run_stats(self) -> dict | None:
        return self._get("/api/runs/stats")

    def queue_jobs(self) -> list:
        return self._get("/api/queue/jobs") or []

    def pause_queue(self) -> bool:
        return self._post("/api/queue/pause", {}) is not None

    def resume_queue(self) -> bool:
        return self._post("/api/queue/resume", {}) is not None

    def list_todos(self, status=None, project=None) -> list:
        return self._get("/api/todos", status=status, project=project) or []

    def create_todo(self, title, description="", priority="medium", project="", due_date="", tags=None) -> dict | None:
        return self._post(
            "/api/todos",
            {
                "title": title,
                "description": description,
                "priority": priority,
                "project": project,
                "due_date": due_date,
                "tags": tags or [],
            },
        )

    def update_todo(self, id, **kwargs) -> dict | None:
        return self._put(f"/api/todos/{id}", kwargs)

    def delete_todo(self, id) -> bool:
        return self._delete(f"/api/todos/{id}")

    def list_trips(self) -> list:
        return self._get("/api/trips") or []

    def create_trip(self, name, destination, depart_date="", return_date="", status="planning", budget=0, notes="") -> dict | None:
        return self._post(
            "/api/trips",
            {
                "name": name,
                "destination": destination,
                "depart_date": depart_date,
                "return_date": return_date,
                "status": status,
                "budget": budget,
                "notes": notes,
            },
        )

    def update_trip(self, id, **kwargs) -> dict | None:
        return self._put(f"/api/trips/{id}", kwargs)

    def delete_trip(self, id) -> bool:
        return self._delete(f"/api/trips/{id}")

    def list_connectors(self) -> list:
        return self._get("/api/connectors") or []

    def create_connector(self, data: dict) -> dict | None:
        return self._post("/api/connectors", data)

    def update_connector(self, id, **kwargs) -> dict | None:
        return self._put(f"/api/connectors/{id}", kwargs)

    def delete_connector(self, id) -> bool:
        return self._delete(f"/api/connectors/{id}")

    def test_connector(self, id) -> dict | None:
        return self._post(f"/api/connectors/{id}/test", {})

    def list_notifications(self, unread_only=False) -> list:
        return self._get("/api/notifications", unread_only=unread_only) or []

    def clear_notifications(self) -> None:
        self._delete("/api/notifications")

    def list_scheduler_jobs(self) -> list:
        return self._get("/api/scheduler/jobs") or []

    def trigger_job(self, id) -> bool:
        return self._post(f"/api/scheduler/jobs/{id}/trigger", {}) is not None

    def get_briefing(self) -> dict | None:
        result = self._get("/api/runs/briefing")
        return result if isinstance(result, dict) else None

    def get_config(self) -> dict | None:
        result = self._get("/api/config")
        return result if isinstance(result, dict) else None

    def update_config(self, data: dict) -> bool:
        return self._put("/api/config", data) is not None

    def list_projects(self) -> list:
        return self._get("/api/projects") or []

    def create_project(self, data: dict) -> dict | None:
        return self._post("/api/projects", data)

    def list_clients(self) -> list:
        return self._get("/api/clients") or []

    def create_client(self, data: dict) -> dict | None:
        return self._post("/api/clients", data)

    def get_health(self) -> dict | None:
        return self._public_get("/api/health")

    def list_users(self) -> list:
        return self._get("/api/users") or []

    def list_conversations(self) -> list:
        return self._get("/api/conversations") or []

    def create_conversation(self, title, slug="global") -> dict | None:
        return self._post("/api/conversations", {"title": title, "slug": slug})

    def list_messages(self, conversation_id) -> list:
        return self._get(f"/api/conversations/{conversation_id}/messages") or []

    def send_message(self, conversation_id, role, content, agent_id="") -> dict | None:
        return self._post(
            f"/api/conversations/{conversation_id}/messages",
            {"role": role, "content": content, "agent_id": agent_id},
        )

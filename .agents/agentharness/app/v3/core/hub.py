from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from core.database import _create_record, _now_iso, _queue_job_record, _save_run_record, _update_job_record, _utcnow

try:
    from hub_nodes import run_graph, LANGGRAPH_OK
except ImportError:
    LANGGRAPH_OK = False

    def run_graph(*args: Any, **kwargs: Any) -> dict:
        raise RuntimeError('hub_nodes is not available')

try:
    from hub_scheduler import build_scheduler
except ImportError:
    class _NullScheduler:
        def start(self) -> None:
            return None

        def shutdown(self, wait: bool = False) -> None:
            return None

        def get_jobs(self) -> list:
            return []

        def add_job(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError('hub_scheduler is not available')

        def remove_job(self, *args: Any, **kwargs: Any) -> None:
            return None

        def get_job(self, *args: Any, **kwargs: Any) -> Any:
            return None

    def build_scheduler(_hub: Any) -> _NullScheduler:
        return _NullScheduler()

try:
    from ah_logging import get_logger
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')

    def get_logger(name: str):
        return logging.getLogger(f'archonhub.{name}')

class HubServer:
    def __init__(self):
        self.start_time = _utcnow()
        self._queue: asyncio.Queue | None = None
        self._active_runs: dict[str, threading.Event] = {}
        self._clients: set[Any] = set()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._scheduler = None
        self._queue_paused = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_task: asyncio.Task | None = None
        self.logger = get_logger("server")

    async def submit_job(self, config: dict) -> str:
        run_id = config.get("run_id") or uuid.uuid4().hex
        payload = dict(config)
        payload["run_id"] = run_id
        payload.setdefault("graph", "reflexion")
        payload.setdefault("max_revisions", 2)
        payload.setdefault("priority", "normal")
        _queue_job_record(payload)
        if self._queue is None:
            raise RuntimeError("Hub queue is not initialized")
        await self._queue.put(payload)
        await self.broadcast(
            {
                "type": "run_queued",
                "run_id": run_id,
                "agent_id": payload.get("agent_id"),
                "project": payload.get("project"),
                "graph": payload.get("graph"),
                "queue_depth": self._queue.qsize(),
            }
        )
        return run_id

    async def broadcast(self, event: dict) -> None:
        dead_clients: list[Any] = []
        for client in list(self._clients):
            try:
                await client.send_json(event)
            except Exception:
                dead_clients.append(client)
        for client in dead_clients:
            self._clients.discard(client)
        if event.get("type") == "notif":
            _create_record(
                "notifications",
                {
                    "text": event.get("text", ""),
                    "color": event.get("color", ""),
                    "category": event.get("category", "system"),
                    "created_at": _now_iso(),
                    "read": 0,
                },
            )

    async def _worker_loop(self) -> None:
        self._loop = asyncio.get_running_loop()
        while True:
            if self._queue_paused:
                await asyncio.sleep(0.25)
                continue
            if self._queue is None:
                await asyncio.sleep(0.25)
                continue
            config = await self._queue.get()
            run_id = config["run_id"]
            cancel_flag = threading.Event()
            self._active_runs[run_id] = cancel_flag
            _update_job_record(run_id, "running")
            await self.broadcast(
                {
                    "type": "run_started",
                    "run_id": run_id,
                    "agent_id": config.get("agent_id"),
                    "project": config.get("project"),
                    "graph": config.get("graph", "reflexion"),
                }
            )
            try:
                loop = asyncio.get_running_loop()

                def _execute() -> dict:
                    payload = dict(config)
                    payload["cancel_flag"] = cancel_flag
                    return run_graph(payload, emit=make_emit(run_id))

                result = await loop.run_in_executor(self._executor, _execute)
                final_status = "cancelled" if cancel_flag.is_set() else str(result.get("status") or "completed")
                save_payload = {
                    "run_id": run_id,
                    "agent_id": config.get("agent_id"),
                    "project": config.get("project"),
                    "graph": config.get("graph", "reflexion"),
                    "task": config.get("task", ""),
                    "score": result.get("score"),
                    "critique": result.get("critique"),
                    "revision_count": result.get("revision_count", 0),
                    "output": result.get("output", ""),
                    "skill_version": result.get("skill_version", 1),
                    "status": final_status,
                }
                _save_run_record(save_payload)
                _update_job_record(run_id, final_status, {"job_data": {**config, "result": result}})
                await self.broadcast(
                    {
                        "type": "run_cancelled" if final_status == "cancelled" else "run_completed",
                        "run_id": run_id,
                        "agent_id": config.get("agent_id"),
                        "project": config.get("project"),
                        "status": final_status,
                        "score": result.get("score"),
                    }
                )
            except Exception as exc:
                self.logger.exception("Run failed: %s", run_id)
                _update_job_record(run_id, "failed", {"job_data": {**config, "error": str(exc)}})
                _save_run_record(
                    {
                        "run_id": run_id,
                        "agent_id": config.get("agent_id"),
                        "project": config.get("project"),
                        "graph": config.get("graph", "reflexion"),
                        "task": config.get("task", ""),
                        "score": 0.0,
                        "critique": str(exc),
                        "revision_count": 0,
                        "output": "",
                        "skill_version": 1,
                        "status": "failed",
                    }
                )
                await self.broadcast(
                    {
                        "type": "run_failed",
                        "run_id": run_id,
                        "agent_id": config.get("agent_id"),
                        "project": config.get("project"),
                        "error": str(exc),
                    }
                )
            finally:
                self._active_runs.pop(run_id, None)
                self._queue.task_done()

    def cancel_run(self, run_id: str) -> bool:
        cancel_flag = self._active_runs.get(run_id)
        if not cancel_flag:
            return False
        cancel_flag.set()
        return True


hub = HubServer()

def make_emit(run_id: str):
    async def _emit(event_type: str, **kwargs: Any):
        await hub.broadcast({"type": event_type, "run_id": run_id, **kwargs})

    def emit(event_type: str, **kwargs: Any):
        loop = hub._loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(_emit(event_type, **kwargs), loop)

    return emit

from __future__ import annotations

import asyncio
import logging
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from core.database import (
    _check_job_cancel_flag,
    _claim_queued_job,
    _cleanup_old_ws_events,
    _count_queued_jobs,
    _create_record,
    _get_ws_events_since,
    _insert_ws_event,
    _now_iso,
    _queue_job_record,
    _release_scheduler_lock,
    _save_run_record,
    _try_acquire_scheduler_lock,
    _update_job_record,
    _utcnow,
)

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
        # DB-backed broadcast state (replaces asyncio.Queue)
        self._last_event_id: int = 0
        self._active_runs: dict[str, threading.Event] = {}
        self._clients: set[Any] = set()
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._scheduler = None
        self._is_scheduler_leader: bool = False
        self._queue_paused = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_tasks: list[asyncio.Task] = []
        self._event_poll_task: asyncio.Task | None = None
        self.logger = get_logger("server")

    async def submit_job(self, config: dict) -> str:
        run_id = config.get("run_id") or uuid.uuid4().hex
        payload = dict(config)
        payload["run_id"] = run_id
        payload.setdefault("graph", "reflexion")
        payload.setdefault("max_revisions", 2)
        payload.setdefault("priority", "normal")
        _queue_job_record(payload)
        await self.broadcast(
            {
                "type": "run_queued",
                "run_id": run_id,
                "agent_id": payload.get("agent_id"),
                "project": payload.get("project"),
                "graph": payload.get("graph"),
                "queue_depth": _count_queued_jobs(),
            }
        )
        return run_id

    async def broadcast(self, event: dict) -> None:
        """Write event to ws_events table. All worker processes poll and forward to their WS clients."""
        _insert_ws_event(event)
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

    async def _event_poll_loop(self) -> None:
        """Poll ws_events table and forward new events to this worker's connected WS clients."""
        self._loop = asyncio.get_running_loop()
        cleanup_counter = 0
        while True:
            try:
                events = _get_ws_events_since(self._last_event_id)
                for event_id, payload in events:
                    self._last_event_id = event_id
                    dead_clients: list[Any] = []
                    for client in list(self._clients):
                        try:
                            await client.send_json(payload)
                        except Exception:
                            dead_clients.append(client)
                    for client in dead_clients:
                        self._clients.discard(client)
                # Periodic cleanup of old ws_events (~every 5 minutes)
                cleanup_counter += 1
                if cleanup_counter >= 1500:  # 1500 * 200ms = 5 min
                    cleanup_counter = 0
                    _cleanup_old_ws_events()
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Error in event poll loop")
            await asyncio.sleep(0.2)

    async def _db_worker_loop(self) -> None:
        """Poll job_queue for unclaimed jobs and execute them. Safe to run in N workers."""
        self._loop = asyncio.get_running_loop()
        while True:
            try:
                if self._queue_paused:
                    await asyncio.sleep(0.5)
                    continue

                job = _claim_queued_job()
                if job is None:
                    await asyncio.sleep(0.5)
                    continue

                job_data: dict = job.get("job_data") or {}
                if isinstance(job_data, str):
                    import json
                    try:
                        job_data = json.loads(job_data)
                    except Exception:
                        job_data = {}
                config = {**job_data, **{k: v for k, v in job.items() if k != "job_data"}}
                config["run_id"] = job.get("id") or job.get("run_id")
                run_id = config["run_id"]

                cancel_flag = threading.Event()
                self._active_runs[run_id] = cancel_flag
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

                    # Run the graph in executor; also poll for cancel flag from DB
                    future = loop.run_in_executor(self._executor, _execute)
                    while not future.done():
                        await asyncio.sleep(2.0)
                        if _check_job_cancel_flag(run_id):
                            cancel_flag.set()
                    result = await future

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

            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Unexpected error in DB worker loop")
                await asyncio.sleep(1.0)

    def cancel_run(self, run_id: str) -> bool:
        """Signal cancellation. Sets the local threading.Event (if run is on this worker)
        and marks the DB job as 'cancelling' so other workers pick it up."""
        cancel_flag = self._active_runs.get(run_id)
        if cancel_flag:
            cancel_flag.set()
        # Write cancelling status so all workers see it
        _update_job_record(run_id, "cancelling")
        return True

    def _try_scheduler_lock(self) -> bool:
        return _try_acquire_scheduler_lock(os.getpid())

    def _release_scheduler_lock_safe(self) -> None:
        try:
            _release_scheduler_lock(os.getpid())
        except Exception:
            pass


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


from __future__ import annotations

import asyncio
import json
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
    _mark_worker_draining,
    _now_iso,
    _queue_job_record,
    _reap_stale_jobs,
    _release_scheduler_lock,
    _save_run_record,
    _try_acquire_scheduler_lock,
    _update_job_record,
    _upsert_worker_node,
    _utcnow,
    _worker_heartbeat,
    _worker_id,
)

# Reaper threshold (minutes a job may stay 'running' before being marked failed).
JOB_REAP_MINUTES = int(os.environ.get("JOB_REAP_MINUTES", "15") or "15")
# How often the reaper loop runs (seconds).
JOB_REAP_INTERVAL_SEC = int(os.environ.get("JOB_REAP_INTERVAL_SEC", "180") or "180")
# Worker heartbeat interval (seconds) and the staleness window the reaper uses to
# declare a node dead (SCALABILITY §2 suggests ~10s heartbeat).
WORKER_HEARTBEAT_SEC = int(os.environ.get("WORKER_HEARTBEAT_SEC", "10") or "10")
WORKER_HEARTBEAT_TIMEOUT_SEC = int(os.environ.get("WORKER_HEARTBEAT_TIMEOUT_SEC", "45") or "45")
# This node's role + advertised capacity/inference endpoint for the registry.
WORKER_ROLE = os.environ.get("WORKER_ROLE", "worker")
WORKER_CAPACITY = int(os.environ.get("WORKER_CAPACITY", "5") or "5")
WORKER_OLLAMA_URL = os.environ.get("OLLAMA_URL", "")
# Scheduler-leader lease TTL (seconds) and renewal interval (seconds).
SCHEDULER_LEASE_TTL_SEC = int(os.environ.get("SCHEDULER_LEASE_TTL_SEC", "30") or "30")
SCHEDULER_LEASE_RENEW_SEC = int(os.environ.get("SCHEDULER_LEASE_RENEW_SEC", "10") or "10")

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
        # Dedicated executor for Inez chat turns so interactive responses
        # are never starved by background graph runs filling _executor.
        self._inez_executor = ThreadPoolExecutor(max_workers=2)
        self._scheduler = None
        self._is_scheduler_leader: bool = False
        self._queue_paused = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_tasks: list[asyncio.Task] = []
        self._event_poll_task: asyncio.Task | None = None
        self._ws_listen_task: asyncio.Task | None = None
        self._reaper_task: asyncio.Task | None = None
        self._scheduler_lease_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None
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

    async def _forward_payload(self, payload: dict) -> None:
        """Fan a single event payload out to this node's connected WS clients,
        pruning any that error. Shared by the poll loop (sqlite / fallback) and the
        LISTEN/NOTIFY listener (postgres)."""
        dead_clients: list[Any] = []
        for client in list(self._clients):
            try:
                await client.send_json(payload)
            except Exception:
                dead_clients.append(client)
        for client in dead_clients:
            self._clients.discard(client)

    async def _event_poll_loop(self) -> None:
        """Poll ws_events and forward new events to this worker's WS clients.

        This is the SQLite path (no LISTEN/NOTIFY) and the documented Postgres
        FALLBACK. On Postgres the primary path is _ws_listen_loop (LISTEN/NOTIFY);
        hub_server starts the listener there and skips this poller. Kept intact so
        SQLite does not regress and PG has a working degraded mode.
        """
        self._loop = asyncio.get_running_loop()
        cleanup_counter = 0
        while True:
            try:
                events = _get_ws_events_since(self._last_event_id)
                for event_id, payload in events:
                    self._last_event_id = event_id
                    await self._forward_payload(payload)
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

    async def _ws_listen_loop(self) -> None:
        """Postgres LISTEN/NOTIFY broadcast (T7 / POSTGRES_MIGRATION §7.2).

        Runs a dedicated psycopg connection that ``LISTEN ws_events`` and blocks on
        notifications; each carries a ws_events row id. On boot we drain any events
        missed while starting (id > _last_event_id) so nothing is lost between the
        table insert and LISTEN registration, then forward each notified row.

        ws_events stays the durable replay log (Inez run-event replay reads it) —
        this loop only replaces the *polling*, not the table.

        verified: sqlite; pg path unexecuted (no infra). The notify handling uses
        psycopg3's connection.notifies() generator (blocking, timeout-bounded).
        """
        self._loop = asyncio.get_running_loop()
        import psycopg  # local import: only needed on the PG path
        from core.config import DATABASE_URL
        from core.database import _get_ws_event_by_id, _get_ws_events_since

        while True:
            conn = None
            try:
                conn = await asyncio.to_thread(psycopg.connect, DATABASE_URL, autocommit=True)
                await asyncio.to_thread(conn.execute, "LISTEN ws_events")
                # Catch up on anything inserted before LISTEN was armed.
                for event_id, payload in _get_ws_events_since(self._last_event_id):
                    self._last_event_id = max(self._last_event_id, event_id)
                    await self._forward_payload(payload)
                # Block for notifications; timeout lets us honour cancellation.
                while True:
                    notifies = await asyncio.to_thread(
                        lambda: list(conn.notifies(timeout=5.0, stop_after=1))
                    )
                    for note in notifies:
                        try:
                            event_id = int(note.payload)
                        except (TypeError, ValueError):
                            continue
                        got = _get_ws_event_by_id(event_id)
                        if got is None:
                            continue
                        eid, payload = got
                        self._last_event_id = max(self._last_event_id, eid)
                        await self._forward_payload(payload)
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Error in ws LISTEN/NOTIFY loop; retrying")
                await asyncio.sleep(1.0)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

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

    # ── Job reaper (Feature 3, failure #4) ───────────────────────────────────

    def reap_stale_jobs(self) -> int:
        """Mark jobs stuck in 'running' past JOB_REAP_MINUTES as failed. Returns count.

        Safe to call from any/all workers concurrently — the underlying SQL is a
        single idempotent UPDATE guarded by the stale condition.
        """
        try:
            return _reap_stale_jobs(JOB_REAP_MINUTES, WORKER_HEARTBEAT_TIMEOUT_SEC)
        except Exception:
            self.logger.exception("Job reaper failed")
            return 0

    async def _reaper_loop(self) -> None:
        """Run the stale-job reaper once on startup, then every JOB_REAP_INTERVAL_SEC.

        Every worker runs this loop; the reaping SQL is idempotent so duplicate runs
        across the 5 workers are harmless (the second and later UPDATEs match no rows).
        """
        while True:
            try:
                self.reap_stale_jobs()
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Unexpected error in reaper loop")
            try:
                await asyncio.sleep(max(30, JOB_REAP_INTERVAL_SEC))
            except asyncio.CancelledError:
                break

    # ── Worker registry + heartbeat (T8 / SCALABILITY §2) ────────────────────

    def register_node(self) -> str:
        """Upsert this process's worker_nodes row on boot. Runs on EVERY node
        (worker/api/control), not just the scheduler leader."""
        try:
            wid = _upsert_worker_node(
                role=WORKER_ROLE, capacity=WORKER_CAPACITY, ollama_url=WORKER_OLLAMA_URL
            )
            self.logger.info("Registered worker node %s (role=%s, capacity=%s)", wid, WORKER_ROLE, WORKER_CAPACITY)
            return wid
        except Exception:
            self.logger.exception("Worker node registration failed")
            return _worker_id()

    async def _heartbeat_loop(self) -> None:
        """Refresh this node's last_heartbeat + owned jobs' heartbeat_at every
        WORKER_HEARTBEAT_SEC. Runs on every node so the reaper can distinguish a
        live worker from a dead one (T8). Not wired via _JOB_SPECS because those
        fire on the scheduler leader ONLY — every node must heartbeat itself.
        """
        cleanup_counter = 0
        while True:
            try:
                _worker_heartbeat()
                # Age out old ws_events (~every 5 min). On SQLite the poll loop also
                # does this; on Postgres the poll loop is off, so do it here — the
                # DELETE is idempotent and safe to run from any/all nodes.
                cleanup_counter += 1
                if cleanup_counter * max(2, WORKER_HEARTBEAT_SEC) >= 300:
                    cleanup_counter = 0
                    _cleanup_old_ws_events()
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Worker heartbeat failed")
            try:
                await asyncio.sleep(max(2, WORKER_HEARTBEAT_SEC))
            except asyncio.CancelledError:
                break

    def deregister_node(self) -> None:
        """Mark this node 'draining' on graceful shutdown so it stops attracting
        new claims while in-flight jobs finish (SCALABILITY §3)."""
        try:
            _mark_worker_draining()
        except Exception:
            pass

    # ── Scheduler leader election (Feature 3, failure #5) ────────────────────

    def _try_scheduler_lock(self) -> bool:
        return _try_acquire_scheduler_lock(os.getpid(), ttl=SCHEDULER_LEASE_TTL_SEC)

    def _release_scheduler_lock_safe(self) -> None:
        try:
            _release_scheduler_lock(os.getpid())
        except Exception:
            pass

    def is_scheduler_leader(self) -> bool:
        """Whether THIS worker currently owns the scheduler lease.

        Consulted by the tracked-job wrapper (hub_scheduler._make_tracked) at fire
        time so that only the leader executes scheduled jobs, even during a brief
        lease handover.
        """
        return bool(self._is_scheduler_leader)

    async def _scheduler_lease_loop(self) -> None:
        """Continuously acquire/renew the scheduler-leader lease.

        Exactly one worker at a time holds the lease and runs _JOB_SPECS jobs. The
        leader renews every SCHEDULER_LEASE_RENEW_SEC (< TTL) to keep it. If the
        leader process dies, the lease expires and another worker acquires it here,
        starting its (already-built) APScheduler — automatic failover without a
        restart. Non-leaders keep their scheduler stopped AND the tracked wrapper
        no-ops, so scheduled jobs never fire more than once across the 5 workers.
        """
        while True:
            try:
                is_leader = self._try_scheduler_lock()
                if is_leader and not self._is_scheduler_leader:
                    # Became leader (startup or failover) — start our scheduler.
                    self._is_scheduler_leader = True
                    if self._scheduler is not None:
                        try:
                            running = getattr(getattr(self._scheduler, "scheduler", None), "running", False)
                            if not running:
                                self._scheduler.start()
                                self.logger.info("Acquired scheduler leadership (pid=%s) — scheduler started", os.getpid())
                        except Exception:
                            self.logger.exception("Failed to start scheduler after acquiring leadership")
                elif not is_leader and self._is_scheduler_leader:
                    # Lost leadership (should be rare) — stand down.
                    self._is_scheduler_leader = False
                    self.logger.warning("Lost scheduler leadership (pid=%s) — standing down", os.getpid())
                    try:
                        if self._scheduler is not None:
                            self._scheduler.shutdown()
                    except Exception:
                        pass
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Unexpected error in scheduler lease loop")
            try:
                await asyncio.sleep(max(2, SCHEDULER_LEASE_RENEW_SEC))
            except asyncio.CancelledError:
                break


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


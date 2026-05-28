"""
AgentHarness Hub — FastAPI Server
hub_server.py

Always-on backend for AgentHarness v3.
Handles agent execution, job queue, WebSocket streaming, scheduling, and persistence.
Mirrors how Base44's online agent platform works — runs regardless of whether the
desktop app (main_m365.py) is open.

Start:
    python hub_server.py
    (or via hub_start.ps1 for Windows service mode)

Desktop connects to:
    REST API:  http://localhost:8765/api/...
    WebSocket: ws://localhost:8765/ws
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import signal
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Resolve paths ─────────────────────────────────────────────────────────────
HERE       = Path(__file__).parent
HARNESS    = HERE.parent.parent
DATA_DIR   = HARNESS.parent / "data"
PID_FILE   = DATA_DIR / "hub.pid"
LOG_DIR    = DATA_DIR / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(HERE))

# ── Local imports ─────────────────────────────────────────────────────────────
from hub_db import (
    init_schema, migrate_todos_json,
    enqueue_job, update_job_status, load_pending_jobs, get_job, list_jobs,
    save_run, load_runs, agent_stats,
    create_todo, get_todo, list_todos, update_todo, delete_todo,
    save_skill, load_skill, list_skills,
    save_notification, list_notifications, mark_notifications_read, clear_notifications,
    get_config, set_config, get_briefing_cache,
    save_scheduled_job, list_scheduled_jobs, delete_scheduled_job,
)
from hub_nodes import run_graph, LANGGRAPH_OK
from hub_scheduler import build_scheduler, get_job_list

HUB_VERSION = "1.0.0"
HUB_PORT    = 8765
THREAD_POOL_DEFAULT = 3


# ════════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS — request/response schemas
# ════════════════════════════════════════════════════════════════════════════════

class RunSubmitRequest(BaseModel):
    agent_id:      str
    project:       str = "global"
    graph:         str = "reflexion"
    task:          str
    max_revisions: int = 2
    priority:      str = "normal"   # urgent | normal | low

class TodoCreateRequest(BaseModel):
    title:    str
    priority: str = "medium"
    project:  Optional[str] = None
    due_date: Optional[str] = None

class TodoUpdateRequest(BaseModel):
    title:    Optional[str] = None
    priority: Optional[str] = None
    status:   Optional[str] = None
    project:  Optional[str] = None
    due_date: Optional[str] = None

class ScheduleAddRequest(BaseModel):
    agent_id:      str
    project:       str = "global"
    graph:         str = "reflexion"
    task:          str
    run_type:      str = "once"      # once | daily | weekly | cron | interval
    scheduled_at:  Optional[str] = None   # ISO datetime for one-time
    cron_expr:     Optional[str] = None   # e.g. "0 8 * * 1"
    interval_sec:  Optional[int] = None   # seconds between runs
    max_revisions: int = 2

class ConfigUpdateRequest(BaseModel):
    thread_pool_size: Optional[int] = None
    model:            Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════════
# HUB SERVER CLASS
# ════════════════════════════════════════════════════════════════════════════════

class HubServer:
    """Central server object — holds queue, pool, WebSocket clients, scheduler."""

    def __init__(self):
        self.start_time     = datetime.now(timezone.utc)
        self.job_queue:     asyncio.Queue = asyncio.Queue()
        self.active_runs:   Dict[str, dict] = {}   # job_id → run metadata
        self.cancel_flags:  Dict[str, threading.Event] = {}
        self.ws_clients:    Set[WebSocket] = set()
        self.executor:      ThreadPoolExecutor = None
        self.scheduler      = None
        self._pool_size     = get_config("thread_pool_size", THREAD_POOL_DEFAULT)
        self._queue_paused  = False

    # ── WebSocket broadcast ──────────────────────────────────────────────────
    async def broadcast(self, event: dict):
        """Send an event to all connected WebSocket clients."""
        dead = set()
        msg  = json.dumps(event)
        for ws in list(self.ws_clients):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.add(ws)
        self.ws_clients -= dead

        # Also persist notifications to DB
        if event.get("type") == "notif":
            save_notification(event.get("text",""), event.get("color"), event.get("category","system"))

    # ── Emit function for graph nodes ────────────────────────────────────────
    def make_emit(self, job_id: str):
        """Return an emit callable that broadcasts WebSocket events for a job."""
        loop = asyncio.get_event_loop()

        def emit(event_type: str, **data):
            event = {"type": event_type, "job_id": job_id, **data}
            # Schedule broadcast on the event loop from the worker thread
            asyncio.run_coroutine_threadsafe(self.broadcast(event), loop)

        return emit

    # ── Job submission ────────────────────────────────────────────────────────
    async def submit_job(self, config: dict) -> str:
        """Enqueue an agent job. Returns job_id."""
        job_id = config.get("id") or uuid.uuid4().hex[:8]
        config["id"] = job_id
        enqueue_job(config)

        position = self.job_queue.qsize() + 1
        await self.job_queue.put(config)

        await self.broadcast({
            "type":     "run_queued",
            "job_id":   job_id,
            "agent_id": config["agent_id"],
            "graph":    config.get("graph","reflexion"),
            "position": position,
        })
        save_notification(
            f"Queued: {config['agent_id']} ({config.get('graph','reflexion')})",
            "#60a5fa", "run"
        )
        return job_id

    # ── Worker ────────────────────────────────────────────────────────────────
    def _execute_job(self, config: dict):
        """Run in ThreadPoolExecutor worker — blocks on LLM calls."""
        job_id     = config["id"]
        cancel_ev  = threading.Event()
        self.cancel_flags[job_id] = cancel_ev
        config["cancel_flag"] = cancel_ev

        update_job_status(job_id, "running")
        emit = self.make_emit(job_id)

        self.active_runs[job_id] = {
            "job_id":   job_id,
            "agent_id": config["agent_id"],
            "project":  config.get("project","global"),
            "graph":    config.get("graph","reflexion"),
            "started":  datetime.now(timezone.utc).isoformat(),
        }

        try:
            final = run_graph(config, emit=emit)
            update_job_status(job_id, "complete")
            save_notification(
                f"Complete: {config['agent_id']} score={final.get('score',0):.2f}",
                "#92c353", "run"
            )
        except Exception as e:
            update_job_status(job_id, "failed", job_data=json.dumps({"error": str(e)}))
            save_notification(f"Failed: {config['agent_id']} — {str(e)[:80]}", "#e74856", "run")
        finally:
            self.active_runs.pop(job_id, None)
            self.cancel_flags.pop(job_id, None)

    # ── Queue consumer ────────────────────────────────────────────────────────
    async def queue_worker(self):
        """Async loop — dequeues jobs and submits to thread pool."""
        print(f"[Hub] Queue worker started (pool={self._pool_size})")
        loop = asyncio.get_event_loop()
        while True:
            if self._queue_paused:
                await asyncio.sleep(2)
                continue
            try:
                config = await asyncio.wait_for(self.job_queue.get(), timeout=5.0)
                loop.run_in_executor(self.executor, self._execute_job, config)
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"[Hub] Queue worker error: {e}")

    # ── Startup ───────────────────────────────────────────────────────────────
    async def startup(self):
        """Initialize everything on server start."""
        print(f"\n[Hub] AgentHarness Hub v{HUB_VERSION} starting on port {HUB_PORT}")

        # DB
        init_schema()
        migrate_todos_json()

        # Thread pool
        self.executor = ThreadPoolExecutor(
            max_workers=self._pool_size,
            thread_name_prefix="HubWorker"
        )

        # Reload pending jobs from DB (survive restart)
        pending = load_pending_jobs()
        for job in pending:
            job_data = {}
            try:
                job_data = json.loads(job.get("job_data") or "{}")
            except Exception:
                pass
            config = {**job_data, **job, "id": job["id"]}
            await self.job_queue.put(config)
        if pending:
            print(f"[Hub] Reloaded {len(pending)} pending jobs from DB")

        # Queue worker
        asyncio.create_task(self.queue_worker(), name="queue_worker")

        # Scheduler
        self.scheduler = build_scheduler(self)
        self.scheduler.start()

        # PID file
        PID_FILE.write_text(str(os.getpid()))

        print(f"[Hub] Ready — REST: http://localhost:{HUB_PORT}/api  WS: ws://localhost:{HUB_PORT}/ws")
        print(f"[Hub] Docs: http://localhost:{HUB_PORT}/docs\n")

    # ── Shutdown ──────────────────────────────────────────────────────────────
    async def shutdown(self):
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        PID_FILE.unlink(missing_ok=True)
        print("[Hub] Shutdown complete")


# ── Global hub instance ───────────────────────────────────────────────────────
hub = HubServer()

# ════════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ════════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="AgentHarness Hub",
    description="Always-on backend for AgentHarness v3 — Smith Capital Portfolio",
    version=HUB_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await hub.startup()


@app.on_event("shutdown")
async def on_shutdown():
    await hub.shutdown()


# ════════════════════════════════════════════════════════════════════════════════
# WEBSOCKET
# ════════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    hub.ws_clients.add(ws)

    # Send initial state snapshot
    await ws.send_text(json.dumps({
        "type":         "state_snapshot",
        "hub_version":  HUB_VERSION,
        "active_runs":  list(hub.active_runs.values()),
        "queue_depth":  hub.job_queue.qsize(),
        "scheduler_jobs": len(hub.scheduler.get_jobs()) if hub.scheduler else 0,
    }))

    try:
        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                data = json.loads(raw)
                evt  = data.get("type", "")

                if evt == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))

                elif evt == "cancel_run":
                    job_id = data.get("job_id","")
                    flag   = hub.cancel_flags.get(job_id)
                    if flag:
                        flag.set()
                        update_job_status(job_id, "cancelled")
                        await hub.broadcast({"type":"run_cancelled","job_id":job_id})

                elif evt == "subscribe_run":
                    # Client wants updates for a specific job — already broadcast globally
                    job = get_job(data.get("job_id",""))
                    if job:
                        await ws.send_text(json.dumps({"type":"run_status","job": job}))

            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await ws.send_text(json.dumps({"type": "heartbeat"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        hub.ws_clients.discard(ws)


# ════════════════════════════════════════════════════════════════════════════════
# HEALTH
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    uptime = (datetime.now(timezone.utc) - hub.start_time).total_seconds()
    return {
        "status":          "ok",
        "version":         HUB_VERSION,
        "uptime_seconds":  int(uptime),
        "active_runs":     len(hub.active_runs),
        "queue_depth":     hub.job_queue.qsize(),
        "queue_paused":    hub._queue_paused,
        "ws_clients":      len(hub.ws_clients),
        "scheduler_jobs":  len(hub.scheduler.get_jobs()) if hub.scheduler else 0,
        "thread_pool":     hub._pool_size,
        "langgraph_ok":    LANGGRAPH_OK,
    }


# ════════════════════════════════════════════════════════════════════════════════
# RUNS
# ════════════════════════════════════════════════════════════════════════════════

@app.post("/api/run/submit", status_code=202)
async def submit_run(req: RunSubmitRequest):
    config = req.model_dump()
    job_id = await hub.submit_job(config)
    return {
        "job_id":   job_id,
        "status":   "queued",
        "position": hub.job_queue.qsize(),
        "estimated_start_seconds": hub.job_queue.qsize() * 45,
    }


@app.get("/api/run/{job_id}")
async def get_run(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return job


@app.delete("/api/run/{job_id}")
async def cancel_run(job_id: str):
    flag = hub.cancel_flags.get(job_id)
    if flag:
        flag.set()
    update_job_status(job_id, "cancelled")
    await hub.broadcast({"type": "run_cancelled", "job_id": job_id})
    return {"job_id": job_id, "status": "cancelled"}


@app.get("/api/runs")
async def list_runs_endpoint(
    status:   Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    project:  Optional[str] = Query(None),
    limit:    int = Query(50, ge=1, le=500),
    skip:     int = Query(0, ge=0),
):
    return load_runs(limit=limit, status=status, agent_id=agent_id, project=project, skip=skip)


@app.get("/api/runs/stats")
async def runs_stats():
    return agent_stats()


@app.get("/api/runs/briefing")
async def briefing():
    data = get_briefing_cache()
    if not data:
        # Compute on demand if not cached
        stats       = agent_stats()
        todos       = list_todos(status="pending")
        all_runs    = load_runs(limit=500)
        flagged     = [a for a, s in stats.items() if s["avg"] < 0.60 and s["runs"] > 0]
        passing     = [a for a, s in stats.items() if s["avg"] >= 0.75 and s["runs"] > 0]
        data = {
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "total_runs":     len(all_runs),
            "agents_total":   len(stats),
            "passing_agents": len(passing),
            "flagged_agents": flagged,
            "flagged_details":[{"agent_id":a,"avg_score":stats[a]["avg"],"runs":stats[a]["runs"]} for a in flagged[:10]],
            "top_todos":      sorted(todos, key=lambda t:{"urgent":0,"high":1,"medium":2,"low":3}.get(t.get("priority","low"),3))[:8],
            "todos_pending":  len(todos),
            "blockers":       [
                "PBS site: Golf Tournament + Chapter Dues pages need payment links",
                "XFTC Gmail: forwarding rule required for signup logger",
                "Smith Capital LLC: TX Comptroller reactivation overdue",
                "Clarity Solar: TX SB 1036 GL insurance deadline Sep 1, 2026",
                "Smith Capital Holdings: S-Corp election not yet filed",
            ],
            "last_24h_runs": 0,
        }
        from hub_db import cache_briefing
        cache_briefing(data)
    return data


@app.get("/api/queue/jobs")
async def queue_jobs():
    return list_jobs(limit=100)


@app.post("/api/queue/pause")
async def pause_queue():
    hub._queue_paused = True
    return {"status": "paused"}


@app.post("/api/queue/resume")
async def resume_queue():
    hub._queue_paused = False
    return {"status": "running"}


# ════════════════════════════════════════════════════════════════════════════════
# SKILLS
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/skills")
async def list_skills_endpoint():
    return list_skills()


@app.get("/api/skills/{agent_id}")
async def get_skill(agent_id: str):
    skill_name = agent_id.replace("-", "_")
    content, version = load_skill(skill_name)
    from hub_nodes import read_agent_skill_file
    if not content:
        content = read_agent_skill_file(agent_id)
    return {"agent_id": agent_id, "skill_name": skill_name, "version": version, "content": content}


@app.put("/api/skills/{agent_id}")
async def update_skill(agent_id: str, body: dict):
    skill_name = agent_id.replace("-", "_")
    save_skill(agent_id, skill_name, body.get("version", 1),
               body.get("content",""), body.get("avg_score",0.0), "Manual update")
    from hub_nodes import write_agent_skill_file
    write_agent_skill_file(agent_id, body.get("content",""))
    return {"agent_id": agent_id, "status": "updated"}


# ════════════════════════════════════════════════════════════════════════════════
# TODOS
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/todos")
async def list_todos_endpoint(
    status:   Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
):
    return list_todos(status=status, priority=priority)


@app.post("/api/todos", status_code=201)
async def create_todo_endpoint(req: TodoCreateRequest):
    todo = create_todo(req.model_dump())
    await hub.broadcast({"type": "todo_update", "action": "create", "todo": todo})
    return todo


@app.patch("/api/todos/{todo_id}")
async def update_todo_endpoint(todo_id: str, req: TodoUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    todo    = update_todo(todo_id, updates)
    if not todo:
        raise HTTPException(404, f"Todo {todo_id} not found")
    await hub.broadcast({"type": "todo_update", "action": "update", "todo": todo})
    return todo


@app.delete("/api/todos/{todo_id}")
async def delete_todo_endpoint(todo_id: str):
    ok = delete_todo(todo_id)
    if not ok:
        raise HTTPException(404, f"Todo {todo_id} not found")
    await hub.broadcast({"type": "todo_update", "action": "delete", "todo": {"id": todo_id}})
    return {"id": todo_id, "deleted": True}


# ════════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/notifications")
async def get_notifications(limit: int = Query(100, ge=1, le=1000)):
    return list_notifications(limit=limit)


@app.post("/api/notifications/push")
async def push_notification(body: dict):
    text     = body.get("text", "")
    color    = body.get("color", "#60a5fa")
    category = body.get("category", "system")
    await hub.broadcast({"type": "notif", "text": text, "color": color, "category": category})
    return {"status": "sent"}


@app.delete("/api/notifications")
async def clear_notifications_endpoint():
    clear_notifications()
    return {"status": "cleared"}


# ════════════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/scheduler/jobs")
async def scheduler_jobs():
    if not hub.scheduler:
        return []
    return get_job_list(hub.scheduler)


@app.post("/api/scheduler/add", status_code=201)
async def add_scheduled_job(req: ScheduleAddRequest):
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from hub_scheduler import CT_TZ, job_grant_research_sweep

    config = req.model_dump()
    job_id = uuid.uuid4().hex[:8]
    config["id"] = job_id

    async def _fire():
        await hub.submit_job(config)
        await hub.broadcast({
            "type":     "scheduler_fired",
            "job_id":   job_id,
            "agent_id": config["agent_id"],
        })

    # Determine trigger
    if req.run_type == "once" and req.scheduled_at:
        from dateutil import parser as dtparser
        fire_dt = dtparser.parse(req.scheduled_at)
        trigger = DateTrigger(run_date=fire_dt)
    elif req.run_type == "cron" and req.cron_expr:
        parts   = req.cron_expr.split()
        trigger = CronTrigger(
            minute=parts[0], hour=parts[1], day=parts[2],
            month=parts[3], day_of_week=parts[4], timezone=CT_TZ
        )
    elif req.run_type in ("interval","daily","weekly") and req.interval_sec:
        trigger = IntervalTrigger(seconds=req.interval_sec)
    elif req.run_type == "daily":
        trigger = CronTrigger(hour=9, minute=0, timezone=CT_TZ)  # default 9 AM CT
    elif req.run_type == "weekly":
        trigger = CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=CT_TZ)
    else:
        raise HTTPException(400, "Invalid run_type or missing scheduled_at/cron_expr")

    hub.scheduler.add_job(_fire, trigger, id=job_id, name=f"{req.agent_id} ({req.run_type})")
    save_scheduled_job({**config, "id": job_id})

    next_fire = hub.scheduler.get_job(job_id)
    return {
        "id":        job_id,
        "status":    "scheduled",
        "next_fire": next_fire.next_run_time.isoformat() if next_fire and next_fire.next_run_time else None,
    }


@app.delete("/api/scheduler/{job_id}")
async def cancel_scheduled_job(job_id: str):
    try:
        hub.scheduler.remove_job(job_id)
    except Exception:
        pass
    delete_scheduled_job(job_id)
    return {"id": job_id, "status": "cancelled"}


# ════════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/api/config")
async def get_hub_config():
    return {
        "thread_pool_size": hub._pool_size,
        "queue_paused":     hub._queue_paused,
        "hub_port":         HUB_PORT,
        "hub_version":      HUB_VERSION,
        "model":            os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "langgraph_ok":     LANGGRAPH_OK,
    }


@app.patch("/api/config")
async def update_hub_config(req: ConfigUpdateRequest):
    if req.thread_pool_size is not None:
        hub._pool_size = req.thread_pool_size
        set_config("thread_pool_size", req.thread_pool_size)
        # Recreate executor with new size
        old = hub.executor
        hub.executor = ThreadPoolExecutor(
            max_workers=hub._pool_size,
            thread_name_prefix="HubWorker"
        )
        if old:
            old.shutdown(wait=False)
    if req.model is not None:
        os.environ["OPENAI_MODEL"] = req.model
        set_config("model", req.model)
    return await get_hub_config()


# ════════════════════════════════════════════════════════════════════════════════
# ROOT — simple status page
# ════════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    uptime = int((datetime.now(timezone.utc) - hub.start_time).total_seconds())
    return JSONResponse({
        "app":         "AgentHarness Hub",
        "version":     HUB_VERSION,
        "status":      "online",
        "uptime":      f"{uptime}s",
        "active_runs": len(hub.active_runs),
        "docs":        f"http://localhost:{HUB_PORT}/docs",
        "ws":          f"ws://localhost:{HUB_PORT}/ws",
    })


# ════════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Load .env
    env_file = Path(__file__).parent.parent.parent.parent / ".agents" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k = k.strip(); v = v.strip().strip("'").strip('"')
                if k and v:
                    os.environ.setdefault(k, v)
        print(f"[Hub] .env loaded from {env_file}")

    def _graceful_shutdown(sig, frame):
        print("\n[Hub] Received shutdown signal — stopping...")
        sys.exit(0)

    signal.signal(signal.SIGINT,  _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    print(f"[Hub] Starting AgentHarness Hub v{HUB_VERSION}")
    print(f"[Hub] REST API: http://localhost:{HUB_PORT}/api")
    print(f"[Hub] WebSocket: ws://localhost:{HUB_PORT}/ws")
    print(f"[Hub] Auto-docs: http://localhost:{HUB_PORT}/docs")
    print()

    uvicorn.run(
        "hub_server:app",
        host="127.0.0.1",
        port=HUB_PORT,
        reload=False,
        log_level="info",
        ws_ping_interval=30,
        ws_ping_timeout=10,
    )

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_admin_user, get_current_user
from core.config import APP_VERSION, DB_PATH
from core.database import _agent_stats, _all_config, _briefing_cache, _count_rows, _update_config_values, _utcnow
from core.hub import LANGGRAPH_OK, hub
from core.models import ConfigUpdate
from routers.scheduler import _scheduler_job_count

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("config_api")
router = APIRouter()

@router.get("/health")
async def health():
    queue_depth = hub._queue.qsize() if hub._queue else 0
    # Resolve current LLM provider + model from config
    try:
        from hub_nodes import _load_ai_config  # type: ignore
        _ai = _load_ai_config()
        _cfg = _all_config()
        _llm_provider = _cfg.get("llm_provider") or _ai.get("provider", "openai")
        _llm_model    = _cfg.get("llm_model")    or _ai.get("model",    "gpt-4o-mini")
    except Exception:
        _llm_provider, _llm_model = "openai", "gpt-4o-mini"

    scheduler_count = _scheduler_job_count()
    worker_ok = hub._worker_task is not None and not hub._worker_task.done()
    scheduler_ok = hub._scheduler is not None and scheduler_count > 0

    # Determine overall status
    if not worker_ok or not scheduler_ok:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "app": "ArchonHub",
        "version": APP_VERSION,
        "uptime_seconds": int((_utcnow() - hub.start_time).total_seconds()),
        "active_runs": len(hub._active_runs),
        "queue_depth": queue_depth,
        "ws_clients": len(hub._clients),
        "scheduler_jobs": scheduler_count,
        "scheduler_ok": scheduler_ok,
        "worker_ok": worker_ok,
        "thread_pool_size": getattr(hub._executor, "_max_workers", 3),
        "langgraph_ok": LANGGRAPH_OK,
        "pending_todos": _count_rows("todos", "status = ?", ["pending"]),
        "total_runs": _count_rows("runs"),
        "llm_provider": _llm_provider,
        "llm_model":    _llm_model,
    }

@router.get("/config")
async def get_config(admin_user: dict = Depends(get_admin_user)):
    del admin_user
    return _all_config()


@router.put("/config")
async def update_config(body: ConfigUpdate, admin_user: dict = Depends(get_admin_user)):
    del admin_user
    updated = _update_config_values(body.data)
    if "thread_pool_size" in body.data:
        old_executor = hub._executor
        hub._executor = ThreadPoolExecutor(max_workers=max(1, int(body.data["thread_pool_size"])))
        old_executor.shutdown(wait=False)
    return updated


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    del current_user
    return _agent_stats()


@router.get("/briefing")
async def get_briefing(current_user: dict = Depends(get_current_user)):
    del current_user
    return _briefing_cache()

@router.post("/monitoring/run")
async def run_monitoring(current_user: dict = Depends(get_current_user)):
    """Run proactive monitoring cycle (deadlines + anomalies)."""
    try:
        user_id = current_user.get("username", "default_user")
        from proactive_monitor import ProactiveMonitor
        
        monitor = ProactiveMonitor(DB_PATH)
        result = await monitor.run_monitoring(user_id)
        
        return result
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
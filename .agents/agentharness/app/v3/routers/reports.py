from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.auth import get_admin_user, get_current_user
from core.models import ReportRunRequest

try:
    import hub_db as db
except ImportError:
    db = None  # type: ignore

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("reports")
router = APIRouter()


@router.get("/reports")
async def list_reports_endpoint(
    report_type: Optional[str] = None,
    project_slug: Optional[str] = None,
    job_id: Optional[str] = None,
    limit: int = 100,
    _: dict = Depends(get_current_user),
):
    if not db or not hasattr(db, "list_reports"):
        raise HTTPException(503, "Reports not available")
    return db.list_reports(report_type=report_type, project_slug=project_slug, job_id=job_id, limit=limit)


@router.get("/reports/types/summary")
async def report_types_summary(_: dict = Depends(get_current_user)):
    if not db or not hasattr(db, "get_conn"):
        raise HTTPException(503, "Reports not available")
    with db.get_conn() as conn:
        rows = conn.execute("SELECT report_type, COUNT(*) as cnt FROM reports GROUP BY report_type ORDER BY cnt DESC").fetchall()
    return [{"report_type": r["report_type"], "count": r["cnt"]} for r in rows]


@router.get("/reports/{report_id}")
async def get_report_endpoint(report_id: str, _: dict = Depends(get_current_user)):
    if not db or not hasattr(db, "get_report"):
        raise HTTPException(503, "Reports not available")
    report = db.get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.delete("/reports/{report_id}")
async def delete_report_endpoint(report_id: str, _: dict = Depends(get_admin_user)):
    if not db or not hasattr(db, "delete_report"):
        raise HTTPException(503, "Reports not available")
    if not db.delete_report(report_id):
        raise HTTPException(404, "Report not found")
    return {"status": "deleted"}


@router.post("/reports/run")
async def run_report_endpoint(
    req: ReportRunRequest,
    background_tasks: BackgroundTasks,
    _: dict = Depends(get_admin_user),
):
    async def _run():
        try:
            from report_monitor import run_report_job
            await run_report_job(req.job_id, extra_context=req.extra_context)
        except Exception as exc:
            logger.error("Manual report run failed: %s", exc)

    background_tasks.add_task(_run)
    return {"status": "queued", "job_id": req.job_id}



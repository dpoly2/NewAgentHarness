from __future__ import annotations

"""
devops.py — DevOps reliability status API.

Aggregates the output of the devops monitoring team (project 'devops') into a
single status payload for the Issue Monitor dashboard (/web/devops.html):
  - monitoring health (last log sweep + recent failures)
  - incident tickets (todos) by status / priority
  - recent log_monitor reports
  - root-cause notes and fix proposals
All queries are defensive — a missing table/column degrades to empty, never 500.
"""

import json
import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from core.auth import get_current_user
from core.config import DB_PATH

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("devops")
router = APIRouter()

PROJECT = "devops"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    return conn


def _q(conn, sql, params=()):
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception:
        return []


@router.get("/devops/status")
async def devops_status(current_user: dict = Depends(get_current_user)):
    del current_user
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    try:
        # --- Incident tickets (todos) ---
        todos = _q(
            conn,
            "SELECT id,title,priority,status,assigned_agent,description,created_at "
            "FROM todos WHERE project=? ORDER BY "
            "CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC",
            (PROJECT,),
        )
        by_status: dict = {}
        by_priority: dict = {}
        for t in todos:
            by_status[t.get("status") or "unknown"] = by_status.get(t.get("status") or "unknown", 0) + 1
            by_priority[t.get("priority") or "unknown"] = by_priority.get(t.get("priority") or "unknown", 0) + 1
        open_tickets = [t for t in todos if (t.get("status") or "pending") not in ("done", "resolved", "closed", "complete")]

        # --- log_monitor reports ---
        reports = _q(
            conn,
            "SELECT title,status,summary,generated_at,created_at FROM reports "
            "WHERE project_slug=? OR title LIKE 'DevOps Log Monitor%' "
            "ORDER BY COALESCE(generated_at, created_at) DESC LIMIT 10",
            (PROJECT,),
        )

        # --- Root-cause notes + fix proposals ---
        rca = _q(
            conn,
            "SELECT title,created_at FROM knowledge_base WHERE project_slug=? "
            "ORDER BY created_at DESC LIMIT 15",
            (PROJECT,),
        )
        fixes = _q(
            conn,
            "SELECT title,status,created_at FROM documents WHERE project_slug=? "
            "ORDER BY created_at DESC LIMIT 15",
            (PROJECT,),
        )
        # Tickets the fix-engineer marked ready to apply
        fix_ready = [t for t in todos if "fix-ready" in str(t.get("description", "")).lower()
                     or "apply fix" in str(t.get("title", "")).lower()]

        # --- Monitoring health ---
        last_sweep = reports[0] if reports else None
        recent_failures = sum(1 for r in reports if (r.get("status") or "") == "partial")
        degraded_note = ""
        if last_sweep and (last_sweep.get("status") or "") == "partial":
            degraded_note = str(last_sweep.get("summary") or "")[:300]
        healthy = bool(last_sweep) and recent_failures == 0

        return {
            "generated_at": now,
            "project": PROJECT,
            "monitoring": {
                "healthy": healthy,
                "configured": True,
                "last_sweep": (last_sweep or {}).get("generated_at") or (last_sweep or {}).get("created_at"),
                "last_sweep_status": (last_sweep or {}).get("status"),
                "recent_failures": recent_failures,
                "degraded_note": degraded_note,
            },
            "tickets": {
                "total": len(todos),
                "open": len(open_tickets),
                "by_status": by_status,
                "by_priority": by_priority,
                "items": open_tickets[:30],
            },
            "reports": reports,
            "rca": rca,
            "fixes": fixes,
            "fixes_ready": fix_ready[:15],
        }
    finally:
        conn.close()

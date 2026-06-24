from __future__ import annotations

import sqlite3

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from core.auth import get_current_user
from core.config import DB_PATH

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name: str):
        return logging.getLogger(f"archonhub.{name}")

logger = get_logger("email_cleanup")
router = APIRouter()

@router.post("/email/cleanup/analyze")
async def analyze_email_cleanup(request: dict, _: dict = Depends(get_current_user)):
    """Analyze inbox and generate cleanup plan."""
    try:
        from email_analyzer import EmailAnalyzer
        
        connector_id = request.get('connector_id')
        limit = request.get('limit', 500)
        
        if not connector_id:
            raise HTTPException(status_code=400, detail="connector_id required")
        
        analyzer = EmailAnalyzer()
        analysis = analyzer.analyze_inbox(connector_id, limit)
        plan_id = analyzer.save_cleanup_plan(analysis)
        
        return {
            "success": True,
            "plan_id": plan_id,
            "summary": analysis['summary']
        }
    except Exception as e:
        logger.error(f"Email cleanup analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/cleanup/plans")
async def list_cleanup_plans(_: dict = Depends(get_current_user)):
    """List all cleanup plans."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, c.email_address, c.label 
            FROM email_cleanup_plans p
            LEFT JOIN email_connectors c ON p.account_id = c.id
            ORDER BY p.created_at DESC
        """)
        
        plans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"success": True, "plans": plans}
    except Exception as e:
        logger.error(f"Failed to list cleanup plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/cleanup/plans/{plan_id}")
async def get_cleanup_plan(plan_id: str, _: dict = Depends(get_current_user)):
    """Get cleanup plan details with categorized emails."""
    try:
        from email_analyzer import EmailAnalyzer
        
        analyzer = EmailAnalyzer()
        plan = analyzer.get_cleanup_plan(plan_id)
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return {"success": True, "plan": plan}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cleanup plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/email/cleanup/plans/{plan_id}/approve")
async def approve_cleanup_items(plan_id: str, request: dict, _: dict = Depends(get_current_user)):
    """Approve specific cleanup items."""
    try:
        item_ids = request.get('item_ids', [])
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="item_ids required")
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(item_ids))
        cursor.execute(f"""
            UPDATE email_cleanup_items 
            SET approved = 1
            WHERE id IN ({placeholders}) AND plan_id = ?
        """, (*item_ids, plan_id))
        
        conn.commit()
        updated = cursor.rowcount
        conn.close()
        
        return {
            "success": True,
            "updated": updated,
            "message": f"Approved {updated} items"
        }
    except Exception as e:
        logger.error(f"Failed to approve items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email/cleanup/plans/{plan_id}/execute")
async def execute_cleanup_plan(plan_id: str, background_tasks: BackgroundTasks, _: dict = Depends(get_current_user)):
    """Execute approved cleanup items."""
    try:
        from email_executor import EmailCleanupExecutor
        
        # Run cleanup in background
        executor = EmailCleanupExecutor()
        
        # Execute synchronously for now (can be async later)
        results = executor.execute_cleanup(plan_id)
        
        return {
            "success": True,
            "results": results,
            "message": f"Cleaned up {results.get('total', 0)} emails"
        }
    except Exception as e:
        logger.error(f"Failed to execute cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/cleanup/history")
async def get_cleanup_history(_: dict = Depends(get_current_user)):
    """Get cleanup execution history and statistics."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, c.email_address,
                   COUNT(i.id) as total_items,
                   SUM(CASE WHEN i.executed = 1 THEN 1 ELSE 0 END) as executed_items
            FROM email_cleanup_plans p
            LEFT JOIN email_connectors c ON p.account_id = c.id
            LEFT JOIN email_cleanup_items i ON p.id = i.plan_id
            WHERE p.status = 'executed'
            GROUP BY p.id
            ORDER BY p.executed_at DESC
            LIMIT 50
        """)
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"success": True, "history": history}
    except Exception as e:
        logger.error(f"Failed to get cleanup history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

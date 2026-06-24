from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.database import _db_connection, _now_iso

router = APIRouter()

@router.get("/prompt-templates")
async def list_prompt_templates(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all prompt templates, optionally filtered by category."""
    del current_user
    
    conn = _db_connection()
    try:
        if category:
            rows = conn.execute(
                "SELECT * FROM prompt_templates WHERE category = ? ORDER BY title ASC",
                (category,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM prompt_templates ORDER BY category, title ASC"
            ).fetchall()
        
        templates = []
        for row in rows:
            templates.append({
                "id": row["id"],
                "title": row["title"],
                "category": row["category"],
                "prompt_text": row["prompt_text"],
                "agent_id": row["agent_id"],
                "project_slug": row["project_slug"],
                "is_system": bool(row["is_system"]),
                "usage_count": row["usage_count"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        return templates
    finally:
        conn.close()


@router.post("/prompt-templates")
async def create_prompt_template(body: dict, current_user: dict = Depends(get_current_user)):
    """Create a new prompt template."""
    del current_user
    
    template_id = body.get("id", uuid.uuid4().hex)
    now = _now_iso()
    
    conn = _db_connection()
    try:
        conn.execute("""
            INSERT INTO prompt_templates 
            (id, title, category, prompt_text, agent_id, project_slug, is_system, usage_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template_id,
            body.get("title", "Untitled Template"),
            body.get("category", "general"),
            body.get("prompt_text", ""),
            body.get("agent_id", "inez"),
            body.get("project_slug", ""),
            0,  # user-created templates are never is_system
            0,  # initial usage_count
            now,
            now
        ))
        conn.commit()
        
        # Return the created template
        row = conn.execute(
            "SELECT * FROM prompt_templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        return {
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "prompt_text": row["prompt_text"],
            "agent_id": row["agent_id"],
            "project_slug": row["project_slug"],
            "is_system": bool(row["is_system"]),
            "usage_count": row["usage_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


@router.put("/prompt-templates/{template_id}")
async def update_prompt_template(
    template_id: str,
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing prompt template."""
    del current_user
    
    conn = _db_connection()
    try:
        # Check if template exists and is not system template
        row = conn.execute(
            "SELECT * FROM prompt_templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(404, "Template not found")
        
        if row["is_system"]:
            raise HTTPException(403, "Cannot modify system templates")
        
        # Update allowed fields
        now = _now_iso()
        conn.execute("""
            UPDATE prompt_templates
            SET title = ?,
                category = ?,
                prompt_text = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            body.get("title", row["title"]),
            body.get("category", row["category"]),
            body.get("prompt_text", row["prompt_text"]),
            now,
            template_id
        ))
        conn.commit()
        
        # Return updated template
        updated_row = conn.execute(
            "SELECT * FROM prompt_templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        return {
            "id": updated_row["id"],
            "title": updated_row["title"],
            "category": updated_row["category"],
            "prompt_text": updated_row["prompt_text"],
            "agent_id": updated_row["agent_id"],
            "project_slug": updated_row["project_slug"],
            "is_system": bool(updated_row["is_system"]),
            "usage_count": updated_row["usage_count"],
            "created_at": updated_row["created_at"],
            "updated_at": updated_row["updated_at"]
        }
    finally:
        conn.close()


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a prompt template (user-created only)."""
    del current_user
    
    conn = _db_connection()
    try:
        # Check if template exists and is not system template
        row = conn.execute(
            "SELECT * FROM prompt_templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(404, "Template not found")
        
        if row["is_system"]:
            raise HTTPException(403, "Cannot delete system templates")
        
        conn.execute("DELETE FROM prompt_templates WHERE id = ?", (template_id,))
        conn.commit()
        
        return {"success": True, "id": template_id}
    finally:
        conn.close()


@router.post("/prompt-templates/{template_id}/use")
async def use_prompt_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Increment usage count for a template and return its text."""
    del current_user
    
    conn = _db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM prompt_templates WHERE id = ?",
            (template_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(404, "Template not found")
        
        # Increment usage count
        conn.execute(
            "UPDATE prompt_templates SET usage_count = usage_count + 1 WHERE id = ?",
            (template_id,)
        ).fetchone()
        conn.commit()
        
        return {
            "id": row["id"],
            "title": row["title"],
            "prompt_text": row["prompt_text"],
            "usage_count": row["usage_count"] + 1
        }
    finally:
        conn.close()

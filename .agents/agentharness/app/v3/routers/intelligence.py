from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user

router = APIRouter()


@router.get("/intelligence/summary")
async def intelligence_summary(_: dict = Depends(get_current_user)):
    """Full PI system summary: skill levels, reflexion log, patterns."""
    try:
        import progressive_intelligence as pi
        return {"success": True, **pi.get_intelligence_summary()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/skills")
async def intelligence_skills(_: dict = Depends(get_current_user)):
    """Per-agent skill levels and run stats."""
    try:
        import progressive_intelligence as pi
        summary = pi.get_intelligence_summary()
        return {"success": True, "skills": summary.get("agent_skill_levels", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/patterns")
async def intelligence_patterns(_: dict = Depends(get_current_user)):
    """Detected interaction patterns and proactive suggestions."""
    try:
        import progressive_intelligence as pi
        return {"success": True, "patterns": pi.detect_patterns(), "suggestions": pi.get_proactive_suggestions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/agent/{agent_id}")
async def intelligence_agent(agent_id: str, _: dict = Depends(get_current_user)):
    """Skill stats for a specific agent."""
    try:
        import progressive_intelligence as pi
        return {"success": True, **pi.get_skill_stats(agent_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



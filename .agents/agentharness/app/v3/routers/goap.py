"""GOAP planner API endpoint."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user

router = APIRouter(prefix="/goap", tags=["goap"])


class PlanRequest(BaseModel):
    goal: str
    project: str
    write_to_inbox: bool = True


class PlanResponse(BaseModel):
    plan_id: str
    goal: str
    project: str
    steps: list[dict[str, Any]]
    complexity: str
    inbox_path: str = ""


@router.post("/plan", response_model=PlanResponse)
async def create_plan(req: PlanRequest, user: dict = Depends(get_current_user)):
    del user
    try:
        from goap_planner import plan_from_goal, write_plan_to_inbox

        plan = plan_from_goal(req.goal, req.project)
        inbox_path = ""
        if req.write_to_inbox:
            inbox_path = str(write_plan_to_inbox(plan, req.project))
        return PlanResponse(
            plan_id=plan["plan_id"],
            goal=plan["goal"],
            project=plan["project"],
            steps=plan["steps"],
            complexity=plan["complexity"],
            inbox_path=inbox_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth import get_current_user
from core.database import _append_plan_event, _get_plan_events, _list_plans, _load_plan, _now_iso, _save_plan

try:
    from core.plan_schema import make_edge, make_node, make_plan
    from core.plan_preflight import run_preflight

    PLAN_OK = True
except ImportError:
    PLAN_OK = False

try:
    from core.plan_executor import LANGGRAPH_OK, compile_plan_to_langgraph, initial_plan_execution_state
except ImportError:
    LANGGRAPH_OK = False

    def compile_plan_to_langgraph(*_args, **_kwargs):  # type: ignore[misc]
        raise RuntimeError("plan_executor not available")

    def initial_plan_execution_state(*_args, **_kwargs):  # type: ignore[misc]
        raise RuntimeError("plan_executor not available")

try:
    from core.hub import hub
except ImportError:
    hub = None  # type: ignore[assignment]

try:
    from ah_logging import get_logger
except ImportError:
    import logging

    def get_logger(name):
        return logging.getLogger(f"archonhub.{name}")


logger = get_logger("plans")
router = APIRouter()


class NodeBody(BaseModel):
    id: str
    label: str
    role: str = "work"
    purpose: str
    context: str = ""
    agent_id: str = "human"
    allowed_scope: list[str] = []
    depends_on: list[str] = []
    entry_criteria: list[str] = []
    exit_criteria: list[str] = []
    expected_evidence: list[str] = []
    on_fail: str = "block"
    retry_limit: int = 1


class EdgeBody(BaseModel):
    from_node: str
    to_node: str
    kind: str = "sequence"
    condition: Optional[str] = None
    parallel_group: Optional[str] = None
    handoff_context: Optional[str] = None


class CreatePlanBody(BaseModel):
    title: str
    objective: str
    project: str = ""
    constraints: list[str] = []
    nodes: list[NodeBody]
    edges: list[EdgeBody] = []
    entry_node: Optional[str] = None
    tags: list[str] = []


class PatchPlanBody(BaseModel):
    title: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list[str]] = None


@router.post("/plans")
async def create_plan(body: CreatePlanBody, current_user: dict = Depends(get_current_user)):
    if not PLAN_OK:
        raise HTTPException(503, "plan_schema module not available")
    nodes = []
    for node in body.nodes:
        nodes.append(
            {
                "id": node.id,
                "label": node.label,
                "role": node.role,
                "purpose": node.purpose,
                "context": node.context,
                "agent_id": node.agent_id,
                "allowed_scope": node.allowed_scope,
                "depends_on": node.depends_on,
                "entry_criteria": node.entry_criteria,
                "exit_criteria": node.exit_criteria,
                "expected_evidence": node.expected_evidence,
                "on_fail": node.on_fail,
                "retry_limit": node.retry_limit,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "assigned_run_id": None,
                "evidence": [],
                "blocked_reason": None,
                "drift_notes": None,
                "attempt": 0,
            }
        )
    edges = []
    for edge in body.edges:
        edges.append(
            {
                "id": f"{edge.from_node}__{edge.to_node}",
                "from_node": edge.from_node,
                "to_node": edge.to_node,
                "kind": edge.kind,
                "condition": edge.condition,
                "parallel_group": edge.parallel_group,
                "handoff_context": edge.handoff_context,
            }
        )
    entry = body.entry_node or (nodes[0]["id"] if nodes else "")
    plan = {
        "plan_id": uuid.uuid4().hex,
        "title": body.title,
        "version": 1,
        "authored_by": current_user.get("username", "human"),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "objective": body.objective,
        "project": body.project,
        "constraints": body.constraints,
        "nodes": nodes,
        "edges": edges,
        "entry_node": entry,
        "status": "draft",
        "preflight_report": None,
        "run_id": None,
        "tags": body.tags,
        "completed_at": None,
        "abandoned_reason": None,
    }
    saved = _save_plan(plan)
    _append_plan_event(plan["plan_id"], None, "plan.created", {"title": body.title, "authored_by": plan["authored_by"]})
    if hub:
        try:
            await hub.broadcast({"type": "plan.created", "plan_id": plan["plan_id"], "title": body.title})
        except Exception:
            logger.exception("Unable to broadcast plan.created")
    return {"success": True, "plan": saved}


@router.get("/plans")
async def list_plans(
    project: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    return {"plans": _list_plans(project=project, status=status, limit=limit)}


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str, _: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return {"plan": plan}


@router.patch("/plans/{plan_id}")
async def patch_plan(plan_id: str, body: PatchPlanBody, _: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if body.title is not None:
        plan["title"] = body.title
    if body.objective is not None:
        plan["objective"] = body.objective
    if body.status is not None:
        plan["status"] = body.status
    if body.tags is not None:
        plan["tags"] = body.tags
    _save_plan(plan)
    return {"success": True, "plan": plan}


@router.post("/plans/{plan_id}/preflight")
async def preflight_plan(plan_id: str, _: dict = Depends(get_current_user)):
    if not PLAN_OK:
        raise HTTPException(503, "plan_schema/preflight module not available")
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    plan["status"] = "preflight_pending"
    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.preflight.start", {})
    if hub:
        try:
            await hub.broadcast({"type": "plan.preflight.start", "plan_id": plan_id})
        except Exception:
            logger.exception("Unable to broadcast plan.preflight.start")
    report = run_preflight(plan)  # type: ignore[arg-type]
    plan["preflight_report"] = dict(report)
    plan["status"] = "preflight_passed" if report["passed"] else "draft"
    _save_plan(plan)
    _append_plan_event(
        plan_id,
        None,
        "plan.preflight.done",
        {"passed": report["passed"], "issue_count": len(report["issues"])},
    )
    if hub:
        try:
            await hub.broadcast(
                {
                    "type": "plan.preflight.done",
                    "plan_id": plan_id,
                    "passed": report["passed"],
                    "issue_count": len(report["issues"]),
                }
            )
        except Exception:
            logger.exception("Unable to broadcast plan.preflight.done")
    return {"success": True, "report": report, "plan_status": plan["status"]}


@router.post("/plans/{plan_id}/approve")
async def approve_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.get("status") not in ("preflight_passed", "draft"):
        raise HTTPException(400, f"Cannot approve a plan in status '{plan['status']}' — run preflight first")
    plan["status"] = "approved"
    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.approved", {"approved_by": current_user.get("username", "human")})
    if hub:
        try:
            await hub.broadcast(
                {"type": "plan.approved", "plan_id": plan_id, "approved_by": current_user.get("username")}
            )
        except Exception:
            logger.exception("Unable to broadcast plan.approved")
    return {"success": True, "plan_id": plan_id, "status": "approved"}


@router.post("/plans/{plan_id}/execute")
async def execute_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.get("status") != "approved":
        raise HTTPException(400, f"Plan must be approved before execution (current: {plan['status']})")
    if not hub:
        raise HTTPException(503, "Hub not available")

    run_id = uuid.uuid4().hex
    plan["status"] = "running"
    plan["run_id"] = run_id
    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.execution.start", {"run_id": run_id, "requested_by": current_user.get("username", "human")})

    await hub.submit_job(
        {
            "run_id": run_id,
            "agent_id": plan.get("authored_by", "human"),
            "project": plan.get("project", ""),
            "task": f"Execute implementation plan: {plan['title']}",
            "graph": "plan",
            "plan_id": plan_id,
            "priority": "normal",
            "max_revisions": 0,
        }
    )

    return {"success": True, "plan_id": plan_id, "run_id": run_id}


@router.post("/plans/{plan_id}/abandon")
async def abandon_plan(plan_id: str, reason: str = Query(""), _: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    plan["status"] = "abandoned"
    plan["abandoned_reason"] = reason
    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.abandoned", {"reason": reason})
    if hub:
        try:
            await hub.broadcast({"type": "plan.abandoned", "plan_id": plan_id, "reason": reason})
        except Exception:
            logger.exception("Unable to broadcast plan.abandoned")
    return {"success": True}


@router.get("/plans/{plan_id}/events")
async def get_events(plan_id: str, limit: int = Query(200, ge=1, le=500), _: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return {"plan_id": plan_id, "events": _get_plan_events(plan_id, limit=limit)}

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


def _create_notification(text: str, color: str = "#2d84ff", category: str = "system", **kwargs) -> None:
    """Create a notification record, silently ignoring errors."""
    try:
        from core.database import _db_connection, _now_iso as _n
        conn = _db_connection()
        with conn:
            conn.execute(
                "INSERT INTO notifications (text, color, category, created_at, read) VALUES (?,?,?,?,0)",
                (text, color, category, _n())
            )
    except Exception:
        pass


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


class ProposeDriftBody(BaseModel):
    drift_notes: str
    new_nodes: list[NodeBody] = []
    new_edges: list[EdgeBody] = []


class DriftReviewBody(BaseModel):
    rejection_reason: str = ""


class YAMLPlanBody(BaseModel):
    yaml_text: str


class NodeRespondBody(BaseModel):
    decision: str
    notes: str = ""


@router.post("/plans/from-yaml")
async def create_plan_from_yaml(body: YAMLPlanBody, current_user: dict = Depends(get_current_user)):
    """
    Create a plan from a compact YAML definition.

    Supported YAML schema:
      title: Plan title
      objective: What this achieves
      project: project-slug
      constraints: [list of constraints]  # optional
      tags: [list of tags]               # optional
      nodes:
        - id: step1
          label: Human-readable name
          purpose: What this step achieves
          agent: agent-id               # defaults to "human"
          role: work                    # optional: work|review|decision|milestone|human_gate
          deps: [dep1, dep2]            # optional: depends_on
          exit: [criterion 1, ...]      # optional: exit_criteria
          evidence: [artifact 1, ...]   # optional: expected_evidence
          scope: [action1, ...]         # optional: allowed_scope
          on_fail: block                # optional: block|skip|retry|escalate_human
      edges:                            # optional — auto-generated from deps if omitted
        - from: step1
          to: step2
          kind: sequence               # optional, default: sequence
    """
    try:
        import yaml as _yaml
    except ImportError:
        raise HTTPException(503, "PyYAML not installed — run: pip install pyyaml")

    try:
        data = _yaml.safe_load(body.yaml_text)
    except Exception as exc:
        raise HTTPException(400, f"YAML parse error: {exc}")

    if not isinstance(data, dict):
        raise HTTPException(400, "YAML must be a mapping at the top level")

    title = str(data.get("title", "")).strip()
    objective = str(data.get("objective", "")).strip()
    if not title or not objective:
        raise HTTPException(400, "YAML must include 'title' and 'objective'")

    raw_nodes = data.get("nodes", [])
    if not raw_nodes:
        raise HTTPException(400, "YAML must include at least one node")

    nodes = []
    for n in raw_nodes:
        if not isinstance(n, dict):
            raise HTTPException(400, f"Each node must be a mapping, got: {n}")
        node_id = str(n.get("id", "")).strip()
        if not node_id:
            raise HTTPException(400, "Each node must have an 'id'")
        nodes.append({
            "id": node_id,
            "label": str(n.get("label", node_id)),
            "role": str(n.get("role", "work")),
            "purpose": str(n.get("purpose", "")),
            "context": str(n.get("context", "")),
            "agent_id": str(n.get("agent", n.get("agent_id", "human"))),
            "allowed_scope": list(n.get("scope", n.get("allowed_scope", []))),
            "depends_on": list(n.get("deps", n.get("depends_on", []))),
            "entry_criteria": list(n.get("entry", n.get("entry_criteria", []))),
            "exit_criteria": list(n.get("exit", n.get("exit_criteria", []))),
            "expected_evidence": list(n.get("evidence", n.get("expected_evidence", []))),
            "on_fail": str(n.get("on_fail", "block")),
            "retry_limit": int(n.get("retry_limit", 1)),
            "status": "pending", "started_at": None, "completed_at": None,
            "assigned_run_id": None, "evidence": [], "blocked_reason": None,
            "drift_notes": None, "attempt": 0,
        })

    raw_edges = data.get("edges", [])
    edges = []
    if raw_edges:
        for e in raw_edges:
            edges.append({
                "id": f"{e.get('from')}__{e.get('to')}",
                "from_node": str(e.get("from", "")),
                "to_node": str(e.get("to", "")),
                "kind": str(e.get("kind", "sequence")),
                "condition": e.get("condition"),
                "parallel_group": e.get("parallel_group"),
                "handoff_context": e.get("handoff_context"),
            })
    else:
        node_ids = {n["id"] for n in nodes}
        for node in nodes:
            for dep in node.get("depends_on", []):
                if dep in node_ids:
                    edges.append({
                        "id": f"{dep}__{node['id']}",
                        "from_node": dep, "to_node": node["id"],
                        "kind": "dependency",
                        "condition": None, "parallel_group": None, "handoff_context": None,
                    })

    entry = nodes[0]["id"] if nodes else ""
    plan = {
        "plan_id": uuid.uuid4().hex,
        "title": title, "version": 1,
        "authored_by": current_user.get("username", "human"),
        "created_at": _now_iso(), "updated_at": _now_iso(),
        "objective": objective,
        "project": str(data.get("project", "")),
        "constraints": list(data.get("constraints", [])),
        "nodes": nodes, "edges": edges, "entry_node": entry,
        "status": "draft",
        "preflight_report": None, "run_id": None,
        "tags": list(data.get("tags", [])),
        "completed_at": None, "abandoned_reason": None,
        "drift_proposals": [], "current_drift_proposal_id": None,
    }
    saved = _save_plan(plan)
    _append_plan_event(plan["plan_id"], None, "plan.created", {
        "title": title, "authored_by": plan["authored_by"], "source": "yaml"
    })
    if hub:
        try:
            await hub.broadcast({"type": "plan.created", "plan_id": plan["plan_id"], "title": title})
        except Exception:
            pass
    return {"success": True, "plan": saved}


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
        "drift_proposals": [],
        "current_drift_proposal_id": None,
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


@router.post("/plans/{plan_id}/propose-drift")
async def propose_drift(plan_id: str, body: ProposeDriftBody, current_user: dict = Depends(get_current_user)):
    """Agent proposes a drift — execution pauses, human notified."""
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.get("status") not in ("running", "approved"):
        raise HTTPException(400, f"Cannot propose drift for a plan in status '{plan['status']}'")

    proposal_id = uuid.uuid4().hex
    now = _now_iso()

    new_nodes = []
    for n in body.new_nodes:
        new_nodes.append({
            "id": n.id, "label": n.label, "role": n.role, "purpose": n.purpose,
            "context": n.context, "agent_id": n.agent_id, "allowed_scope": n.allowed_scope,
            "depends_on": n.depends_on, "entry_criteria": n.entry_criteria,
            "exit_criteria": n.exit_criteria, "expected_evidence": n.expected_evidence,
            "on_fail": n.on_fail, "retry_limit": n.retry_limit,
            "status": "pending", "started_at": None, "completed_at": None,
            "assigned_run_id": None, "evidence": [], "blocked_reason": None,
            "drift_notes": None, "attempt": 0,
        })
    new_edges = []
    for e in body.new_edges:
        new_edges.append({
            "id": f"{e.from_node}__{e.to_node}", "from_node": e.from_node, "to_node": e.to_node,
            "kind": e.kind, "condition": e.condition, "parallel_group": e.parallel_group,
            "handoff_context": e.handoff_context,
        })

    proposal = {
        "proposal_id": proposal_id,
        "proposed_by": current_user.get("username", "agent"),
        "proposed_at": now,
        "drift_notes": body.drift_notes,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
        "status": "pending",
        "reviewed_by": None,
        "reviewed_at": None,
        "rejection_reason": None,
    }

    plan.setdefault("drift_proposals", [])
    plan["drift_proposals"].append(proposal)
    plan["current_drift_proposal_id"] = proposal_id
    plan["status"] = "drift_pending"
    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.drift.proposed", {"proposal_id": proposal_id, "notes": body.drift_notes[:200]})

    _create_notification(
        text=f"Plan drift proposed: \"{plan['title']}\" — {body.drift_notes[:120]}",
        color="#f59e0b",
        category="plan_drift",
        plan_id=plan_id,
        proposal_id=proposal_id,
    )

    if hub:
        try:
            await hub.broadcast({"type": "plan.drift.proposed", "plan_id": plan_id, "proposal_id": proposal_id})
        except Exception:
            pass

    return {"success": True, "proposal_id": proposal_id, "status": "drift_pending"}


@router.post("/plans/{plan_id}/drift/approve")
async def approve_drift(plan_id: str, current_user: dict = Depends(get_current_user)):
    """Human approves a pending drift proposal. Adds new nodes/edges, bumps version, re-preflights."""
    if not PLAN_OK:
        raise HTTPException(503, "plan modules not available")
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.get("status") != "drift_pending":
        raise HTTPException(400, "No pending drift proposal")

    proposal_id = plan.get("current_drift_proposal_id")
    proposal = next((p for p in plan.get("drift_proposals", []) if p["proposal_id"] == proposal_id), None)
    if not proposal:
        raise HTTPException(404, "Drift proposal not found")

    now = _now_iso()
    proposal["status"] = "approved"
    proposal["reviewed_by"] = current_user.get("username", "human")
    proposal["reviewed_at"] = now

    plan["nodes"] = plan.get("nodes", []) + proposal.get("new_nodes", [])
    plan["edges"] = plan.get("edges", []) + proposal.get("new_edges", [])
    plan["version"] = plan.get("version", 1) + 1
    plan["current_drift_proposal_id"] = None
    plan["status"] = "running"
    plan["updated_at"] = now

    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.drift.approved", {"proposal_id": proposal_id, "new_version": plan["version"]})

    if hub:
        try:
            await hub.broadcast({"type": "plan.drift.approved", "plan_id": plan_id, "version": plan["version"]})
        except Exception:
            pass

    return {"success": True, "new_version": plan["version"], "nodes_added": len(proposal.get("new_nodes", []))}


@router.post("/plans/{plan_id}/drift/reject")
async def reject_drift(plan_id: str, body: DriftReviewBody, current_user: dict = Depends(get_current_user)):
    """Human rejects a pending drift proposal. Execution resumes with original plan."""
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if plan.get("status") != "drift_pending":
        raise HTTPException(400, "No pending drift proposal")

    proposal_id = plan.get("current_drift_proposal_id")
    proposal = next((p for p in plan.get("drift_proposals", []) if p["proposal_id"] == proposal_id), None)
    if proposal:
        proposal["status"] = "rejected"
        proposal["reviewed_by"] = current_user.get("username", "human")
        proposal["reviewed_at"] = _now_iso()
        proposal["rejection_reason"] = body.rejection_reason

    plan["current_drift_proposal_id"] = None
    plan["status"] = "running"
    _save_plan(plan)
    _append_plan_event(plan_id, None, "plan.drift.rejected", {"proposal_id": proposal_id, "reason": body.rejection_reason})

    if hub:
        try:
            await hub.broadcast({"type": "plan.drift.rejected", "plan_id": plan_id, "reason": body.rejection_reason})
        except Exception:
            pass

    return {"success": True}


@router.get("/plans/{plan_id}/events")
async def get_events(plan_id: str, limit: int = Query(200, ge=1, le=500), _: dict = Depends(get_current_user)):
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    return {"plan_id": plan_id, "events": _get_plan_events(plan_id, limit=limit)}


@router.post("/plans/{plan_id}/nodes/{node_id}/respond")
async def respond_to_node(plan_id: str, node_id: str, body: NodeRespondBody,
                          current_user: dict = Depends(get_current_user)):
    """Human responds to a human_gate or blocked node."""
    plan = _load_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    node = next((n for n in plan.get("nodes", []) if n["id"] == node_id), None)
    if not node:
        raise HTTPException(404, f"Node '{node_id}' not found")

    now = _now_iso()
    if body.decision == "approve":
        node["status"] = "done"
        node["completed_at"] = now
        node["evidence"] = node.get("evidence", []) + [{
            "id": uuid.uuid4().hex[:8],
            "type": "human_decision",
            "content": f"Approved by {current_user.get('username', 'human')}: {body.notes}",
            "source": "human",
            "timestamp": now,
            "ref": None,
        }]
    else:
        node["status"] = "blocked"
        node["blocked_reason"] = f"Rejected by {current_user.get('username', 'human')}: {body.notes}"

    _save_plan(plan)
    _append_plan_event(plan_id, node_id, f"plan.node.{body.decision}", {
        "decision": body.decision, "notes": body.notes,
        "by": current_user.get("username", "human"),
    })
    if hub:
        try:
            await hub.broadcast({
                "type": f"plan.node.{'done' if body.decision == 'approve' else 'blocked'}",
                "plan_id": plan_id, "node_id": node_id,
            })
        except Exception:
            pass
    return {"success": True, "node_id": node_id, "status": node["status"]}

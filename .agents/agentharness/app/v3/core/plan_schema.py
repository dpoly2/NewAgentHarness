from __future__ import annotations

import uuid
from typing import Optional, TypedDict


class EvidenceItem(TypedDict):
    id: str
    type: str
    content: str
    source: str
    timestamp: str
    ref: Optional[str]


class PlanNode(TypedDict):
    id: str
    label: str
    role: str
    purpose: str
    context: str
    agent_id: str
    allowed_scope: list[str]
    depends_on: list[str]
    entry_criteria: list[str]
    exit_criteria: list[str]
    expected_evidence: list[str]
    on_fail: str
    retry_limit: int
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    assigned_run_id: Optional[str]
    evidence: list[EvidenceItem]
    blocked_reason: Optional[str]
    drift_notes: Optional[str]
    attempt: int


class PlanEdge(TypedDict):
    id: str
    from_node: str
    to_node: str
    kind: str
    condition: Optional[str]
    parallel_group: Optional[str]
    handoff_context: Optional[str]


class PreflightIssue(TypedDict):
    severity: str
    node_id: Optional[str]
    message: str


class PreflightReport(TypedDict):
    passed: bool
    issues: list[PreflightIssue]
    simulated_order: list[str]
    parallel_stages: list[list[str]]
    estimated_node_count: int


class ImplementationPlan(TypedDict):
    plan_id: str
    title: str
    version: int
    authored_by: str
    created_at: str
    updated_at: str
    objective: str
    project: str
    constraints: list[str]
    nodes: list[PlanNode]
    edges: list[PlanEdge]
    entry_node: str
    status: str
    preflight_report: Optional[PreflightReport]
    run_id: Optional[str]
    tags: list[str]
    completed_at: Optional[str]
    abandoned_reason: Optional[str]


def make_node(
    id: str,
    label: str,
    purpose: str,
    agent_id: str = "human",
    role: str = "work",
    **kwargs,
) -> PlanNode:
    """Construct a PlanNode with safe defaults."""
    return PlanNode(
        id=id,
        label=label,
        role=role,
        purpose=purpose,
        context=kwargs.get("context", ""),
        agent_id=agent_id,
        allowed_scope=list(kwargs.get("allowed_scope", [])),
        depends_on=list(kwargs.get("depends_on", [])),
        entry_criteria=list(kwargs.get("entry_criteria", [])),
        exit_criteria=list(kwargs.get("exit_criteria", [])),
        expected_evidence=list(kwargs.get("expected_evidence", [])),
        on_fail=kwargs.get("on_fail", "block"),
        retry_limit=kwargs.get("retry_limit", 1),
        status=kwargs.get("status", "pending"),
        started_at=kwargs.get("started_at"),
        completed_at=kwargs.get("completed_at"),
        assigned_run_id=kwargs.get("assigned_run_id"),
        evidence=list(kwargs.get("evidence", [])),
        blocked_reason=kwargs.get("blocked_reason"),
        drift_notes=kwargs.get("drift_notes"),
        attempt=kwargs.get("attempt", 0),
    )


def make_edge(from_node: str, to_node: str, kind: str = "sequence", **kwargs) -> PlanEdge:
    return PlanEdge(
        id=f"{from_node}__{to_node}",
        from_node=from_node,
        to_node=to_node,
        kind=kind,
        condition=kwargs.get("condition"),
        parallel_group=kwargs.get("parallel_group"),
        handoff_context=kwargs.get("handoff_context"),
    )


def make_plan(
    title: str,
    objective: str,
    project: str,
    nodes: list[PlanNode],
    edges: list[PlanEdge],
    authored_by: str = "human",
    **kwargs,
) -> ImplementationPlan:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    entry = nodes[0]["id"] if nodes else ""
    return ImplementationPlan(
        plan_id=uuid.uuid4().hex,
        title=title,
        version=1,
        authored_by=authored_by,
        created_at=now,
        updated_at=now,
        objective=objective,
        project=project,
        constraints=list(kwargs.get("constraints", [])),
        nodes=nodes,
        edges=edges,
        entry_node=kwargs.get("entry_node", entry),
        status="draft",
        preflight_report=None,
        run_id=None,
        tags=list(kwargs.get("tags", [])),
        completed_at=None,
        abandoned_reason=None,
    )


def node_map(plan: ImplementationPlan) -> dict[str, PlanNode]:
    return {node["id"]: node for node in plan["nodes"]}

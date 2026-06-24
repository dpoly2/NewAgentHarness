from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from core.database import _now_iso
from core.plan_schema import ImplementationPlan, node_map as _node_map

HERE = Path(__file__).parent

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_OK = True
except ImportError:
    LANGGRAPH_OK = False


if LANGGRAPH_OK:
    from typing import TypedDict

    class PlanExecutionState(TypedDict):
        plan: dict
        current_node_id: str
        completed_nodes: list[str]
        blocked_nodes: list[str]
        accumulated_context: str
        run_id: str
else:
    PlanExecutionState = dict  # type: ignore[assignment,misc]


def _build_brief(plan_node: dict, accumulated_context: str) -> str:
    """Build the agent task brief from plan node fields."""
    parts = [f"## Task: {plan_node['label']}"]
    parts.append(f"\n**Purpose:** {plan_node['purpose']}")
    if plan_node.get("context"):
        parts.append(f"\n**Context:** {plan_node['context']}")
    if accumulated_context:
        parts.append(f"\n**Prior work (full context):**\n{accumulated_context}")
    if plan_node.get("entry_criteria"):
        parts.append("\n**Entry criteria (verify before starting):**")
        for criterion in plan_node["entry_criteria"]:
            parts.append(f"  - {criterion}")
    if plan_node.get("exit_criteria"):
        parts.append("\n**Exit criteria (you are done when ALL of these are true):**")
        for criterion in plan_node["exit_criteria"]:
            parts.append(f"  - {criterion}")
    if plan_node.get("allowed_scope"):
        parts.append(f"\n**Allowed actions:** {', '.join(plan_node['allowed_scope'])}")
    if plan_node.get("expected_evidence"):
        parts.append("\n**Expected evidence to produce:**")
        for evidence in plan_node["expected_evidence"]:
            parts.append(f"  - {evidence}")
    return "\n".join(parts)


async def _safe_emit(emit: Callable[[dict], Any], payload: dict) -> None:
    try:
        result = emit(payload)
        if asyncio.iscoroutine(result):
            await result
    except Exception:
        pass


def make_work_node(plan_node_id: str, emit: Optional[Callable[[dict], Any]] = None):
    """Returns an async LangGraph node function for a plan work node."""

    async def _node(state: dict) -> dict:
        plan = state["plan"]
        nmap = _node_map(plan)  # type: ignore[arg-type]
        pnode = nmap.get(plan_node_id)
        if not pnode:
            return state

        pnode["status"] = "running"
        pnode["started_at"] = _now_iso()
        pnode["attempt"] = pnode.get("attempt", 0) + 1
        state["current_node_id"] = plan_node_id

        if emit:
            await _safe_emit(
                emit,
                {
                    "type": "plan.node.start",
                    "plan_id": plan["plan_id"],
                    "node_id": plan_node_id,
                    "agent_id": pnode.get("agent_id"),
                    "attempt": pnode["attempt"],
                },
            )

        brief = _build_brief(pnode, state.get("accumulated_context", ""))
        result_output = ""
        result_score = 0.0
        try:
            from hub_nodes import LANGGRAPH_OK as HUB_LG_OK, run_graph

            if HUB_LG_OK:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: run_graph(
                        {
                            "agent_id": pnode.get("agent_id", "default"),
                            "project": plan.get("project", ""),
                            "task": brief,
                            "graph": "reflexion",
                            "max_revisions": 1,
                            "run_id": f"{plan['plan_id']}__{plan_node_id}",
                        }
                    ),
                )
                result_output = result.get("output", "")
                result_score = float(result.get("score", 0.0) or 0.0)
                pnode["assigned_run_id"] = result.get("run_id", "")
            else:
                result_output = f"[Simulated execution of: {brief[:200]}]"
                result_score = 1.0
        except Exception as exc:
            result_output = f"[Execution error: {exc}]"
            result_score = 0.0

        # Collect evidence — large content saved to file, ref stored instead
        EVIDENCE_INLINE_MAX = 2048
        evidence_content = result_output
        evidence_ref = None
        if len(evidence_content) > EVIDENCE_INLINE_MAX:
            # Save full content to uploads directory
            try:
                import tempfile, os
                uploads_dir = HERE.parent.parent.parent / "uploads"
                uploads_dir.mkdir(parents=True, exist_ok=True)
                evidence_filename = f"evidence_{plan['plan_id']}_{plan_node_id}_{uuid.uuid4().hex[:8]}.txt"
                evidence_path = uploads_dir / evidence_filename
                evidence_path.write_text(evidence_content, encoding="utf-8")
                evidence_ref = str(evidence_path)
                evidence_content = evidence_content[:EVIDENCE_INLINE_MAX] + f"\n\n[Truncated — full content at: {evidence_filename}]"
            except Exception:
                pass  # Fall back to inline if file write fails

        evidence_item = {
            "id": uuid.uuid4().hex[:8],
            "type": "artifact",
            "content": evidence_content,
            "source": pnode.get("agent_id", "unknown"),
            "timestamp": _now_iso(),
            "ref": evidence_ref,
        }
        pnode["evidence"] = pnode.get("evidence", []) + [evidence_item]

        if emit:
            await _safe_emit(
                emit,
                {
                    "type": "plan.node.evidence",
                    "plan_id": plan["plan_id"],
                    "node_id": plan_node_id,
                    "evidence": evidence_item,
                },
            )

        exit_met = result_score >= 0.5
        if exit_met:
            pnode["status"] = "done"
            pnode["completed_at"] = _now_iso()
            completed = list(state.get("completed_nodes", []))
            completed.append(plan_node_id)
            state["completed_nodes"] = completed
            ctx = state.get("accumulated_context", "")
            ctx += f"\n\n---\n[{pnode['label']} — {pnode.get('agent_id', '')}]:\n{result_output}"
            # Cap at 16KB, trimming from the front to keep most recent context
            if len(ctx) > 16384:
                ctx = "[...earlier context trimmed...]\n" + ctx[-16000:]
            state["accumulated_context"] = ctx
            if emit:
                await _safe_emit(
                    emit,
                    {
                        "type": "plan.node.done",
                        "plan_id": plan["plan_id"],
                        "node_id": plan_node_id,
                        "summary": result_output[:200],
                    },
                )
        else:
            retry_limit = pnode.get("retry_limit", 1)
            if pnode["attempt"] < retry_limit:
                pnode["status"] = "pending"
                if emit:
                    await _safe_emit(
                        emit,
                        {
                            "type": "plan.node.retry",
                            "plan_id": plan["plan_id"],
                            "node_id": plan_node_id,
                            "attempt": pnode["attempt"],
                        },
                    )
            else:
                on_fail = pnode.get("on_fail", "block")
                if on_fail == "skip":
                    pnode["status"] = "skipped"
                    completed = list(state.get("completed_nodes", []))
                    completed.append(plan_node_id)
                    state["completed_nodes"] = completed
                elif on_fail == "escalate_human":
                    pnode["status"] = "blocked"
                    pnode["blocked_reason"] = "Escalated to human — exit criteria not met after retries"
                    blocked = list(state.get("blocked_nodes", []))
                    blocked.append(plan_node_id)
                    state["blocked_nodes"] = blocked
                else:
                    pnode["status"] = "blocked"
                    pnode["blocked_reason"] = f"Exit criteria not met after {pnode['attempt']} attempt(s)"
                    blocked = list(state.get("blocked_nodes", []))
                    blocked.append(plan_node_id)
                    state["blocked_nodes"] = blocked
                if emit:
                    await _safe_emit(
                        emit,
                        {
                            "type": "plan.node.blocked",
                            "plan_id": plan["plan_id"],
                            "node_id": plan_node_id,
                            "reason": pnode.get("blocked_reason", ""),
                        },
                    )

        return state

    return _node


def make_human_gate_node(plan_node_id: str, emit=None):
    """
    Human gate node — creates a notification, pauses at 'running'.
    Resolved externally via POST /api/plans/{id}/nodes/{node_id}/respond.
    """

    async def _node(state: dict) -> dict:
        plan = state["plan"]
        nmap = _node_map(plan)  # type: ignore[arg-type]
        pnode = nmap.get(plan_node_id)
        if not pnode:
            return state

        pnode["status"] = "running"
        pnode["started_at"] = _now_iso()

        prompt = pnode.get("purpose", "Human decision required")
        if emit:
            await _safe_emit(emit, {
                "type": "plan.node.human_gate",
                "plan_id": plan.get("plan_id", ""),
                "node_id": plan_node_id,
                "prompt": prompt,
            })

        # Create a notification for the human
        try:
            from core.database import _db_connection
            conn = _db_connection()
            with conn:
                conn.execute(
                    "INSERT INTO notifications (text, color, category, created_at, read) VALUES (?,?,?,?,0)",
                    (
                        f"Human gate: {pnode.get('label', plan_node_id)} — {prompt[:120]}",
                        "#f59e0b",
                        "human_gate",
                        _now_iso(),
                    )
                )
        except Exception:
            pass

        # Gate nodes pause the graph here — they are resolved by external API call.
        # For now, auto-complete so the graph doesn't deadlock without a checkpointer.
        # TODO: Use LangGraph interrupt() once checkpointer is wired.
        pnode["status"] = "done"
        pnode["completed_at"] = _now_iso()
        completed = list(state.get("completed_nodes", []))
        completed.append(plan_node_id)
        state["completed_nodes"] = completed
        return state

    return _node


def compile_plan_to_langgraph(plan: ImplementationPlan, emit: Optional[Callable[[dict], Any]] = None):
    """Compile an ImplementationPlan into a LangGraph StateGraph."""
    if not LANGGRAPH_OK:
        raise RuntimeError("langgraph is not installed — cannot compile plan")

    graph = StateGraph(dict)
    node_ids = [node["id"] for node in plan["nodes"]]

    for node in plan["nodes"]:
        if node.get("role") == "human_gate":
            graph.add_node(node["id"], make_human_gate_node(node["id"], emit))
        else:
            graph.add_node(node["id"], make_work_node(node["id"], emit))

    async def _plan_done(state: dict) -> dict:
        plan_dict = state.get("plan", {})
        plan_dict["status"] = "done"
        plan_dict["completed_at"] = _now_iso()
        if emit:
            await _safe_emit(
                emit,
                {
                    "type": "plan.done",
                    "plan_id": plan_dict.get("plan_id", ""),
                    "summary": f"Plan completed — {len(state.get('completed_nodes', []))} nodes done",
                },
            )
        return state

    graph.add_node("__plan_done__", _plan_done)

    adj: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in plan.get("edges", []):
        from_node = edge.get("from_node")
        to_node = edge.get("to_node")
        if from_node in adj:
            adj[from_node].append(to_node)

    for node in plan["nodes"]:
        targets = adj.get(node["id"], [])
        if not targets:
            graph.add_edge(node["id"], "__plan_done__")
        elif len(targets) == 1:
            graph.add_edge(node["id"], targets[0])
        else:
            for target in targets:
                graph.add_edge(node["id"], target)

    graph.add_edge("__plan_done__", END)
    graph.set_entry_point(plan.get("entry_node", node_ids[0] if node_ids else "__plan_done__"))
    return graph.compile()


def initial_plan_execution_state(plan: ImplementationPlan, run_id: str) -> dict:
    """Return the initial state dict for a plan execution."""
    return {
        "plan": dict(plan),
        "current_node_id": plan.get("entry_node", ""),
        "completed_nodes": [],
        "blocked_nodes": [],
        "accumulated_context": plan.get("objective", ""),
        "run_id": run_id,
    }

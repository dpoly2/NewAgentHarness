"""
GOAP Planner bridge for ArchonHub.
Converts plain-English goals into structured A* execution plans
and drops them into the plan inbox for the autoloader.
Inspired by ruvnet/ruflo GOAP module (MIT).
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
HARNESS_DIR = HERE.parent.parent
AGENTS_DIR = HARNESS_DIR.parent
PLAN_MARKDOWN_INBOX = HARNESS_DIR / "memory" / "incoming_files"
PLAN_AUTOLOAD_INBOX = AGENTS_DIR / "plans" / "inbox"

try:
    import hub_db as db
except Exception:
    db = None  # type: ignore

try:
    from ah_logging import get_logger
    logger = get_logger("goap_planner")
except Exception:
    import logging
    logger = logging.getLogger("archonhub.goap_planner")

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except Exception:
    HumanMessage = None  # type: ignore
    SystemMessage = None  # type: ignore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str, fallback: str = "step") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or fallback


def _extract_json_object(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"(\{[\s\S]*\})", text)
    if not match:
        raise ValueError("Planner did not return a JSON object")
    parsed = json.loads(match.group(1))
    if not isinstance(parsed, dict):
        raise ValueError("Planner JSON was not an object")
    return parsed


def _load_agents(project: str) -> list[dict[str, Any]]:
    if db is None or not hasattr(db, "list_agents"):
        return []
    try:
        agents = db.list_agents() or []
    except Exception:
        return []
    filtered = [
        a for a in agents
        if (a.get("status") in (None, "", "active")) and a.get("agent_id")
    ]
    project_matches = [
        a for a in filtered
        if str(a.get("project_slug", "")).lower() == str(project).lower()
    ]
    return project_matches or filtered


def _normalize_agent(agent_id: str, agents: list[dict[str, Any]]) -> str:
    if not agent_id:
        return "human"
    registered = {str(a.get("agent_id", "")): a for a in agents if a.get("agent_id")}
    if agent_id in registered:
        return agent_id

    def _norm(value: str) -> str:
        return re.sub(r"[-_\s]", "", value.lower())

    norm_target = _norm(agent_id)
    for rid in registered:
        if _norm(rid) == norm_target:
            return rid
    for rid in registered:
        norm_rid = _norm(rid)
        if norm_target in norm_rid or norm_rid in norm_target:
            return rid
    return next(iter(registered), "human")


def _fallback_plan(goal: str, project: str, agent_id: str, agents: list[dict[str, Any]]) -> dict[str, Any]:
    primary = next((a.get("agent_id") for a in agents if a.get("agent_id")), None) or agent_id or "human"
    steps = [
        {
            "step": 1,
            "action": f"Assess the current state, constraints, and dependencies for: {goal}",
            "agent": primary,
            "verify": "Current state, blockers, and required assets are documented.",
            "depends_on": [],
        },
        {
            "step": 2,
            "action": f"Implement the core work needed to achieve: {goal}",
            "agent": primary,
            "verify": "Primary deliverables are built and integrated.",
            "depends_on": [1],
        },
        {
            "step": 3,
            "action": f"Validate the outcome and capture next actions for: {goal}",
            "agent": primary,
            "verify": "Verification passes and remaining follow-ups are recorded.",
            "depends_on": [2],
        },
    ]
    return {
        "goal": goal,
        "project": project,
        "steps": steps,
        "estimated_agents": [primary],
        "complexity": "medium",
    }


def _coerce_plan(data: dict[str, Any], goal: str, project: str, default_agent_id: str, agents: list[dict[str, Any]]) -> dict[str, Any]:
    raw_steps = data.get("steps", [])
    if not isinstance(raw_steps, list) or not raw_steps:
        data = _fallback_plan(goal, project, default_agent_id, agents)
        raw_steps = data["steps"]

    steps: list[dict[str, Any]] = []
    for idx, raw_step in enumerate(raw_steps[:8], start=1):
        if not isinstance(raw_step, dict):
            continue
        action = str(raw_step.get("action", "")).strip()
        verify = str(raw_step.get("verify", "")).strip()
        if not action:
            continue
        depends_raw = raw_step.get("depends_on", [])
        if not isinstance(depends_raw, list):
            depends_raw = []
        depends_on = sorted({
            int(dep) for dep in depends_raw
            if str(dep).isdigit() and 0 < int(dep) < idx
        })
        normalized_agent = _normalize_agent(str(raw_step.get("agent", default_agent_id)), agents)
        steps.append({
            "step": idx,
            "action": action,
            "agent": normalized_agent,
            "verify": verify or "Confirm the expected output is complete and correct.",
            "depends_on": depends_on,
        })

    if len(steps) < 3:
        return _coerce_plan(_fallback_plan(goal, project, default_agent_id, agents), goal, project, default_agent_id, agents)

    estimated_agents = data.get("estimated_agents", [])
    if not isinstance(estimated_agents, list) or not estimated_agents:
        estimated_agents = [step["agent"] for step in steps]
    estimated_agents = list(dict.fromkeys(
        _normalize_agent(str(agent), agents) for agent in estimated_agents if str(agent).strip()
    ))

    complexity = str(data.get("complexity", "")).lower()
    if complexity not in {"low", "medium", "high"}:
        complexity = "high" if len(steps) >= 6 else "medium" if len(steps) >= 4 else "low"

    return {
        "plan_id": uuid.uuid4().hex,
        "goal": goal,
        "project": project,
        "steps": steps,
        "estimated_agents": estimated_agents or [default_agent_id],
        "complexity": complexity,
        "created_at": _now_iso(),
    }


def _build_prompt(goal: str, project: str, agent_id: str, context: dict[str, Any] | None, agents: list[dict[str, Any]]) -> tuple[str, str]:
    roster_lines = []
    for agent in agents[:80]:
        aid = str(agent.get("agent_id", "")).strip()
        if not aid:
            continue
        name = str(agent.get("name", "")).strip()
        role = str(agent.get("role", "")).strip()
        description = str(agent.get("description", "")).strip()
        parts = [aid]
        meta = " | ".join(p for p in (name, role, description[:120]) if p)
        if meta:
            parts.append(meta)
        roster_lines.append(" - " + " — ".join(parts))

    system_prompt = (
        "You are ArchonHub's GOAP planner, inspired by Ruflo's goal-planner agent.\n"
        "Break a high-level goal into an ordered implementation plan using Goal-Oriented Action Planning principles.\n"
        "Return valid JSON only.\n"
        "Rules:\n"
        "- Create 3 to 8 sequential steps.\n"
        "- Use exact ArchonHub agent IDs from the registry when assigning steps.\n"
        "- Each step must include: step, action, agent, verify, depends_on.\n"
        "- depends_on must be a list of earlier step numbers only.\n"
        "- Keep actions concrete and implementation-focused.\n"
        "- Keep verify checks measurable.\n"
        "- Include estimated_agents as a de-duplicated list of assigned agents.\n"
        "- Include complexity as one of: low, medium, high.\n"
        "JSON shape:\n"
        "{"
        "\"goal\":\"...\","
        "\"project\":\"...\","
        "\"steps\":[{\"step\":1,\"action\":\"...\",\"agent\":\"...\",\"verify\":\"...\",\"depends_on\":[]}],"
        "\"estimated_agents\":[\"agent-id\"],"
        "\"complexity\":\"medium\""
        "}"
    )
    user_prompt = (
        f"Planner request from agent: {agent_id}\n"
        f"Project: {project}\n"
        f"Goal: {goal}\n"
        f"Context: {json.dumps(context or {}, ensure_ascii=False)}\n\n"
        "Available ArchonHub agents:\n"
        + ("\n".join(roster_lines) if roster_lines else " - human — fallback when no agent registry entries are available")
    )
    return system_prompt, user_prompt


def plan_from_goal(goal: str, project: str, agent_id: str = "inez", context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a structured plan from a natural-language goal."""
    goal = (goal or "").strip()
    project = (project or "archon").strip() or "archon"
    agents = _load_agents(project)
    system_prompt, user_prompt = _build_prompt(goal, project, agent_id, context, agents)

    try:
        from hub_nodes import _llm
        model = _llm(temperature=0.2, weight="heavy")
        if SystemMessage is not None and HumanMessage is not None:
            response = model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
        else:
            response = model.invoke(system_prompt + "\n\n" + user_prompt)
        raw = response.content if hasattr(response, "content") else str(response)
        parsed = _extract_json_object(raw)
    except Exception as exc:
        logger.warning("GOAP LLM planning failed, using fallback plan: %s", exc)
        parsed = _fallback_plan(goal, project, agent_id, agents)

    return _coerce_plan(parsed, goal, project, agent_id, agents)


def _format_markdown(plan: dict[str, Any]) -> str:
    created_at = plan.get("created_at", _now_iso())
    steps = plan.get("steps", [])
    lines = [
        "---",
        "type: plan",
        f"plan_id: {plan.get('plan_id', uuid.uuid4().hex)}",
        f"project: {plan.get('project', '')}",
        f"goal: {json.dumps(plan.get('goal', ''), ensure_ascii=False)}",
        f"created_at: {created_at}",
        f"complexity: {plan.get('complexity', 'medium')}",
        f"agent_count: {len(plan.get('estimated_agents', []))}",
        "---",
        "",
        f"# Plan: {plan.get('goal', '')}",
        "",
        f"**Project:** {plan.get('project', '')}",
        f"**Created:** {created_at}",
        f"**Complexity:** {plan.get('complexity', 'medium')}",
        "",
        "## Steps",
        "",
    ]
    for step in steps:
        dep_list = step.get("depends_on", [])
        dep_text = "none" if not dep_list else ", ".join(f"Step {dep}" for dep in dep_list)
        lines.extend([
            f"### Step {step.get('step')}: {step.get('action', '')}",
            f"- **Agent:** `{step.get('agent', 'human')}`",
            f"- **Verify:** {step.get('verify', '')}",
            f"- **Depends on:** {dep_text}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def _build_autoload_plan(plan: dict[str, Any]) -> dict[str, Any]:
    nodes = []
    edges = []
    for step in plan.get("steps", []):
        node_id = f"step-{int(step.get('step', len(nodes) + 1))}"
        deps = [f"step-{int(dep)}" for dep in step.get("depends_on", []) if str(dep).isdigit()]
        nodes.append({
            "id": node_id,
            "label": step.get("action", "")[:120] or node_id,
            "purpose": step.get("action", ""),
            "agent": step.get("agent", "human"),
            "role": "work",
            "deps": deps,
            "exit": [step.get("verify", "")],
            "evidence": [step.get("verify", "")],
            "scope": [],
            "on_fail": "block",
        })
        for dep in deps:
            edges.append({"from": dep, "to": node_id, "kind": "dependency"})

    return {
        "title": f"GOAP Plan — {str(plan.get('goal', 'Plan'))[:120]}",
        "objective": plan.get("goal", ""),
        "project": plan.get("project", ""),
        "authored_by": "inez-goap",
        "constraints": [],
        "tags": ["goap", "ruflo", "inez"],
        "nodes": nodes,
        "edges": edges,
    }


def write_plan_to_inbox(plan: dict[str, Any], project: str) -> Path:
    """Write markdown plan to incoming_files and a JSON sidecar to the current autoload inbox."""
    PLAN_MARKDOWN_INBOX.mkdir(parents=True, exist_ok=True)
    PLAN_AUTOLOAD_INBOX.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_name = f"plan-{_slugify(project or 'archon', 'archon')}-{stamp}"
    markdown_path = PLAN_MARKDOWN_INBOX / f"{base_name}.md"
    json_path = PLAN_AUTOLOAD_INBOX / f"{base_name}.json"

    normalized_plan = dict(plan)
    normalized_plan.setdefault("project", project)
    normalized_plan.setdefault("plan_id", uuid.uuid4().hex)
    normalized_plan.setdefault("created_at", _now_iso())
    normalized_plan.setdefault("estimated_agents", [])
    normalized_plan.setdefault("complexity", "medium")

    markdown_path.write_text(_format_markdown(normalized_plan), encoding="utf-8")
    json_path.write_text(json.dumps(_build_autoload_plan(normalized_plan), ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("GOAP plan written to markdown inbox %s and autoload inbox %s", markdown_path.name, json_path.name)
    return markdown_path


async def goap_plan_from_mcp(goal: str, project: str) -> dict[str, Any]:
    """Try a local Ruflo-compatible GOAP bridge, then fall back to LLM planning."""
    try:
        import httpx

        with httpx.Client(timeout=10) as client:
            response = client.post(
                "http://localhost:3001/goap/plan",
                json={"goal": goal, "project": project},
            )
            if response.status_code == 200:
                payload = response.json()
                if isinstance(payload, dict):
                    return _coerce_plan(payload, goal, project, "inez", _load_agents(project))
    except Exception as exc:
        logger.debug("Local MCP GOAP bridge unavailable, using LLM fallback: %s", exc)
    return plan_from_goal(goal, project)

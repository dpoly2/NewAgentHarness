from __future__ import annotations

from collections import defaultdict, deque
from typing import Optional

from core.plan_schema import ImplementationPlan, PlanEdge, PreflightIssue, PreflightReport


def _err(node_id: Optional[str], msg: str) -> PreflightIssue:
    return PreflightIssue(severity="error", node_id=node_id, message=msg)


def _warn(node_id: Optional[str], msg: str) -> PreflightIssue:
    return PreflightIssue(severity="warning", node_id=node_id, message=msg)


def _has_cycle_kahn(node_ids: list[str], depends_on: dict[str, list[str]]) -> bool:
    """Kahn's algorithm — returns True if cycle exists."""
    in_degree = {node: 0 for node in node_ids}
    valid_ids = set(node_ids)
    graph: dict[str, list[str]] = defaultdict(list)
    for node in node_ids:
        for dep in depends_on.get(node, []):
            if dep in valid_ids:
                graph[dep].append(node)
                in_degree[node] = in_degree.get(node, 0) + 1
    queue = deque(node for node in node_ids if in_degree[node] == 0)
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in graph[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    return visited != len(node_ids)


def _topological_sort(node_ids: list[str], depends_on: dict[str, list[str]]) -> list[str]:
    """Returns topologically sorted node IDs. Raises ValueError on cycle."""
    in_degree: dict[str, int] = defaultdict(int)
    graph: dict[str, list[str]] = defaultdict(list)
    valid_ids = set(node_ids)
    for node in node_ids:
        in_degree[node]
        for dep in depends_on.get(node, []):
            if dep in valid_ids:
                graph[dep].append(node)
                in_degree[node] += 1
    queue = deque(sorted(node for node in node_ids if in_degree[node] == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(graph[node]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    if len(order) != len(node_ids):
        raise ValueError("Dependency cycle detected")
    return order


def _bfs_reachable(entry: str, edges: list[PlanEdge]) -> set[str]:
    """BFS from entry node following edges."""
    adj: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        adj[edge["from_node"]].append(edge["to_node"])
    visited: set[str] = set()
    queue = deque([entry])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for child in adj[node]:
            queue.append(child)
    return visited


def _detect_parallel_stages(node_ids: list[str], depends_on: dict[str, list[str]]) -> list[list[str]]:
    """Group nodes by their 'level' in the DAG — same level can run in parallel."""
    levels: dict[str, int] = {}
    topo = _topological_sort(node_ids, depends_on)
    for node in topo:
        max_dep_level = max((levels[dep] for dep in depends_on.get(node, []) if dep in levels), default=-1)
        levels[node] = max_dep_level + 1
    stage_map: dict[int, list[str]] = defaultdict(list)
    for node, level in levels.items():
        stage_map[level].append(node)
    return [stage_map[level] for level in sorted(stage_map)]


def run_preflight(plan: ImplementationPlan) -> PreflightReport:
    issues: list[PreflightIssue] = []
    node_ids = [node["id"] for node in plan["nodes"]]
    node_set = set(node_ids)
    nmap = {node["id"]: node for node in plan["nodes"]}
    depends_on_map = {node["id"]: list(node.get("depends_on", [])) for node in plan["nodes"]}

    if plan.get("entry_node") not in node_set:
        issues.append(_err(None, f"entry_node '{plan.get('entry_node')}' does not exist in nodes"))

    for node in plan["nodes"]:
        for dep in node.get("depends_on", []):
            if dep not in node_set:
                issues.append(_err(node["id"], f"depends_on '{dep}' not found in nodes"))

    for edge in plan.get("edges", []):
        for endpoint, label in ((edge["from_node"], "from_node"), (edge["to_node"], "to_node")):
            if endpoint not in node_set:
                issues.append(_err(None, f"Edge {edge['id']}: {label} '{endpoint}' not found"))

    if _has_cycle_kahn(node_ids, depends_on_map):
        issues.append(_err(None, "Dependency cycle detected — graph cannot be executed"))

    if plan.get("entry_node") in node_set:
        reachable = _bfs_reachable(plan["entry_node"], plan.get("edges", []))
        for node in plan["nodes"]:
            if node["id"] not in reachable and node["id"] != plan["entry_node"]:
                issues.append(_warn(node["id"], "Node is unreachable from entry_node via edges"))

    for node in plan["nodes"]:
        purpose = node.get("purpose", "").strip()
        if len(purpose) < 20:
            issues.append(_warn(node["id"], "purpose is too short — agent may not understand its task"))

    for node in plan["nodes"]:
        if node.get("role", "work") == "work" and not node.get("exit_criteria"):
            issues.append(_warn(node["id"], "No exit_criteria — agent cannot self-terminate correctly"))

    for node in plan["nodes"]:
        if not node.get("agent_id", ""):
            issues.append(_warn(node["id"], "agent_id is empty"))

    has_cycle = any(issue["severity"] == "error" and "cycle" in issue["message"].lower() for issue in issues)
    if not has_cycle:
        try:
            stages = _detect_parallel_stages(node_ids, depends_on_map)
            for stage in stages:
                if len(stage) < 2:
                    continue
                all_scopes: list[str] = []
                for node_id in stage:
                    all_scopes.extend(nmap[node_id].get("allowed_scope", []))
                write_scopes = [scope for scope in all_scopes if "write" in scope.lower() or "create" in scope.lower()]
                conflicts = {scope for scope in write_scopes if write_scopes.count(scope) > 1}
                if conflicts:
                    issues.append(_warn(None, f"Parallel nodes share write scope: {sorted(conflicts)}"))
        except Exception:
            pass

    seen_ids: set[str] = set()
    for node in plan["nodes"]:
        if node["id"] in seen_ids:
            issues.append(_err(node["id"], f"Duplicate node id '{node['id']}'"))
        seen_ids.add(node["id"])

    errors = [issue for issue in issues if issue["severity"] == "error"]
    simulated_order: list[str] = []
    parallel_stages: list[list[str]] = []
    if not any("cycle" in issue["message"].lower() for issue in errors):
        try:
            simulated_order = _topological_sort(node_ids, depends_on_map)
            parallel_stages = _detect_parallel_stages(node_ids, depends_on_map)
        except Exception:
            pass

    return PreflightReport(
        passed=len(errors) == 0,
        issues=issues,
        simulated_order=simulated_order,
        parallel_stages=parallel_stages,
        estimated_node_count=len(plan["nodes"]),
    )

"""
AgentHarness — Shared Agent State
Works identically in Base44 (cloud) and local offline tool.
"""
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # ── Core Identity ─────────────────────────────────────────
    agent_id: str           # e.g. "xftc-plugin-dev"
    project: str            # e.g. "xftc"
    task: str               # Natural language task description

    # ── Execution ─────────────────────────────────────────────
    messages: Annotated[list, add_messages]   # Full message history
    tool_calls: List[dict]                    # Tools invoked this run
    output: str                               # Current best output

    # ── Reflexion ─────────────────────────────────────────────
    score: float            # 0.0–1.0 quality score from evaluator
    critique: str           # What was wrong / what to improve
    revision_count: int     # How many times revised this run
    max_revisions: int      # Cap (default: 3)

    # ── Memory ────────────────────────────────────────────────
    skill_name: str         # Which skill file this run maps to
    skill_version: int      # Version of skill being used
    skill_content: str      # Full text of current skill
    memory_context: str     # Retrieved long-term memory

    # ── Environment ───────────────────────────────────────────
    environment: str        # "base44" | "local"
    run_id: str             # Unique ID for this execution


def default_state(agent_id: str, project: str, task: str,
                  environment: str = "local") -> AgentState:
    """Return a clean starting state for a new run."""
    import uuid
    return AgentState(
        agent_id=agent_id,
        project=project,
        task=task,
        messages=[],
        tool_calls=[],
        output="",
        score=0.0,
        critique="",
        revision_count=0,
        max_revisions=3,
        skill_name=f"{agent_id.replace('-', '_')}",
        skill_version=1,
        skill_content="",
        memory_context="",
        environment=environment,
        run_id=str(uuid.uuid4())[:8],
    )

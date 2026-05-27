"""
Memory Node — loads context before execution, saves learnings after.
Called at START and END of every agent run.
"""
from ..state.agent_state import AgentState


def load_memory(state: AgentState, adapter) -> AgentState:
    """
    PRE-RUN: Pull prior skill content + memory context for this agent.
    Populates state.memory_context and state.skill_content/skill_version.
    """
    agent_id   = state["agent_id"]
    skill_name = state["skill_name"]

    # Load long-term memory
    memory_context = adapter.read_memory(agent_id)

    # Load current skill
    skill_content, skill_version = adapter.read_skill(skill_name)

    print(f"[MemoryNode] Loaded skill v{skill_version} for '{agent_id}'")
    print(f"[MemoryNode] Memory: {memory_context[:100]}...")

    return {
        **state,
        "memory_context": memory_context,
        "skill_content": skill_content,
        "skill_version": skill_version,
    }


def save_memory(state: AgentState, adapter) -> AgentState:
    """
    POST-RUN: Persist run outcome to memory/entity storage.
    """
    adapter.write_memory(
        agent_id=state["agent_id"],
        run_id=state["run_id"],
        score=state["score"],
        critique=state["critique"],
        output_summary=state["output"][:300],
        task=state["task"],
        project=state["project"],
        revision_count=state["revision_count"],
        skill_version=state["skill_version"],
        status="complete",
    )
    print(f"[MemoryNode] Run {state['run_id']} saved — "
          f"score:{state['score']:.2f} revisions:{state['revision_count']}")
    return state

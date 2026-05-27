"""
Reflexion Loop — the core self-improving agent graph.
Wires all nodes together: load_memory → act → evaluate → (revise →)* save.
Works with either Base44Adapter or LocalAdapter.
"""
from functools import partial
from langgraph.graph import StateGraph, END

from ..state.agent_state import AgentState, default_state
from ..nodes.memory_node   import load_memory, save_memory
from ..nodes.act_node      import act
from ..nodes.evaluate_node import evaluate, should_revise
from ..nodes.revise_node   import revise


def build_reflexion_graph(adapter):
    """
    Build and compile the Reflexion LangGraph.
    Pass in either Base44Adapter() or LocalAdapter().
    """

    # Bind adapter to nodes that need it
    _load_memory = partial(load_memory,  adapter=adapter)
    _save_memory = partial(save_memory,  adapter=adapter)
    _revise      = partial(revise,       adapter=adapter)

    graph = StateGraph(AgentState)

    # ── Add nodes ─────────────────────────────────────────────
    graph.add_node("load_memory", _load_memory)
    graph.add_node("act",         act)
    graph.add_node("evaluate",    evaluate)
    graph.add_node("revise",      _revise)
    graph.add_node("save_memory", _save_memory)

    # ── Wire edges ────────────────────────────────────────────
    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "act")
    graph.add_edge("act",         "evaluate")

    # Conditional: revise or save
    graph.add_conditional_edges(
        "evaluate",
        should_revise,
        {
            "revise": "revise",
            "save":   "save_memory",
        }
    )

    # Revision loops back to act
    graph.add_edge("revise", "act")

    # Final save → END
    graph.add_edge("save_memory", END)

    return graph.compile()


def run_agent(agent_id: str, project: str, task: str,
              environment: str = "local") -> dict:
    """
    High-level entry point. Auto-selects adapter based on environment.
    Returns the final state dict.
    """
    if environment == "base44":
        from ..adapters.base44_adapter import Base44Adapter
        adapter = Base44Adapter()
    else:
        from ..adapters.local_adapter import LocalAdapter
        adapter = LocalAdapter()

    graph = build_reflexion_graph(adapter)
    state = default_state(agent_id, project, task, environment)

    print(f"\n{'='*60}")
    print(f"REFLEXION RUN — {agent_id} | {project} | run:{state['run_id']}")
    print(f"TASK: {task[:100]}")
    print(f"{'='*60}\n")

    final_state = graph.invoke(state)

    print(f"\n{'='*60}")
    print(f"COMPLETE — score:{final_state['score']:.2f} "
          f"revisions:{final_state['revision_count']} "
          f"skill_v:{final_state['skill_version']}")
    print(f"{'='*60}\n")

    return final_state

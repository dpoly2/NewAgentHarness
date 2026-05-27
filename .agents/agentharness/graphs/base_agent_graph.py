"""
Base Agent Graph — minimal single-step graph.
Use this as a starting point for any new agent type.
Wires: load_memory → act → evaluate → (revise →)* save
This is the Phase 1 foundation all other graphs extend.
"""
from .reflexion_loop import build_reflexion_graph, run_agent

# Re-export for convenience — base graph IS the reflexion loop
__all__ = ["build_reflexion_graph", "run_agent"]

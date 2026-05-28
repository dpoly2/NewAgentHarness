"""
AgentHarness — Main Entry Point
Usage:
    python run.py --agent grants-research-agent --project xftc --task "Find 3 grants"
    python run.py --agent xftc-plugin-dev --project xftc --task "Write leaderboard endpoint" --graph wordpress
    python run.py --agent grants-research-agent --project xftc --task "Find grants" --graph research
    python run.py --verify   (quick sanity check — no OpenAI key needed)
"""

import sys
import os
import argparse

# Make sure agentharness is importable regardless of where you run from
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
if PARENT not in sys.path:
    sys.path.append(PARENT)

# ── CLI argument parser ─────────────────────────────────────────────────────

parser = argparse.ArgumentParser(
    description="AgentHarness — LangGraph + Reflexion Agent Runner",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  python run.py --verify
  python run.py --agent grants-research-agent --project xftc --task "Find 3 active grants for youth track in Texas"
  python run.py --agent xftc-plugin-dev --project xftc --task "Write REST endpoint for leaderboard" --graph wordpress
  python run.py --agent grants-research-agent --project yepc --task "Find infrastructure grants for sports complex" --graph research
    """
)
parser.add_argument("--agent",   type=str, help="Agent ID (e.g. grants-research-agent)")
parser.add_argument("--project", type=str, help="Project name (e.g. xftc, yepc, pbs)")
parser.add_argument("--task",    type=str, help="Task description in plain English")
parser.add_argument("--graph",   type=str, default="reflexion",
                    choices=["reflexion", "research", "wordpress"],
                    help="Which graph to run (default: reflexion)")
parser.add_argument("--env",     type=str, default="local",
                    choices=["local", "base44"],
                    help="Adapter environment (default: local)")
parser.add_argument("--verify",  action="store_true",
                    help="Run a quick import + graph compile check (no API key needed)")

args = parser.parse_args()

# ── Verify mode ──────────────────────────────────────────────────────────────

if args.verify:
    print("\nAgentHarness — Verify Mode")
    print("=" * 50)
    try:
        from agentharness.state.agent_state import default_state
        print("  ✅ state.agent_state")
        from agentharness.adapters.local_adapter import LocalAdapter
        print("  ✅ adapters.local_adapter")
        from agentharness.nodes.act_node import act
        from agentharness.nodes.evaluate_node import evaluate, should_revise
        from agentharness.nodes.revise_node import revise
        from agentharness.nodes.memory_node import load_memory, save_memory
        print("  ✅ nodes (act, evaluate, revise, memory)")
        from agentharness.graphs.reflexion_loop import build_reflexion_graph
        from agentharness.graphs.research_graph import build_research_graph
        from agentharness.graphs.wordpress_graph import build_wordpress_graph
        print("  ✅ graphs (reflexion, research, wordpress)")

        adapter = LocalAdapter()
        g1 = build_reflexion_graph(adapter)
        g2 = build_research_graph(adapter)
        g3 = build_wordpress_graph(adapter)
        print(f"  ✅ all 3 graphs compiled ({type(g1).__name__})")

        state = default_state("test-agent", "test", "test task", "local")
        state["score"] = 0.60; state["revision_count"] = 0; state["max_revisions"] = 3
        assert should_revise(state) == "revise"
        state["score"] = 0.82
        assert should_revise(state) == "save"
        print("  ✅ reflexion logic validated")

        print()
        print("ALL SYSTEMS GO ✅")
        print("Run with: python run.py --agent <id> --project <project> --task \"<task>\"")
        print("=" * 50)
        sys.exit(0)
    except Exception as e:
        print(f"\n  ❌ ERROR: {e}")
        print("\nCheck that dependencies are installed:")
        print("  py -m pip install -r requirements.txt")
        sys.exit(1)

# ── Run mode ─────────────────────────────────────────────────────────────────

if not args.agent or not args.project or not args.task:
    parser.print_help()
    print("\n❌ --agent, --project, and --task are all required for a run.")
    sys.exit(1)

# Check for OpenAI key
if not os.environ.get("OPENAI_API_KEY"):
    # Try loading from .env in the agentharness folder
    env_path = os.path.join(HERE, ".env")
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"  Loaded .env from {env_path}")
    else:
        print("\n❌ OPENAI_API_KEY not set.")
        print("   Set it in PowerShell:  $env:OPENAI_API_KEY = 'sk-...'")
        print(f"   Or create a .env file: {env_path}")
        print("   Contents: OPENAI_API_KEY=sk-...")
        sys.exit(1)

# Select and run the graph
graph_map = {
    "reflexion": "agentharness.graphs.reflexion_loop",
    "research":  "agentharness.graphs.research_graph",
    "wordpress": "agentharness.graphs.wordpress_graph",
}

run_fn_map = {
    "reflexion": "run_agent",
    "research":  "run_research",
    "wordpress": "run_wordpress_task",
}

import importlib
mod = importlib.import_module(graph_map[args.graph])
run_fn = getattr(mod, run_fn_map[args.graph])

result = run_fn(
    agent_id=args.agent,
    project=args.project,
    task=args.task,
    environment=args.env,
)

# Print output
print("\n" + "=" * 60)
print("OUTPUT:")
print("=" * 60)
print(result.get("output", "(no output)"))
print()
print(f"Score:     {result.get('score', 0):.2f}")
print(f"Revisions: {result.get('revision_count', 0)}")
print(f"Run ID:    {result.get('run_id', '?')}")
print("=" * 60)

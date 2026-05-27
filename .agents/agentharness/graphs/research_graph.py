"""
Research Graph — multi-hop grant & funding research workflow.
Used by: grants-research-agent, yepc-grant-writer-agent
Nodes: plan → search → synthesize → evaluate → revise* → save
"""
from functools import partial
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..state.agent_state import AgentState, default_state
from ..nodes.memory_node   import load_memory, save_memory
from ..nodes.evaluate_node import evaluate, should_revise
from ..nodes.revise_node   import revise

MODEL = "gpt-4o"


def plan(state: AgentState) -> AgentState:
    """Break the research task into specific search queries."""
    llm = ChatOpenAI(model=MODEL, temperature=0.2)
    response = llm.invoke([
        SystemMessage(content=(
            "You are a research planning assistant. "
            "Given a research task, output 3–5 specific search queries "
            "that will find the most relevant grants, funding sources, or information. "
            "Output as a numbered list only."
        )),
        HumanMessage(content=f"Research task: {state['task']}"),
    ])
    print(f"[ResearchGraph:plan] Queries generated")
    return {
        **state,
        "messages": state["messages"] + [response],
        "output": f"RESEARCH PLAN:\n{response.content}",
    }


def search(state: AgentState) -> AgentState:
    """
    Simulate multi-hop search across grant databases.
    In production: wire to Perplexity API, Google Search, or web_search skill.
    """
    llm = ChatOpenAI(model=MODEL, temperature=0.1)

    queries = state["output"].replace("RESEARCH PLAN:\n", "")
    response = llm.invoke([
        SystemMessage(content=(
            "You are a grant research specialist with knowledge of federal, state, "
            "and private foundation funding opportunities as of 2026. "
            "For each search query provided, synthesize the most relevant funding "
            "opportunities including: grant name, funder, amount, deadline, eligibility, "
            "and application link. Be specific and factual."
        )),
        HumanMessage(content=(
            f"Project context: {state['project']}\n"
            f"Agent: {state['agent_id']}\n"
            f"Memory: {state.get('memory_context', '')}\n\n"
            f"Search queries:\n{queries}"
        )),
    ])
    print(f"[ResearchGraph:search] Results gathered")
    return {
        **state,
        "messages": state["messages"] + [response],
        "output": response.content,
    }


def synthesize(state: AgentState) -> AgentState:
    """Produce a final ranked digest with action items."""
    llm = ChatOpenAI(model=MODEL, temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=(
            "You are a grant writing strategist. "
            "Given raw research results, produce a clean, prioritized digest with:\n"
            "1. TOP OPPORTUNITIES (3–5 best fits, ranked)\n"
            "2. QUICK WINS (low barrier, fast deadline)\n"
            "3. ACTION ITEMS (what to do next for each)\n"
            "4. WATCH LIST (longer-term opportunities)\n"
            "Be specific with amounts, deadlines, and next steps."
        )),
        HumanMessage(content=(
            f"Original task: {state['task']}\n\n"
            f"Raw research:\n{state['output']}"
        )),
    ])
    print(f"[ResearchGraph:synthesize] Digest complete")
    return {
        **state,
        "output": response.content,
        "messages": state["messages"] + [response],
    }


def build_research_graph(adapter):
    """Build and compile the multi-hop research graph."""
    _load_memory = partial(load_memory,  adapter=adapter)
    _save_memory = partial(save_memory,  adapter=adapter)
    _revise      = partial(revise,       adapter=adapter)

    graph = StateGraph(AgentState)

    graph.add_node("load_memory", _load_memory)
    graph.add_node("plan",        plan)
    graph.add_node("search",      search)
    graph.add_node("synthesize",  synthesize)
    graph.add_node("evaluate",    evaluate)
    graph.add_node("revise",      _revise)
    graph.add_node("save_memory", _save_memory)

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "plan")
    graph.add_edge("plan",        "search")
    graph.add_edge("search",      "synthesize")
    graph.add_edge("synthesize",  "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        should_revise,
        {"revise": "revise", "save": "save_memory"}
    )
    graph.add_edge("revise",      "synthesize")   # Re-synthesize after revision
    graph.add_edge("save_memory", END)

    return graph.compile()


def run_research(project: str, task: str, environment: str = "local") -> dict:
    """Entry point for research agent runs."""
    if environment == "base44":
        from ..adapters.base44_adapter import Base44Adapter
        adapter = Base44Adapter()
    else:
        from ..adapters.local_adapter import LocalAdapter
        adapter = LocalAdapter()

    graph = build_research_graph(adapter)
    state = default_state("grants-research-agent", project, task, environment)
    return graph.invoke(state)

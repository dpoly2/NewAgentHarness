"""
WordPress Graph — multi-step WP agent workflow.
Used by: xftc-plugin-dev, xftc-frontend-dev, s2t-webdev-agent
Nodes: plan → implement → verify → evaluate → revise* → save
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


def wp_plan(state: AgentState) -> AgentState:
    """Decompose WP task into implementation steps."""
    llm = ChatOpenAI(model=MODEL, temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=(
            "You are a senior WordPress developer. "
            "Given a WordPress development task, output a numbered implementation plan "
            "with specific technical steps. Include: files to modify, functions to write, "
            "REST API calls needed, and any WP hooks/filters to use. "
            "Be concrete — no vague steps."
        )),
        HumanMessage(content=(
            f"Agent: {state['agent_id']}\n"
            f"Project: {state['project']}\n"
            f"Skill context: {state.get('skill_content', '')[:500]}\n"
            f"Memory: {state.get('memory_context', '')}\n\n"
            f"Task: {state['task']}"
        )),
    ])
    print(f"[WPGraph:plan] Implementation plan generated")
    return {
        **state,
        "output": f"IMPLEMENTATION PLAN:\n{response.content}",
        "messages": state["messages"] + [response],
    }


def wp_implement(state: AgentState) -> AgentState:
    """Generate the actual code, REST calls, or content updates."""
    llm = ChatOpenAI(model=MODEL, temperature=0.1)
    response = llm.invoke([
        SystemMessage(content=(
            "You are a senior WordPress developer implementing a task. "
            "Given an implementation plan, produce the complete, working code or "
            "REST API call sequences needed. Include:\n"
            "- Full PHP/JS code (no placeholders)\n"
            "- Exact REST API endpoints and payloads\n"
            "- Error handling\n"
            "- Inline comments explaining non-obvious logic\n"
            "Output should be immediately usable."
        )),
        HumanMessage(content=(
            f"Project: {state['project']}\n"
            f"Original task: {state['task']}\n\n"
            f"Plan to implement:\n{state['output']}"
        )),
    ])
    print(f"[WPGraph:implement] Code generated")
    return {
        **state,
        "output": response.content,
        "messages": state["messages"] + [response],
    }


def wp_verify(state: AgentState) -> AgentState:
    """Self-check the implementation for common WP errors."""
    llm = ChatOpenAI(model=MODEL, temperature=0.0)
    response = llm.invoke([
        SystemMessage(content=(
            "You are a WordPress code reviewer. "
            "Review the implementation for:\n"
            "1. Security issues (SQL injection, nonce missing, capability checks)\n"
            "2. WP coding standards violations\n"
            "3. REST API authentication issues\n"
            "4. Gutenberg block format errors\n"
            "5. Missing error handling\n"
            "If issues found, list them. If clean, say 'VERIFIED: No issues found.' "
            "Then output the corrected/verified final implementation."
        )),
        HumanMessage(content=(
            f"Task: {state['task']}\n\n"
            f"Implementation to verify:\n{state['output']}"
        )),
    ])
    print(f"[WPGraph:verify] Verification complete")
    return {
        **state,
        "output": response.content,
        "messages": state["messages"] + [response],
    }


def build_wordpress_graph(adapter):
    """Build and compile the WordPress agent graph."""
    _load_memory = partial(load_memory,  adapter=adapter)
    _save_memory = partial(save_memory,  adapter=adapter)
    _revise      = partial(revise,       adapter=adapter)

    graph = StateGraph(AgentState)

    graph.add_node("load_memory",   _load_memory)
    graph.add_node("wp_plan",       wp_plan)
    graph.add_node("wp_implement",  wp_implement)
    graph.add_node("wp_verify",     wp_verify)
    graph.add_node("evaluate",      evaluate)
    graph.add_node("revise",        _revise)
    graph.add_node("save_memory",   _save_memory)

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory",   "wp_plan")
    graph.add_edge("wp_plan",       "wp_implement")
    graph.add_edge("wp_implement",  "wp_verify")
    graph.add_edge("wp_verify",     "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        should_revise,
        {"revise": "revise", "save": "save_memory"}
    )
    graph.add_edge("revise",      "wp_implement")  # Re-implement after revision
    graph.add_edge("save_memory", END)

    return graph.compile()


def run_wordpress_task(agent_id: str, project: str, task: str,
                       environment: str = "local") -> dict:
    """Entry point for WordPress agent tasks."""
    if environment == "base44":
        from ..adapters.base44_adapter import Base44Adapter
        adapter = Base44Adapter()
    else:
        from ..adapters.local_adapter import LocalAdapter
        adapter = LocalAdapter()

    graph = build_wordpress_graph(adapter)
    state = default_state(agent_id, project, task, environment)
    return graph.invoke(state)

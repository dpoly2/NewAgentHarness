"""
Act Node — executes the agent's task using the LLM + current skill.
This is the core "do the work" node in the Reflexion loop.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..state.agent_state import AgentState

MODEL = "gpt-4o"


def build_system_prompt(state: AgentState) -> str:
    """Construct the agent's system prompt from identity + skill + memory."""
    parts = [
        f"You are the '{state['agent_id']}' agent for the '{state['project']}' project.",
        "Your job is to complete the task given to you accurately and thoroughly.",
    ]
    if state.get("skill_content"):
        parts.append(
            f"\n## Your Current Skill (v{state['skill_version']}):\n"
            f"{state['skill_content']}"
        )
    if state.get("memory_context"):
        parts.append(f"\n## Memory Context:\n{state['memory_context']}")
    if state.get("critique") and state["revision_count"] > 0:
        parts.append(
            f"\n## Critique from Last Attempt:\n{state['critique']}\n"
            "Address every point in this critique in your new response."
        )
    return "\n\n".join(parts)


def act(state: AgentState) -> AgentState:
    """
    Execute the task. Returns updated state with output + appended message.
    """
    llm = ChatOpenAI(model=MODEL, temperature=0.2)

    system_prompt = build_system_prompt(state)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["task"]),
    ]

    # Include prior message history if this is a revision
    if state["revision_count"] > 0 and state.get("messages"):
        messages = state["messages"] + [
            HumanMessage(
                content=f"REVISION {state['revision_count']} — "
                        f"Please address this critique:\n{state['critique']}\n\n"
                        f"Re-complete the original task: {state['task']}"
            )
        ]

    print(f"[ActNode] Running '{state['agent_id']}' — "
          f"revision:{state['revision_count']} run:{state['run_id']}")

    response = llm.invoke(messages)
    output   = response.content

    return {
        **state,
        "output": output,
        "messages": messages + [response],
    }

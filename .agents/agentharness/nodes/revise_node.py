"""
Revise Node — rewrites the agent's skill file based on the critique.
Increments version, saves to disk/entity, then loops back to act_node.
This is where agents actually get smarter over time.
"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..state.agent_state import AgentState

MODEL = "gpt-4o"

SKILL_REWRITER_SYSTEM = """You are an AI agent skill optimizer.
You will be given:
1. An agent's current skill file (instructions for how it does its job)
2. A task it just attempted
3. Its output
4. A critique of what went wrong

Your job: rewrite the skill file to address the critique and prevent the same mistakes.
The rewritten skill should make the agent perform better on this type of task in the future.

Rules:
- Keep the skill file in Markdown format
- Keep the version header: "# Skill: {name} v{N}" (increment N)
- Be specific — add concrete instructions, examples, or rules based on the critique
- Do NOT pad or add fluff — every line should improve performance
- Output ONLY the rewritten skill file content, nothing else
"""


def revise(state: AgentState, adapter) -> AgentState:
    """
    Rewrite the skill file based on critique. Increment version. Loop to act.
    """
    llm = ChatOpenAI(model=MODEL, temperature=0.3)

    skill_name    = state["skill_name"]
    current_skill = state.get("skill_content", "")
    new_version   = state["skill_version"] + 1

    # If no skill file exists yet, create a starter
    if not current_skill.strip():
        current_skill = (
            f"# Skill: {skill_name} v1\n\n"
            f"## Agent: {state['agent_id']}\n"
            f"## Project: {state['project']}\n\n"
            "## Instructions\n"
            "Complete tasks accurately and thoroughly.\n"
        )

    rewrite_prompt = (
        f"## Current Skill File (v{state['skill_version']}):\n"
        f"{current_skill}\n\n"
        f"## Task That Was Attempted:\n{state['task']}\n\n"
        f"## Agent's Output:\n{state['output'][:1000]}\n\n"
        f"## Critique:\n{state['critique']}\n\n"
        f"Rewrite the skill file as v{new_version} to address this critique."
    )

    response = llm.invoke([
        SystemMessage(content=SKILL_REWRITER_SYSTEM),
        HumanMessage(content=rewrite_prompt),
    ])

    new_skill_content = response.content.strip()

    # Ensure version header is present
    if not new_skill_content.startswith(f"# Skill: {skill_name} v{new_version}"):
        new_skill_content = (
            f"# Skill: {skill_name} v{new_version}\n\n" + new_skill_content
        )

    # Persist to storage
    adapter.write_skill(
        skill_name=skill_name,
        content=new_skill_content,
        version=new_version,
        score=state["score"],
        critique=state["critique"],
        agent_id=state["agent_id"],
    )

    print(f"[ReviseNode] Skill '{skill_name}' upgraded v{state['skill_version']} → v{new_version}")

    return {
        **state,
        "skill_content": new_skill_content,
        "skill_version": new_version,
        "revision_count": state["revision_count"] + 1,
    }

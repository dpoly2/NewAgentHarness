"""
Evaluate Node — scores the agent's output on 3 criteria.
Returns a score 0.0–1.0 and a structured critique.
If score >= 0.75 → proceed to save. If < 0.75 → trigger revise.
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..state.agent_state import AgentState

MODEL      = "gpt-4o"
THRESHOLD  = 0.75


EVALUATOR_SYSTEM = """You are a strict but fair quality evaluator for AI agent outputs.
Score the agent's output on these 3 criteria (0.0 to 1.0 each):

1. COMPLETION — Did the agent fully complete the task as requested?
2. QUALITY    — Is the output accurate, well-structured, and useful?
3. EFFICIENCY — Is the output concise and free of unnecessary content?

Respond ONLY with valid JSON in this exact format:
{
  "completion": 0.0,
  "quality": 0.0,
  "efficiency": 0.0,
  "overall": 0.0,
  "critique": "Specific, actionable feedback on what to improve. Be direct."
}

The "overall" score should be a weighted average: completion*0.5 + quality*0.35 + efficiency*0.15.
If the output is excellent, say so briefly in the critique but still give a score.
"""


def evaluate(state: AgentState) -> AgentState:
    """
    Score the current output. Returns updated state with score + critique.
    """
    llm = ChatOpenAI(model=MODEL, temperature=0.0)

    eval_prompt = (
        f"TASK:\n{state['task']}\n\n"
        f"AGENT OUTPUT:\n{state['output']}\n\n"
        "Score this output on the 3 criteria."
    )

    response = llm.invoke([
        SystemMessage(content=EVALUATOR_SYSTEM),
        HumanMessage(content=eval_prompt),
    ])

    # Parse JSON response
    try:
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        scores = json.loads(raw.strip())
        overall  = scores.get("overall", 0.0)
        critique = scores.get("critique", "No critique provided.")
    except (json.JSONDecodeError, KeyError):
        # Fallback: assume mediocre score if parsing fails
        overall  = 0.60
        critique = f"Evaluator parse error. Raw: {response.content[:200]}"

    print(f"[EvaluateNode] Score: {overall:.2f} — {critique[:80]}")

    return {
        **state,
        "score": overall,
        "critique": critique,
    }


def should_revise(state: AgentState) -> str:
    """
    Conditional edge function.
    Returns "revise" if score is below threshold AND revisions remain.
    Returns "save" otherwise.
    """
    below_threshold = state["score"] < THRESHOLD
    has_revisions   = state["revision_count"] < state["max_revisions"]

    if below_threshold and has_revisions:
        print(f"[EvaluateNode] Score {state['score']:.2f} < {THRESHOLD} → REVISE "
              f"({state['revision_count']+1}/{state['max_revisions']})")
        return "revise"

    print(f"[EvaluateNode] Score {state['score']:.2f} → SAVE "
          f"(revisions:{state['revision_count']})")
    return "save"

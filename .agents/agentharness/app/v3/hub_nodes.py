from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).parent         # app/v3/
HARNESS = HERE.parent.parent         # agentharness/
AGENTS_DIR = HARNESS.parent          # .agents/
APP_ROOT = AGENTS_DIR.parent         # repo root
SKILLS_DIR = AGENTS_DIR / "agents" / "projects"
MEMORY_DIR = HARNESS / "memory"

try:
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from typing import TypedDict, List, Annotated
    from langgraph.graph.message import add_messages
    LANGGRAPH_OK = True
except ImportError:
    LANGGRAPH_OK = False


class _HubDbFallback:
    def load_memory_context(self, agent_id: str) -> str:
        memory_file = MEMORY_DIR / f"{agent_id}.txt"
        if memory_file.exists():
            try:
                return memory_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return "No prior runs."
        return "No prior runs."

    def save_run(self, payload: dict) -> None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        runs_file = MEMORY_DIR / "hub_runs.log"
        try:
            with runs_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def load_skill(self, skill_name: str) -> tuple[str, int]:
        return "", 1

    def save_skill(
        self,
        agent_id: str,
        skill_name: str,
        version: int,
        content: str,
        score: float,
        critique: str,
    ) -> None:
        return None

    def update_agent_memory(self, agent_id: str, content: str) -> None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        try:
            (MEMORY_DIR / f"{agent_id}.txt").write_text(content, encoding="utf-8")
        except Exception:
            pass


try:
    try:
        from . import hub_db as db  # type: ignore[import-not-found]
    except ImportError:
        import hub_db as db  # type: ignore[import-not-found]
except ImportError:
    db = _HubDbFallback()


MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

_AI_CONFIG_PATHS = [
    AGENTS_DIR / "data" / "ai_config.json",
    APP_ROOT / "projects" / "agentharness-v2" / "data" / "ai_config.json",
]

_BASE_URLS_BY_PROVIDER = {
    "ollama": "http://localhost:11434/v1",
    "github": "https://models.inference.ai.azure.com",
    "groq":   "https://api.groq.com/openai/v1",
}


def _load_ai_config() -> dict:
    """Load LLM provider config from file, then env vars as fallback."""
    defaults: dict = {
        "provider": os.environ.get("LLM_PROVIDER", "openai"),
        "baseUrl":  os.environ.get("LLM_BASE_URL", ""),
        "apiKey":   os.environ.get("OPENAI_API_KEY", ""),
        "model":    os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "enabled":  True,
    }
    for path in _AI_CONFIG_PATHS:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return {**defaults, **data}
            except Exception:
                pass
    return defaults


def _llm(temperature: float = 0.2):
    cfg = _load_ai_config()
    # DB overrides take highest priority
    try:
        if hasattr(db, "get_config"):
            db_cfg = db.get_config()
            if isinstance(db_cfg, dict):
                if db_cfg.get("llm_provider"):
                    cfg["provider"] = db_cfg["llm_provider"]
                if db_cfg.get("llm_model"):
                    cfg["model"] = db_cfg["llm_model"]
                if db_cfg.get("llm_api_key"):
                    cfg["apiKey"] = db_cfg["llm_api_key"]
                if db_cfg.get("llm_base_url"):
                    cfg["baseUrl"] = db_cfg["llm_base_url"]
    except Exception:
        pass

    provider = cfg.get("provider", "openai")
    model    = cfg.get("model", "gpt-4o-mini")
    api_key  = cfg.get("apiKey", "") or os.environ.get("OPENAI_API_KEY", "")
    base_url = cfg.get("baseUrl", "")

    # Anthropic
    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic  # type: ignore
            return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
        except ImportError:
            pass  # fall through to OpenAI-compatible

    # Google Gemini
    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
            return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=api_key)
        except ImportError:
            pass

    # OpenAI-compatible: openai, ollama, github, groq, custom
    resolved_url = base_url or _BASE_URLS_BY_PROVIDER.get(provider, "")
    resolved_key = api_key or (os.environ.get("GITHUB_TOKEN", "") if provider == "github" else "ollama")
    kwargs: dict = {
        "model":       model,
        "temperature": temperature,
        "api_key":     resolved_key or "sk-placeholder",
    }
    if resolved_url:
        kwargs["base_url"] = resolved_url
    return ChatOpenAI(**kwargs)


if LANGGRAPH_OK:
    class AgentState(TypedDict):
        run_id: str
        agent_id: str
        project: str
        graph_type: str
        task: str
        skill_name: str
        skill_content: str
        skill_version: int
        memory_context: str
        output: str
        score: float
        critique: str
        revision_count: int
        max_revisions: int
        messages: Annotated[List, add_messages]
        cancel_flag: Any


_NOOP_EMIT: Callable[..., None] = lambda event_type, **kwargs: None


def _emit(emit: Callable[..., None] | None, event_type: str, **kwargs: Any) -> None:
    if not emit:
        return
    try:
        emit(event_type, **kwargs)
    except Exception:
        pass


def _cancel_check(state: dict) -> None:
    if state.get("cancel_flag") and state["cancel_flag"].is_set():
        raise RuntimeError("Run cancelled")


def _message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


def _extract_skill_version(content: str, fallback: int = 1) -> int:
    match = re.search(r"\bv(?:ersion)?\s*[:#-]?\s*(\d+)\b", content, re.IGNORECASE)
    return int(match.group(1)) if match else fallback


def _strip_json_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _invoke(messages: list[Any], temperature: float, fallback_text: str) -> tuple[str, list[Any]]:
    if not LANGGRAPH_OK:
        return fallback_text, []
    try:
        response = _llm(temperature=temperature).invoke(messages)
        return _message_text(response), [response]
    except Exception as exc:
        return f"{fallback_text}\n\nLLM error: {exc}", []


def _skill_system_prompt(state: dict) -> str:
    return (
        (state.get("skill_content") or "You are a helpful specialist agent.")
        + "\n\nMemory Context:\n"
        + (state.get("memory_context") or "No prior runs.")
    )


def read_agent_skill_file(agent_id: str) -> tuple[str, str]:
    if not SKILLS_DIR.exists():
        return "", ""
    for path in SKILLS_DIR.rglob(f"{agent_id}.md"):
        try:
            return path.read_text(encoding="utf-8", errors="ignore"), str(path)
        except Exception:
            return "", str(path)
    return "", ""


def write_agent_skill_file(agent_id: str, content: str) -> None:
    existing_content, existing_path = read_agent_skill_file(agent_id)
    target = Path(existing_path) if existing_path else SKILLS_DIR / f"{agent_id}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content if content else existing_content, encoding="utf-8")


def node_load_memory(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="load_memory", status="running", run_id=state.get("run_id"))
    skill_content, _ = read_agent_skill_file(state["agent_id"])
    skill_version = _extract_skill_version(skill_content, state.get("skill_version", 1))
    try:
        if hasattr(db, "load_skill"):
            db_content, db_version = db.load_skill(state.get("skill_name", state["agent_id"]))
            if not skill_content and db_content:
                skill_content = db_content
                skill_version = db_version or skill_version
    except Exception:
        pass
    try:
        memory_context = db.load_memory_context(state["agent_id"])
    except Exception:
        memory_context = "No prior runs."
    _emit(
        emit,
        "node_update",
        node="load_memory",
        status="complete",
        run_id=state.get("run_id"),
        skill_version=skill_version,
    )
    return {
        "skill_content": skill_content,
        "skill_version": skill_version,
        "memory_context": memory_context,
    }


def node_act(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="act", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(content=_skill_system_prompt(state)),
        HumanMessage(content=state["task"]),
    ] if LANGGRAPH_OK else []
    output, response_messages = _invoke(messages, 0.2, "LangGraph not installed - mock output")
    _emit(
        emit,
        "node_update",
        node="act",
        status="complete",
        run_id=state.get("run_id"),
        preview=output[:200],
    )
    return {"output": output, "messages": messages + response_messages}


def node_evaluate(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="evaluate", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Score the output from 0.0 to 1.0 for completeness, correctness, and usefulness. "
                'Return JSON only with keys "score" and "critique".'
            )
        ),
        HumanMessage(content=f"TASK:\n{state['task']}\n\nOUTPUT:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    raw, _ = _invoke(messages, 0.0, '{"score": 0.0, "critique": "LangGraph not installed - mock output"}')
    try:
        payload = json.loads(_strip_json_fence(raw))
        score = max(0.0, min(1.0, float(payload.get("score", 0.0))))
        critique = str(payload.get("critique", "")).strip()
    except Exception:
        score = 0.0
        critique = f"Could not parse evaluator response: {raw[:300]}"
    _emit(
        emit,
        "node_update",
        node="evaluate",
        status="complete",
        run_id=state.get("run_id"),
        score=score,
        critique=critique,
    )
    return {"score": score, "critique": critique}


def node_revise(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="revise", status="running", run_id=state.get("run_id"))
    if state.get("score", 1.0) >= 0.75:
        _emit(emit, "node_update", node="revise", status="skipped", run_id=state.get("run_id"))
        return {
            "output": state.get("output", ""),
            "revision_count": state.get("revision_count", 0),
            "skill_content": state.get("skill_content", ""),
        }

    revise_messages = [
        SystemMessage(
            content=(
                "Revise the work to address the critique while preserving valid content. "
                "Return only the improved result."
            )
        ),
        HumanMessage(
            content=(
                f"TASK:\n{state['task']}\n\nCURRENT OUTPUT:\n{state.get('output', '')}\n\n"
                f"CRITIQUE:\n{state.get('critique', '')}"
            )
        ),
    ] if LANGGRAPH_OK else []
    revised_output, _ = _invoke(revise_messages, 0.3, state.get("output", "LangGraph not installed - mock output"))

    updated_skill = state.get("skill_content", "")
    updated_version = state.get("skill_version", 1)
    if LANGGRAPH_OK:
        skill_messages = [
            SystemMessage(
                content=(
                    "Improve the agent skill instructions based on the critique. "
                    "Return concise markdown guidance only."
                )
            ),
            HumanMessage(
                content=(
                    f"CURRENT SKILL:\n{state.get('skill_content', '')}\n\n"
                    f"TASK:\n{state['task']}\n\nCRITIQUE:\n{state.get('critique', '')}\n\n"
                    "Revise the skill only if it would improve future runs."
                )
            ),
        ]
        candidate_skill, _ = _invoke(skill_messages, 0.2, updated_skill or "# Skill\n")
        candidate_skill = candidate_skill.strip()
        if candidate_skill and candidate_skill != updated_skill:
            updated_skill = candidate_skill
            updated_version += 1
            try:
                if hasattr(db, "save_skill"):
                    db.save_skill(
                        state["agent_id"],
                        state.get("skill_name", state["agent_id"]),
                        updated_version,
                        updated_skill,
                        state.get("score", 0.0),
                        state.get("critique", ""),
                    )
            except Exception:
                pass
            try:
                write_agent_skill_file(state["agent_id"], updated_skill)
            except Exception:
                pass

    revision_count = state.get("revision_count", 0) + 1
    _emit(
        emit,
        "node_update",
        node="revise",
        status="complete",
        run_id=state.get("run_id"),
        revision_count=revision_count,
        skill_version=updated_version,
    )
    return {
        "output": revised_output,
        "revision_count": revision_count,
        "skill_content": updated_skill,
        "skill_version": updated_version,
    }


def node_save_memory(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="save_memory", status="running", run_id=state.get("run_id"))
    payload = {
        "run_id": state.get("run_id"),
        "agent_id": state.get("agent_id"),
        "project": state.get("project"),
        "graph": state.get("graph_type", "reflexion"),
        "task": state.get("task", ""),
        "score": state.get("score", 0.0),
        "critique": state.get("critique", ""),
        "revision_count": state.get("revision_count", 0),
        "output": state.get("output", ""),
        "skill_version": state.get("skill_version", 1),
        "status": "complete",
    }
    try:
        db.save_run(payload)
    except Exception:
        pass
    memory_update = (
        f"Task: {state.get('task', '')}\n"
        f"Score: {state.get('score', 0.0):.2f}\n"
        f"Critique: {state.get('critique', '')}\n"
        f"Last Output:\n{state.get('output', '')[:2000]}"
    )
    try:
        if hasattr(db, "update_agent_memory"):
            db.update_agent_memory(state["agent_id"], memory_update)
        elif hasattr(db, "save_memory_context"):
            db.save_memory_context(state["agent_id"], memory_update)
        else:
            _HubDbFallback().update_agent_memory(state["agent_id"], memory_update)
    except Exception:
        _HubDbFallback().update_agent_memory(state["agent_id"], memory_update)
    _emit(emit, "node_update", node="save_memory", status="complete", run_id=state.get("run_id"))
    _emit(
        emit,
        "run_completed",
        run_id=state.get("run_id"),
        agent_id=state.get("agent_id"),
        graph=state.get("graph_type"),
        score=state.get("score", 0.0),
        critique=state.get("critique", ""),
        output_preview=state.get("output", "")[:300],
    )
    return {}


def node_plan(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="plan", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(content="Create a concise research plan with 3-7 numbered steps."),
        HumanMessage(content=f"Task:\n{state['task']}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.2, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="plan", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_search(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="search", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Expand the research plan into synthesized findings, assumptions, sources to verify, "
                "and notable risks."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nResearch Plan:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.1, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="search", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_synthesize(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="synthesize", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Synthesize the research into a clear final answer with summary, evidence, "
                "recommendations, and next steps."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nFindings:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.1, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="synthesize", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_wp_plan(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="wp_plan", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Create a WordPress implementation plan covering files, hooks, APIs, data flow, "
                "testing, and deployment concerns."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.1, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="wp_plan", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_wp_implement(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="wp_implement", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Generate a complete WordPress implementation with code, configuration, hooks, "
                "API usage, and operational notes. No placeholders."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nImplementation Plan:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.1, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="wp_implement", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_wp_verify(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="wp_verify", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Verify the WordPress implementation for correctness, security, capability checks, "
                "nonce handling, escaping, and failure modes. Return a verified result."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nImplementation:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.0, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="wp_verify", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_legal_analyze(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="legal_analyze", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Analyze the business-law issue by identifying facts, governing rules, risks, "
                "assumptions, and open questions."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.1, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="legal_analyze", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_legal_draft(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="legal_draft", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Draft the requested business-law document or response in a professional format, "
                "using the analysis as guidance."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nAnalysis:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.2, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="legal_draft", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def node_legal_review(state: dict, emit: callable = None) -> dict:
    _cancel_check(state)
    _emit(emit, "node_update", node="legal_review", status="running", run_id=state.get("run_id"))
    messages = [
        SystemMessage(
            content=(
                "Review the draft for business-law issues, ambiguity, missing protections, "
                "and practical risk. Return a corrected final version or review findings."
            )
        ),
        HumanMessage(content=f"Task:\n{state['task']}\n\nDraft:\n{state.get('output', '')}"),
    ] if LANGGRAPH_OK else []
    output, _ = _invoke(messages, 0.0, "LangGraph not installed - mock output")
    _emit(emit, "node_update", node="legal_review", status="complete", run_id=state.get("run_id"))
    return {"output": output}


def should_revise(state: dict) -> str:
    if state.get("score", 1.0) < 0.75 and state.get("revision_count", 0) < state.get("max_revisions", 2):
        return "revise"
    return "save_memory"


def _wrap(node_fn: Callable[..., dict], emit: Callable[..., None] | None) -> Callable[[dict], dict]:
    def _wrapped(state: dict) -> dict:
        return node_fn(state, emit=emit)

    return _wrapped


def build_reflexion_graph(emit: Callable[..., None] | None = None):
    if not LANGGRAPH_OK:
        raise RuntimeError("LangGraph not installed")
    graph = StateGraph(AgentState)
    graph.add_node("load_memory", _wrap(node_load_memory, emit))
    graph.add_node("act", _wrap(node_act, emit))
    graph.add_node("evaluate", _wrap(node_evaluate, emit))
    graph.add_node("revise", _wrap(node_revise, emit))
    graph.add_node("save_memory", _wrap(node_save_memory, emit))
    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "act")
    graph.add_edge("act", "evaluate")
    graph.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save_memory": "save_memory"})
    graph.add_edge("revise", "act")
    graph.add_edge("save_memory", END)
    return graph.compile()


def build_research_graph(emit: Callable[..., None] | None = None):
    if not LANGGRAPH_OK:
        raise RuntimeError("LangGraph not installed")
    graph = StateGraph(AgentState)
    graph.add_node("load_memory", _wrap(node_load_memory, emit))
    graph.add_node("plan", _wrap(node_plan, emit))
    graph.add_node("search", _wrap(node_search, emit))
    graph.add_node("synthesize", _wrap(node_synthesize, emit))
    graph.add_node("evaluate", _wrap(node_evaluate, emit))
    graph.add_node("revise", _wrap(node_revise, emit))
    graph.add_node("save_memory", _wrap(node_save_memory, emit))
    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "plan")
    graph.add_edge("plan", "search")
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", "evaluate")
    graph.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save_memory": "save_memory"})
    graph.add_edge("revise", "synthesize")
    graph.add_edge("save_memory", END)
    return graph.compile()


def build_wordpress_graph(emit: Callable[..., None] | None = None):
    if not LANGGRAPH_OK:
        raise RuntimeError("LangGraph not installed")
    graph = StateGraph(AgentState)
    graph.add_node("load_memory", _wrap(node_load_memory, emit))
    graph.add_node("wp_plan", _wrap(node_wp_plan, emit))
    graph.add_node("wp_implement", _wrap(node_wp_implement, emit))
    graph.add_node("wp_verify", _wrap(node_wp_verify, emit))
    graph.add_node("evaluate", _wrap(node_evaluate, emit))
    graph.add_node("revise", _wrap(node_revise, emit))
    graph.add_node("save_memory", _wrap(node_save_memory, emit))
    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "wp_plan")
    graph.add_edge("wp_plan", "wp_implement")
    graph.add_edge("wp_implement", "wp_verify")
    graph.add_edge("wp_verify", "evaluate")
    graph.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save_memory": "save_memory"})
    graph.add_edge("revise", "wp_implement")
    graph.add_edge("save_memory", END)
    return graph.compile()


def build_business_law_graph(emit: Callable[..., None] | None = None):
    if not LANGGRAPH_OK:
        raise RuntimeError("LangGraph not installed")
    graph = StateGraph(AgentState)
    graph.add_node("load_memory", _wrap(node_load_memory, emit))
    graph.add_node("legal_analyze", _wrap(node_legal_analyze, emit))
    graph.add_node("legal_draft", _wrap(node_legal_draft, emit))
    graph.add_node("legal_review", _wrap(node_legal_review, emit))
    graph.add_node("evaluate", _wrap(node_evaluate, emit))
    graph.add_node("revise", _wrap(node_revise, emit))
    graph.add_node("save_memory", _wrap(node_save_memory, emit))
    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "legal_analyze")
    graph.add_edge("legal_analyze", "legal_draft")
    graph.add_edge("legal_draft", "legal_review")
    graph.add_edge("legal_review", "evaluate")
    graph.add_conditional_edges("evaluate", should_revise, {"revise": "revise", "save_memory": "save_memory"})
    graph.add_edge("revise", "legal_draft")
    graph.add_edge("save_memory", END)
    return graph.compile()


GRAPH_BUILDERS = {
    "reflexion": build_reflexion_graph,
    "research": build_research_graph,
    "wordpress": build_wordpress_graph,
    "business-law": build_business_law_graph,
}


def run_graph(config: dict, emit: callable = None) -> dict:
    """
    config: {agent_id, project, graph, task, max_revisions, run_id?, cancel_flag?}
    emit: callable(event_type, **data) or None
    Returns final state dict
    """
    graph_name = config.get("graph", "reflexion")
    initial_state = {
        "run_id": config.get("run_id") or uuid.uuid4().hex[:8],
        "agent_id": config.get("agent_id", "unknown-agent"),
        "project": config.get("project", "global"),
        "graph_type": graph_name,
        "task": config.get("task", ""),
        "skill_name": config.get("skill_name") or config.get("agent_id", "unknown-agent").replace("-", "_"),
        "skill_content": "",
        "skill_version": 1,
        "memory_context": "",
        "output": "",
        "score": 0.0,
        "critique": "",
        "revision_count": 0,
        "max_revisions": config.get("max_revisions", 2),
        "messages": [],
        "cancel_flag": config.get("cancel_flag"),
    }
    _emit(
        emit,
        "run_started",
        run_id=initial_state["run_id"],
        agent_id=initial_state["agent_id"],
        graph=graph_name,
        project=initial_state["project"],
    )

    if not LANGGRAPH_OK:
        mock_state = {
            **initial_state,
            "output": "LangGraph not installed - mock output",
            "critique": "LangGraph not installed - mock output",
            "score": 0.0,
        }
        _emit(
            emit,
            "run_completed",
            run_id=mock_state["run_id"],
            agent_id=mock_state["agent_id"],
            graph=mock_state["graph_type"],
            score=mock_state["score"],
            critique=mock_state["critique"],
            output_preview=mock_state["output"],
        )
        return mock_state

    try:
        builder = GRAPH_BUILDERS.get(graph_name, build_reflexion_graph)
        graph = builder(emit=emit)
        final_state = graph.invoke(initial_state)
        return dict(final_state)
    except Exception as exc:
        error_state = {
            **initial_state,
            "output": f"Run failed: {exc}",
            "critique": str(exc),
            "score": 0.0,
        }
        _emit(
            emit,
            "run_failed",
            run_id=initial_state["run_id"],
            agent_id=initial_state["agent_id"],
            graph=graph_name,
            error=str(exc),
        )
        return error_state

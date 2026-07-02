from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from core.auth import get_current_user
from core.database import (
    _create_record, _get_record, _json_loads, _list_records,
    _now_iso, _update_record,
)
from core.hub import hub
from core.models import InezChatRequest

try:
    import hub_db as db
except ImportError:
    db = None  # type: ignore

try:
    import run_events
except ImportError:
    run_events = None  # type: ignore

router = APIRouter()

# Strong references to in-flight background Inez turns. asyncio.create_task holds
# only a weak reference, so without this set the task can be garbage-collected
# mid-run once the request handler returns. Discarded in the task's done callback.
_inflight_turns: set[asyncio.Task] = set()


@router.post("/inez/chat")
async def inez_chat(body: InezChatRequest, response: Response, _: dict = Depends(get_current_user)):
    try:
        from inez_agent import think
    except ImportError:
        raise HTTPException(503, "Inez agent module not available")

    conv_id = body.conversation_id
    if not conv_id:
        conv_id = uuid.uuid4().hex
        _create_record("conversations", {"id": conv_id, "title": body.message[:60], "slug": "inez", "created_at": _now_iso(), "updated_at": _now_iso()})
    else:
        if not _get_record("conversations", conv_id):
            conv_id = uuid.uuid4().hex
            _create_record("conversations", {"id": conv_id, "title": body.message[:60], "slug": "inez", "created_at": _now_iso(), "updated_at": _now_iso()})

    _create_record("messages", {"id": uuid.uuid4().hex, "conversation_id": conv_id, "role": "user", "content": body.message, "agent_id": None, "created_at": _now_iso()})

    history_rows = _list_records("messages", where=["conversation_id = ?"], params=[conv_id], order_by="created_at ASC")
    history = [{"role": r.get("role", "user"), "content": r.get("content", "")} for r in (history_rows or [])]

    loop = asyncio.get_running_loop()
    run_id = uuid.uuid4().hex

    def _inez_emit(event_type: str, **kwargs: Any) -> None:
        event: dict = {"type": event_type, "run_id": run_id, "conversation_id": conv_id}
        if "message" in kwargs:
            event["text"] = kwargs.pop("message")
        event.update(kwargs)
        # Durable event log — the WS is a live tail of this. A dropped socket or a
        # proxy-timed-out HTTP request is recoverable via the replay endpoint.
        if run_events is not None:
            try:
                run_events.append_event(run_id, event_type, event, conversation_id=conv_id)
            except Exception:
                pass
        asyncio.run_coroutine_threadsafe(hub.broadcast(event), loop)

    async def _process_turn() -> None:
        """Run think() and deliver the result off the request path.

        think() is a multi-call LLM pipeline (~40s+ on slow local models); running
        it inline blocked the HTTP response past the ~100s reverse-proxy limit and
        524'd. Instead we return 202 immediately (below) and drive the whole turn
        here: progress + the final answer reach the client over WebSocket, and the
        durable run_events log lets a reconnecting client replay the outcome.
        """
        try:
            result = await loop.run_in_executor(
                hub._executor, lambda: think(body.message, history, emit=_inez_emit)
            )

            inez_message = result.get("inez_message", "")
            dispatches = result.get("dispatches", [])
            needs_agents = result.get("needs_agents", False)
            error = result.get("error")

            message_data: dict = {"id": uuid.uuid4().hex, "conversation_id": conv_id, "role": "assistant", "content": inez_message, "agent_id": "inez-chief-of-staff", "created_at": _now_iso()}
            if result.get("has_citations"):
                message_data["has_citations"] = True
                message_data["citations"] = json.dumps(result.get("citations", []))
                message_data["search_query"] = result.get("search_query")
            _create_record("messages", message_data)
            _update_record("conversations", conv_id, {"updated_at": _now_iso()})

            queued_runs = []
            for dispatch in dispatches:
                agent_id = dispatch.get("agent_id", "")
                project = dispatch.get("project", "")
                graph = dispatch.get("graph", "reflexion")
                task = dispatch.get("task", "")
                if agent_id and task:
                    job_run_id = await hub.submit_job({"agent_id": agent_id, "project": project, "graph": graph, "task": task, "max_revisions": 2, "priority": "high"})
                    queued_runs.append({"run_id": job_run_id, "agent_id": agent_id, "project": project})

            response_data: dict = {"run_id": run_id, "conversation_id": conv_id, "inez_message": inez_message, "dispatches": dispatches, "needs_agents": needs_agents, "queued_runs": queued_runs, "error": error}
            if result.get("has_citations"):
                response_data["has_citations"] = True
                response_data["citations"] = result.get("citations", [])
                response_data["search_query"] = result.get("search_query")
            # Generate follow-up suggestions only after the first exchange to avoid
            # a redundant LLM call on brand-new conversations (first user message has
            # no prior context to generate meaningful follow-ups from).
            if len(history) > 1 and result.get("followup_suggestions"):
                response_data["followup_suggestions"] = result.get("followup_suggestions", [])

            # Deliver the final answer over WebSocket. The frontend leaves the chat
            # in the "thinking" state after the 202 and renders the reply from this
            # `inez_response` event. Also persisted to the durable event log so a
            # dropped socket can replay it.
            _inez_emit("inez_response", message_id=message_data["id"],
                       **{k: v for k, v in response_data.items()
                          if k not in ("run_id", "conversation_id")})
        except Exception as exc:  # never leave the UI stuck in "thinking"
            # Persist a fallback assistant message so the turn is recoverable, then
            # emit inez_response with an error so the client exits the thinking state.
            fallback = "Sorry — something went wrong while processing that. Please try again."
            try:
                err_msg: dict = {"id": uuid.uuid4().hex, "conversation_id": conv_id, "role": "assistant", "content": fallback, "agent_id": "inez-chief-of-staff", "created_at": _now_iso()}
                _create_record("messages", err_msg)
                _update_record("conversations", conv_id, {"updated_at": _now_iso()})
                msg_id = err_msg["id"]
            except Exception:
                msg_id = None
            _inez_emit("inez_response", message_id=msg_id, inez_message=fallback,
                       dispatches=[], needs_agents=False, queued_runs=[], error=str(exc))

    task = loop.create_task(_process_turn())
    _inflight_turns.add(task)
    task.add_done_callback(_inflight_turns.discard)

    # 202 Accepted: the turn is running in the background. The client tracks it via
    # run_id (WS events + the /inez/runs/{run_id}/events replay endpoint) and renders
    # the answer from the `inez_response` WS event, not this body.
    response.status_code = 202
    return {"run_id": run_id, "conversation_id": conv_id, "status": "processing"}


@router.get("/inez/runs/{run_id}/events")
async def inez_run_events(run_id: str, after: int = 0, _: dict = Depends(get_current_user)):
    """Replay a run's durable event log (progress + final message) after a cursor.

    Lets a refreshed tab or a client whose HTTP response was lost recover the
    outcome of an Inez turn instead of hanging on the last progress step.
    """
    if run_events is None:
        return {"run_id": run_id, "events": [], "cursor": after}
    events = run_events.get_events(run_id=run_id, after_id=after)
    cursor = events[-1]["id"] if events else after
    return {"run_id": run_id, "events": events, "cursor": cursor}


@router.get("/inez/conversations/{conversation_id}/events")
async def inez_conversation_events(conversation_id: str, after: int = 0, _: dict = Depends(get_current_user)):
    """Replay by conversation — used on reconnect when the client knows the
    conversation but lost the in-flight run_id."""
    if run_events is None:
        return {"conversation_id": conversation_id, "events": [], "cursor": after}
    events = run_events.get_events(conversation_id=conversation_id, after_id=after)
    cursor = events[-1]["id"] if events else after
    return {"conversation_id": conversation_id, "events": events, "cursor": cursor}


@router.get("/inez/brief")
async def inez_morning_brief(_: dict = Depends(get_current_user)):
    try:
        from inez_agent import generate_morning_brief
    except ImportError:
        raise HTTPException(503, "Inez agent module not available")
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(hub._executor, lambda: generate_morning_brief())


@router.get("/inez/status")
async def inez_status(_: dict = Depends(get_current_user)):
    try:
        from inez_agent import generate_status_report
    except ImportError:
        raise HTTPException(503, "Inez agent module not available")
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(hub._executor, generate_status_report)


@router.get("/inez/memory")
async def inez_memory(conversation_id: Optional[str] = None, _: dict = Depends(get_current_user)):
    from inez_agent import INEZ_AGENT_ID
    short_term: list[dict] = []
    if conversation_id:
        rows = _list_records("messages", where=["conversation_id = ?"], params=[conversation_id], order_by="created_at ASC") or []
        short_term = [{"role": r.get("role", "user"), "content": r.get("content", ""), "created_at": r.get("created_at", "")} for r in rows[-20:]]

    raw_facts = (db.get_memory(INEZ_AGENT_ID) if db and hasattr(db, "get_memory") else []) or []
    saved_facts = [{"key": m["key"], "value": m["value"], "updated_at": m.get("updated_at", "")} for m in raw_facts if not m["key"].startswith("exchange_")]

    all_convs = _list_records("conversations", order_by="updated_at DESC") or []
    sessions_by_date: dict[str, list[dict]] = {}
    for conv in all_convs:
        date_str = (conv.get("updated_at") or conv.get("created_at") or "")[:10]
        if date_str:
            sessions_by_date.setdefault(date_str, []).append({"id": conv.get("id"), "title": conv.get("title", "Conversation"), "slug": conv.get("slug", ""), "updated_at": conv.get("updated_at", "")})

    daily_sessions = [{"date": d, "conversations": c, "count": len(c)} for d, c in sorted(sessions_by_date.items(), reverse=True)]
    return {"short_term": short_term, "saved_facts": saved_facts, "daily_sessions": daily_sessions}


@router.delete("/inez/memory/facts/{key}")
async def delete_inez_fact(key: str, _: dict = Depends(get_current_user)):
    from inez_agent import INEZ_AGENT_ID
    if db and hasattr(db, "get_conn"):
        with db.get_conn() as conn:
            conn.execute("DELETE FROM agent_memory WHERE agent_id = ? AND key = ?", (INEZ_AGENT_ID, key))
    return {"deleted": key}



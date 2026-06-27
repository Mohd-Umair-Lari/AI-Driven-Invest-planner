"""FastAPI chat routes: advisor chat, RAG chat, session management."""

from typing import List

from fastapi import APIRouter, Body, HTTPException, Path as FPath, Query

from api.schemas import AdvisorChatRequest
from db import collection, memory
from orchestrator.ai_orchestrator import AIOrchestrator

router = APIRouter()


def _get_orchestrator() -> AIOrchestrator:
    from db import conversations_col
    return AIOrchestrator(collection, conversations_col)


# ------------------------------------------------------------------
# Advisor chat
# ------------------------------------------------------------------
@router.post("/api/advisor/chat", tags=["AI Advisor"])
async def advisor_chat(body: AdvisorChatRequest):
    ctx = body.context

    if body.session_id and body.session_id.strip():
        session_id = body.session_id.strip()
    else:
        session_id = f"{body.email}-session"

    extra = {
        "income": ctx.monthly_income if ctx else 0,
        "expenses": ctx.monthly_expenses if ctx else 0,
        "debt": ctx.debt if ctx else 0,
        "risk": ctx.risk_appetite if ctx else "moderate",
    }

    orchestrator = _get_orchestrator()
    result = orchestrator.run(
        email=body.email,
        query=body.question,
        session_id=session_id,
        extra_context=extra,
    )

    if not result.get("success", True):
        raise HTTPException(500, result.get("response", "AI error"))

    return {**result, "user_email": body.email, "session_id": session_id}


@router.post("/api/rag/chat", tags=["AI Advisor"])
async def rag_chat(body: AdvisorChatRequest):
    return await advisor_chat(body)


# ------------------------------------------------------------------
# Session management
# ------------------------------------------------------------------
@router.get("/api/chat/sessions/{email}", tags=["Chat History"])
async def get_sessions(email: str = FPath(...)):
    return {"sessions": memory.list_sessions(email)}


@router.get("/api/chat/history/{email}/{session_id}", tags=["Chat History"])
async def get_history(email: str = FPath(...), session_id: str = FPath(...)):
    session = memory.get_session(email, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.delete("/api/chat/history/{email}/{session_id}", tags=["Chat History"])
async def clear_session(email: str = FPath(...), session_id: str = FPath(...)):
    memory.clear_session(email, session_id)
    return {"status": "cleared"}


@router.delete("/api/chat/history/{email}", tags=["Chat History"])
async def clear_all_sessions(email: str = FPath(...)):
    memory.clear_all(email)
    return {"status": "all sessions cleared"}


# ------------------------------------------------------------------
# Delete specific / batch sessions (query-param based)
# ------------------------------------------------------------------
@router.delete("/api/advisor/chat", tags=["AI Advisor"])
async def delete_chat(
    email: str = Query(..., description="User email"),
    session_id: str = Query(..., description="Session ID to delete"),
):
    """Delete the stored conversation for a given user and session."""
    existing = memory.get_session(email, session_id)
    if not existing:
        raise HTTPException(404, "Conversation not found")
    memory.clear_session(email, session_id)
    return {"status": "deleted", "email": email, "session_id": session_id}


@router.delete("/api/advisor/chat/batch", tags=["AI Advisor"])
async def delete_chat_batch(
    email: str = Query(..., description="User email"),
    session_ids: List[str] = Body(..., description="List of session IDs to delete"),
):
    """Delete several chat sessions for a user in one request."""
    deleted = []
    for sid in session_ids:
        if memory.get_session(email, sid):
            memory.clear_session(email, sid)
            deleted.append(sid)
    if not deleted:
        raise HTTPException(404, "No matching conversations found for deletion")
    return {"status": "deleted_batch", "email": email, "deleted_sessions": deleted}

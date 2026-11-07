from fastapi import APIRouter, HTTPException
from api.schemas import AdvisorChatRequest
from db import collection, conversations_col
from orchestrator.ai_orchestrator import AIOrchestrator

router = APIRouter()

@router.post("/api/advisor/chat", tags=["AI Advisor"])
async def chat_advisor(body: AdvisorChatRequest):
    try:
        ctx = body.context
        session_id = body.session_id.strip() if body.session_id and body.session_id.strip() else f"{body.email}-session"
        result = AIOrchestrator(collection, conversations_col).run(
            email=body.email,
            query=body.question,
            session_id=session_id,
            extra_context={
                "income": ctx.monthly_income if ctx else 0,
                "expenses": ctx.monthly_expenses if ctx else 0,
                "debt": ctx.debt if ctx else 0,
                "risk": ctx.risk_appetite if ctx else "moderate",
            },
        )
        if not result.get("success", True):
            raise HTTPException(status_code=502, detail=result.get("response", "AI service error"))
        return {**result, "user_email": body.email, "session_id": session_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to generate advisor response") from exc

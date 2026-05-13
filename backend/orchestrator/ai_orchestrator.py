"""
orchestrator/ai_orchestrator.py
--------------------------------
Central AI brain. Coordinates the full pipeline:
  1. Classify intent
  2. Retrieve user context (RAG)
  3. Select the right agent
  4. Construct grounded prompt
  5. Call LLM
  6. Format and return response

Designed to be provider-agnostic: swap Groq → Ollama via settings.
"""
from typing import Any, Dict, Optional

try:
    from loguru import logger
except ImportError:
    import logging as _l; logger = _l.getLogger("orchestrator")


from orchestrator.intent_classifier import classify_intent, Intent
from orchestrator.response_formatter import format_response
from rag.rag_chain import run_rag_chain
from memory.conversation_memory import ConversationMemory


class AIOrchestrator:
    """
    Stateless orchestrator — instantiated per request.
    All state lives in MongoDB (via memory module).
    """

    def __init__(self, collection, conversations_col):
        self.collection = collection
        self.memory     = ConversationMemory(conversations_col)

    def run(
        self,
        email: str,
        query: str,
        session_id: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full orchestration pipeline.
        Returns a standardized response dict.
        """

        # ── 1. Classify intent ───────────────────────────────────
        classified = classify_intent(query)
        logger.info(f"Intent: {classified.intent} | Agent: {classified.agent} | User: {email}")

        # ── 2. Retrieve conversation history ─────────────────────
        history = []
        if session_id:
            history = self.memory.get_recent(email, session_id, limit=6)

        # ── 3. Run RAG pipeline ──────────────────────────────────
        result = run_rag_chain(
            collection=self.collection,
            email=email,
            question=query,
            extra_context=extra_context or {},
            conversation_history=history,
            intent=classified,
        )

        # ── 4. Format response ───────────────────────────────────
        formatted = format_response(
            raw_response=result.get("response", ""),
            intent=classified.intent,
            context_used=result.get("context_used", ""),
        )

        # ── 5. Store to memory ───────────────────────────────────
        if session_id:
            self.memory.append(
                email=email,
                session_id=session_id,
                user_msg=query,
                ai_msg=formatted["response"],
                intent=classified.intent.value,
                context_used=result.get("context_used", ""),
            )

        return {
            "success":      result.get("success", True),
            "response":     formatted["response"],
            "intent":       classified.intent.value,
            "agent":        classified.agent,
            "suggestions":  formatted.get("suggestions", []),
            "context_used": result.get("context_used", ""),
            "rag":          True,
            "session_id":   session_id,
        }


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

        classified = classify_intent(query)
        logger.info(f"Intent: {classified.intent} | Agent: {classified.agent} | User: {email}")

        history = []
        if session_id:
            # Retrieve recent messages (default 16) then enforce a token‑based window.
            raw_history = self.memory.get_recent(email, session_id, limit=16)
            # Simple token estimate: each word ~= 1 token.
            max_tokens = 1500  # adjust as needed for your model's context budget
            token_count = 0
            clipped = []
            # Walk backwards (most recent first) and keep adding until limit.
            for msg in reversed(raw_history):
                est = len(msg["content"].split())
                if token_count + est > max_tokens:
                    break
                token_count += est
                clipped.insert(0, msg)  # prepend to preserve order
            history = clipped

        result = run_rag_chain(
            collection=self.collection,
            email=email,
            question=query,
            extra_context=extra_context or {},
            conversation_history=history,
            intent=classified,
        )

        formatted = format_response(
            raw_response=result.get("response", ""),
            intent=classified.intent,
            context_used=result.get("context_used", ""),
        )

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

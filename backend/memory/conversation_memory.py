"""
memory/conversation_memory.py
------------------------------
Stores and retrieves conversation history per user session in MongoDB.
Enables multi-turn context — the AI "remembers" what was said earlier.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional


class ConversationMemory:
    """
    MongoDB-backed conversation memory.
    Each session = one document in the `conversations` collection.
    """

    def __init__(self, conversations_col):
        self.col = conversations_col

    # ── Read ───────────────────────────────────────────────────────

    def get_session(self, email: str, session_id: str) -> Optional[Dict]:
        return self.col.find_one(
            {"email": email, "session_id": session_id},
            {"_id": 0},
        )

    def get_recent(
        self, email: str, session_id: str, limit: int = 6
    ) -> List[Dict[str, str]]:
        """
        Returns the last `limit` messages as a simple list of
        {"role": "user"|"assistant", "content": "..."} dicts
        — compatible with the OpenAI messages format.
        """
        session = self.get_session(email, session_id)
        if not session:
            return []
        messages = session.get("messages", [])
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-limit:]
        ]

    def list_sessions(self, email: str) -> List[Dict]:
        """List all conversation sessions for a user."""
        return list(
            self.col.find(
                {"email": email},
                {"_id": 0, "session_id": 1, "created_at": 1, "updated_at": 1,
                 "messages": {"$slice": -1}},   # only last message for preview
            ).sort("updated_at", -1).limit(20)
        )

    # ── Write ──────────────────────────────────────────────────────

    def append(
        self,
        email: str,
        session_id: str,
        user_msg: str,
        ai_msg: str,
        intent: str = "",
        context_used: str = "",
    ):
        """Upsert messages into the session document."""
        now = datetime.utcnow().isoformat()
        messages = [
            {"role": "user",      "content": user_msg, "timestamp": now},
            {"role": "assistant", "content": ai_msg,   "timestamp": now,
             "intent": intent, "context_used": context_used},
        ]
        self.col.update_one(
            {"email": email, "session_id": session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$set":  {"updated_at": now, "email": email},
                "$setOnInsert": {"created_at": now, "session_id": session_id},
            },
            upsert=True,
        )

    def clear_session(self, email: str, session_id: str):
        """Delete a specific session."""
        self.col.delete_one({"email": email, "session_id": session_id})

    def clear_all(self, email: str):
        """Delete all sessions for a user."""
        self.col.delete_many({"email": email})


from datetime import datetime
from typing import Any, Dict, List, Optional


def _session_title(messages: List[Dict], fallback: str = "New conversation") -> str:
    for m in messages:
        if m.get("role") == "user" and m.get("content"):
            text = m["content"].strip().replace("\n", " ")
            return (text[:48] + "…") if len(text) > 48 else text
    return fallback


class ConversationMemory:

    def __init__(self, conversations_col):
        self.col = conversations_col

    def get_session(self, email: str, session_id: str) -> Optional[Dict]:
        return self.col.find_one(
            {"email": email, "session_id": session_id},
            {"_id": 0},
        )

    def get_recent(
        self, email: str, session_id: str, limit: int = 6
    ) -> List[Dict[str, str]]:

        session = self.get_session(email, session_id)
        if not session:
            return []
        messages = session.get("messages", [])
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages[-limit:]
        ]

    def list_sessions(self, email: str, limit: int = 30) -> List[Dict]:
        sessions = []
        cursor = self.col.find(
            {"email": email},
            {"_id": 0, "session_id": 1, "created_at": 1, "updated_at": 1,
             "title": 1, "messages": 1},
        ).sort("updated_at", -1).limit(limit)

        for doc in cursor:
            messages = doc.get("messages") or []
            last = messages[-1] if messages else None
            sessions.append({
                "session_id": doc.get("session_id"),
                "title": doc.get("title") or _session_title(messages),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "message_count": len(messages),
                "preview": (last.get("content", "")[:80] if last else ""),
            })
        return sessions

    def append(
        self,
        email: str,
        session_id: str,
        user_msg: str,
        ai_msg: str,
        intent: str = "",
        context_used: str = "",
    ):

        now = datetime.utcnow().isoformat()
        messages = [
            {"role": "user",      "content": user_msg, "timestamp": now},
            {"role": "assistant", "content": ai_msg,   "timestamp": now,
             "intent": intent, "context_used": context_used},
        ]
        existing = self.get_session(email, session_id)
        title_update = {}
        if not existing or not existing.get("title"):
            title_update["title"] = _session_title(
                (existing or {}).get("messages", []) + [{"role": "user", "content": user_msg}]
            )

        self.col.update_one(
            {"email": email, "session_id": session_id},
            {
                "$push": {"messages": {"$each": messages}},
                "$set":  {"updated_at": now, "email": email, **title_update},
                "$setOnInsert": {"created_at": now, "session_id": session_id},
            },
            upsert=True,
        )

    def clear_session(self, email: str, session_id: str):

        self.col.delete_one({"email": email, "session_id": session_id})

    def clear_all(self, email: str):

        self.col.delete_many({"email": email})

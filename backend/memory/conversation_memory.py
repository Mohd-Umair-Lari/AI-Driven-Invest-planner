
from datetime import datetime
from typing import Any, Dict, List, Optional

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

    def list_sessions(self, email: str) -> List[Dict]:

        return list(
            self.col.find(
                {"email": email},
                {"_id": 0, "session_id": 1, "created_at": 1, "updated_at": 1,
                 "messages": {"$slice": -1}},
            ).sort("updated_at", -1).limit(20)
        )

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

        self.col.delete_one({"email": email, "session_id": session_id})

    def clear_all(self, email: str):

        self.col.delete_many({"email": email})

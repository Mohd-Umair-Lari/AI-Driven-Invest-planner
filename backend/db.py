"""
Shared database module.

Provides centralized access to MongoDB collections, helper utilities,
and shared service instances (ConversationMemory, MongoVectorStore).

All route modules should import from here instead of main.py.
"""

import os
import threading
from datetime import datetime

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()





MONGO_URI = os.getenv("MONGO_URI", "").strip()
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set.")

DB_NAME = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()

_mongo = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10_000,
    connectTimeoutMS=10_000,
    socketTimeoutMS=10_000,
)
_mongo.admin.command("ping")

db = _mongo[DB_NAME]
collection = db[COLLECTION_NAME]
conversations_col = db["conversations"]
documents_col = db["documents"]





from memory.conversation_memory import ConversationMemory
from rag.mongo_vector_store import MongoVectorStore

memory = ConversationMemory(conversations_col)
vector_store = MongoVectorStore(db)






def serialize(doc: dict) -> dict:
    """Convert a MongoDB document to a JSON-safe dict, stripping password."""
    doc = dict(doc)
    doc["_id"] = str(doc.get("_id", ""))
    doc.pop("password", None)
    return doc


def ensure_onboarding(email: str, user: dict) -> dict:
    """Ensure the user document has an onboarding sub-document."""
    if "onboarding" not in user:
        ob = {
            "status": "not_started",
            "current_step": 0,
            "last_updated": datetime.utcnow().isoformat(),
        }
        collection.update_one({"email": email}, {"$set": {"onboarding": ob}})
        user["onboarding"] = ob
    return user


def get_num(obj, *keys, default=0.0):
    """Safely extract a numeric value from a dict, trying multiple keys."""
    for key in keys:
        val = (obj or {}).get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    return default






from rag.indexer import seed_knowledge_base, index_user_profile


def _seed_kb_async():
    try:
        n = seed_knowledge_base(vector_store)
        if n > 0:
            print(f"Knowledge base seeded: {n} chunks")
        else:
            print("Knowledge base already seeded or embedding unavailable")
    except Exception as e:
        print(f"Knowledge base seeding skipped: {e}")


threading.Thread(target=_seed_kb_async, daemon=True).start()


def trigger_user_indexing(email: str):
    """Index a user's profile for RAG in a background thread."""
    def _do_index():
        try:
            user = collection.find_one({"email": email})
            if user:
                index_user_profile(vector_store, user)
        except Exception as e:
            print(f"User indexing failed for {email}: {e}")

    threading.Thread(target=_do_index, daemon=True).start()

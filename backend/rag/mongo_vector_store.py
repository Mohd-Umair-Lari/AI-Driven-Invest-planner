"""
rag/mongo_vector_store.py
--------------------------
MongoDB Atlas Vector Search integration.
- Replaces ChromaDB — zero native build dependencies.
- Stores embeddings directly in MongoDB collections alongside user data.
- Uses $vectorSearch aggregation pipeline (Atlas Search required).
- Falls back gracefully to keyword retrieval if vector search index not yet created.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging as _l; logger = _l.getLogger("mongo_vector_store")

# ── Collection names ────────────────────────────────────────────
KNOWLEDGE_COL = "financial_knowledge"   # Finance concepts knowledge base
USER_CHUNKS_COL = "user_embeddings"     # Per-user profile + transaction chunks

# ── Vector search index name (must be created in Atlas UI once) ─
VECTOR_INDEX_NAME = "finpass_vector_index"


class MongoVectorStore:
    """
    Atlas Vector Search wrapper.
    Falls back to text-regex search if the vector index doesn't exist yet.
    """

    def __init__(self, db):
        self.db             = db
        self.knowledge_col  = db[KNOWLEDGE_COL]
        self.user_col       = db[USER_CHUNKS_COL]
        self._index_ready   = None  # lazily detected

    # ── Upsert knowledge chunks ─────────────────────────────────

    def upsert_knowledge(self, doc_id: str, text: str, embedding: List[float], metadata: Dict = None):
        """Store a financial knowledge chunk with its embedding."""
        self.knowledge_col.update_one(
            {"doc_id": doc_id},
            {"$set": {
                "doc_id":    doc_id,
                "text":      text,
                "embedding": embedding,
                "metadata":  metadata or {},
                "updated_at": datetime.utcnow(),
            }},
            upsert=True,
        )

    def upsert_user_chunk(self, email: str, chunk_id: str, text: str, embedding: List[float], metadata: Dict = None):
        """Store a user-specific chunk (profile summary, transaction, etc.) with embedding."""
        self.user_col.update_one(
            {"email": email, "chunk_id": chunk_id},
            {"$set": {
                "email":      email,
                "chunk_id":   chunk_id,
                "text":       text,
                "embedding":  embedding,
                "metadata":   metadata or {},
                "updated_at": datetime.utcnow(),
            }},
            upsert=True,
        )

    def delete_user_chunks(self, email: str):
        """Remove all embedded chunks for a user (called on profile update)."""
        self.user_col.delete_many({"email": email})

    # ── Vector search ───────────────────────────────────────────

    def _vector_search(self, collection_name: str, query_embedding: List[float],
                       filter_dict: Dict = None, limit: int = 5) -> List[Dict]:
        """Run Atlas $vectorSearch aggregation."""
        pipeline = [
            {
                "$vectorSearch": {
                    "index":         VECTOR_INDEX_NAME,
                    "path":          "embedding",
                    "queryVector":   query_embedding,
                    "numCandidates": limit * 10,
                    "limit":         limit,
                    **({"filter": filter_dict} if filter_dict else {}),
                }
            },
            {
                "$project": {
                    "text":     1,
                    "metadata": 1,
                    "doc_id":   1,
                    "score":    {"$meta": "vectorSearchScore"},
                    "_id":      0,
                }
            },
        ]
        try:
            col = self.db[collection_name]
            results = list(col.aggregate(pipeline))
            return results
        except Exception as e:
            logger.warning(f"Vector search failed (index may not exist yet): {e}")
            return []

    def search_knowledge(self, query_embedding: List[float], limit: int = 4) -> List[str]:
        """Semantic search over the financial knowledge base."""
        results = self._vector_search(KNOWLEDGE_COL, query_embedding, limit=limit)
        return [r["text"] for r in results if r.get("score", 0) > 0.5]

    def search_user_chunks(self, email: str, query_embedding: List[float], limit: int = 3) -> List[str]:
        """Semantic search over a specific user's embedded chunks."""
        results = self._vector_search(
            USER_CHUNKS_COL,
            query_embedding,
            filter_dict={"email": email},
            limit=limit,
        )
        return [r["text"] for r in results if r.get("score", 0) > 0.5]

    # ── Fallback text search (when index not yet ready) ─────────

    def keyword_search_knowledge(self, query: str, limit: int = 3) -> List[str]:
        """Text-based fallback when vector index not yet configured."""
        words = [w for w in query.lower().split() if len(w) > 3]
        if not words:
            return []
        regex = "|".join(words[:5])
        docs = self.knowledge_col.find(
            {"text": {"$regex": regex, "$options": "i"}},
            {"text": 1, "_id": 0}
        ).limit(limit)
        return [d["text"] for d in docs]

    # ── Stats ───────────────────────────────────────────────────

    def knowledge_count(self) -> int:
        return self.knowledge_col.count_documents({})

    def user_chunk_count(self, email: str) -> int:
        return self.user_col.count_documents({"email": email})

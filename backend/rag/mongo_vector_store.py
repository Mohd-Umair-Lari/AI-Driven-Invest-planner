
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging as _l; logger = _l.getLogger("mongo_vector_store")

KNOWLEDGE_COL = "financial_knowledge"
USER_CHUNKS_COL = "user_embeddings"

VECTOR_INDEX_NAME = "finpass_vector_index"

class MongoVectorStore:

    def __init__(self, db):
        self.db             = db
        self.knowledge_col  = db[KNOWLEDGE_COL]
        self.user_col       = db[USER_CHUNKS_COL]
        self._index_ready   = None

    def upsert_knowledge(self, doc_id: str, text: str, embedding: List[float], metadata: Dict = None):

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

        self.user_col.delete_many({"email": email})

    def _vector_search(self, collection_name: str, query_embedding: List[float],
                       filter_dict: Dict = None, limit: int = 5) -> List[Dict]:

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

        results = self._vector_search(KNOWLEDGE_COL, query_embedding, limit=limit)
        return [r["text"] for r in results if r.get("score", 0) > 0.5]

    def search_user_chunks(self, email: str, query_embedding: List[float], limit: int = 3) -> List[str]:

        results = self._vector_search(
            USER_CHUNKS_COL,
            query_embedding,
            filter_dict={"email": email},
            limit=limit,
        )
        return [r["text"] for r in results if r.get("score", 0) > 0.5]

    def keyword_search_knowledge(self, query: str, limit: int = 3) -> List[str]:

        words = [w for w in query.lower().split() if len(w) > 3]
        if not words:
            return []
        regex = "|".join(words[:5])
        docs = self.knowledge_col.find(
            {"text": {"$regex": regex, "$options": "i"}},
            {"text": 1, "_id": 0}
        ).limit(limit)
        return [d["text"] for d in docs]

    def knowledge_count(self) -> int:
        return self.knowledge_col.count_documents({})

    def user_chunk_count(self, email: str) -> int:
        return self.user_col.count_documents({"email": email})

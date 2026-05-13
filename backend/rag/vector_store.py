"""
rag/vector_store.py
--------------------
ChromaDB abstraction layer.
- Graceful fallback: if chromadb is not installed, vector search is skipped.
- All user data lives in MongoDB. This adds *semantic search* on top.
- Swap-ready: replace the _ChromaBackend with Pinecone/Qdrant without
  touching any calling code.
"""
from typing import Any, Dict, List, Optional
from loguru import logger


class _ChromaBackend:
    """Thin wrapper around ChromaDB client."""

    def __init__(self, persist_dir: str, collection_name: str):
        import chromadb
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._col    = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, ids: List[str], embeddings: List[List[float]],
               documents: List[str], metadatas: List[Dict]):
        self._col.upsert(ids=ids, embeddings=embeddings,
                         documents=documents, metadatas=metadatas)

    def query(self, embedding: List[float], n_results: int = 5,
              where: Optional[Dict] = None) -> List[Dict]:
        kwargs = {"query_embeddings": [embedding], "n_results": n_results,
                  "include": ["documents", "metadatas", "distances"]}
        if where:
            kwargs["where"] = where
        res = self._col.query(**kwargs)
        results = []
        for i, doc in enumerate(res["documents"][0]):
            results.append({
                "document": doc,
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i],
            })
        return results

    def delete_by_email(self, email: str):
        self._col.delete(where={"email": email})


class VectorStore:
    """
    Public interface. Import this — never import _ChromaBackend directly.
    Falls back silently if chromadb is unavailable (HF free tier etc.).
    """

    def __init__(self):
        self._backend: Optional[_ChromaBackend] = None
        self._available = False
        try:
            from config.settings import get_settings
            s = get_settings()
            self._backend   = _ChromaBackend(s.CHROMA_PERSIST_DIR, s.CHROMA_COLLECTION)
            self._available = True
            logger.info("✅ ChromaDB vector store ready")
        except Exception as e:
            logger.warning(f"⚠️  ChromaDB unavailable — vector search disabled: {e}")

    @property
    def available(self) -> bool:
        return self._available

    def upsert_chunks(
        self,
        email: str,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ):
        if not self._available:
            return
        ids       = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"email": email, "doc_id": doc_id, "chunk": i}
                     for i in range(len(chunks))]
        self._backend.upsert(ids, embeddings, chunks, metadatas)

    def search(
        self,
        embedding: List[float],
        email: Optional[str] = None,
        n_results: int = 5,
    ) -> List[str]:
        """Returns top-k relevant text chunks."""
        if not self._available:
            return []
        where = {"email": email} if email else None
        results = self._backend.query(embedding, n_results, where)
        # Filter by distance threshold (cosine < 0.5 = relevant)
        return [r["document"] for r in results if r["distance"] < 0.5]

    def delete_user_data(self, email: str):
        if self._available:
            self._backend.delete_by_email(email)


# Singleton — import this everywhere
vector_store = VectorStore()

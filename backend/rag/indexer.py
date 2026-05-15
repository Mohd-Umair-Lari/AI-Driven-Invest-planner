"""
rag/indexer.py
--------------
Orchestrates embedding + storage for:
1. Knowledge base seeding (run once / on startup if not already seeded)
2. User profile indexing (run on signup / profile update)
3. Transaction indexing (run when transactions are added)
"""
from typing import Any, Dict, List
from datetime import datetime

try:
    from loguru import logger
except ImportError:
    import logging as _l; logger = _l.getLogger("indexer")

from rag.embedder import embed_text, embed_batch, is_available
from rag.knowledge_base import get_all_chunks
from rag.mongo_vector_store import MongoVectorStore


# ── Knowledge base seeding ─────────────────────────────────────

def seed_knowledge_base(vector_store: MongoVectorStore, force: bool = False) -> int:
    """
    Seed the financial knowledge base into MongoDB.
    Skips if already seeded (checks count). Use force=True to re-seed.
    Returns number of chunks seeded.
    """
    if not is_available():
        logger.warning("Embedding not available — knowledge base seeding skipped.")
        return 0

    existing = vector_store.knowledge_count()
    chunks   = get_all_chunks()

    if existing >= len(chunks) and not force:
        logger.info(f"Knowledge base already seeded ({existing} chunks). Skipping.")
        return 0

    logger.info(f"Seeding {len(chunks)} knowledge chunks into MongoDB...")
    texts = [text for _, text in chunks]
    embeddings = embed_batch(texts)

    seeded = 0
    for (doc_id, text), embedding in zip(chunks, embeddings):
        if embedding is None:
            logger.warning(f"Embedding failed for chunk '{doc_id}' — skipping.")
            continue
        vector_store.upsert_knowledge(
            doc_id=doc_id,
            text=text,
            embedding=embedding,
            metadata={"source": "finpass_knowledge_base", "seeded_at": datetime.utcnow().isoformat()},
        )
        seeded += 1

    logger.info(f"Knowledge base seeding complete: {seeded}/{len(chunks)} chunks stored.")
    return seeded


# ── User profile indexing ──────────────────────────────────────

def _build_user_narrative(user: Dict[str, Any]) -> str:
    """
    Converts a user's MongoDB document into a rich text narrative
    that can be embedded and searched semantically.
    """
    fin  = user.get("financials") or {}
    inv  = user.get("investments") or {}
    goal = user.get("Goal") or {}
    name = user.get("Name", "User")
    age  = user.get("Age", "")
    emp  = user.get("employment-status", "")

    income   = float(fin.get("monthly-income") or 0)
    expenses = float(fin.get("monthly-expenses") or 0)
    debt     = float(fin.get("debt") or 0)
    surplus  = income - expenses
    sav_rate = round(surplus / income * 100, 1) if income > 0 else 0

    invest_amt  = float(inv.get("invest-amt") or 0)
    risk_opt    = inv.get("risk-opt", "moderate")
    invest_mode = inv.get("prefered-mode", "Monthly SIP")

    goal_name  = goal.get("goal", "wealth building")
    target_amt = float(goal.get("target-amt") or 0)
    timeline   = goal.get("target-time", "")

    return (
        f"{name} is a {age}-year-old {emp} earning ₹{income:,.0f} per month. "
        f"Monthly expenses are ₹{expenses:,.0f}, leaving a surplus of ₹{surplus:,.0f} "
        f"(savings rate: {sav_rate}%). Outstanding debt is ₹{debt:,.0f}. "
        f"Current SIP investment: ₹{invest_amt:,.0f}/month via {invest_mode}. "
        f"Risk appetite: {risk_opt}. "
        f"Financial goal: {goal_name} with target of ₹{target_amt:,.0f} in {timeline} months."
    )


def _build_transaction_chunk(transactions: List[Dict], max_txns: int = 20) -> str:
    """Build a text chunk summarising recent transactions."""
    if not transactions:
        return ""
    recent = transactions[-max_txns:]
    lines = ["Recent transactions:"]
    for t in recent:
        date  = t.get("date", "")[:10]
        cat   = t.get("category", "Other")
        desc  = t.get("description", "")
        amt   = abs(t.get("amount", 0))
        ttype = t.get("type", "debit")
        sign  = "-" if ttype == "debit" else "+"
        lines.append(f"{date} | {cat} | {sign}₹{amt:,.0f} | {desc[:50]}")
    return "\n".join(lines)


def index_user_profile(vector_store: MongoVectorStore, user: Dict[str, Any]) -> bool:
    """
    Embed and store a user's financial profile + transactions.
    Called on signup, profile update, or transaction addition.
    Returns True on success.
    """
    if not is_available():
        logger.debug("Embedding not available — user indexing skipped.")
        return False

    email = user.get("email")
    if not email:
        return False

    # Remove old chunks for this user
    vector_store.delete_user_chunks(email)

    chunks_to_index = []

    # Chunk 1: Full profile narrative
    narrative = _build_user_narrative(user)
    if narrative:
        chunks_to_index.append(("profile_narrative", narrative))

    # Chunk 2: Transaction history
    transactions = user.get("transactions", [])
    txn_text = _build_transaction_chunk(transactions)
    if txn_text:
        chunks_to_index.append(("transaction_history", txn_text))

    # Chunk 3: Goal summary
    goal = user.get("Goal") or {}
    if goal:
        goal_text = (
            f"Financial goal: {goal.get('goal', 'N/A')}. "
            f"Target: ₹{float(goal.get('target-amt', 0)):,.0f}. "
            f"Timeline: {goal.get('target-time', 'N/A')} months. "
            f"Risk: {goal.get('risk', 'moderate')}."
        )
        chunks_to_index.append(("goal_summary", goal_text))

    if not chunks_to_index:
        return False

    texts = [text for _, text in chunks_to_index]
    embeddings = embed_batch(texts)

    indexed = 0
    for (chunk_id, text), embedding in zip(chunks_to_index, embeddings):
        if embedding is None:
            continue
        vector_store.upsert_user_chunk(
            email=email,
            chunk_id=chunk_id,
            text=text,
            embedding=embedding,
            metadata={"type": chunk_id, "indexed_at": datetime.utcnow().isoformat()},
        )
        indexed += 1

    logger.info(f"User '{email}' indexed: {indexed}/{len(chunks_to_index)} chunks.")
    return indexed > 0

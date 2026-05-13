"""
rag/rag_chain.py  (v2)
-----------------------
Full RAG pipeline — now accepts conversation history and classified intent
so the LLM has multi-turn context and the right focus.

MongoDB is the sole store for user data. ChromaDB (optional) adds
semantic search on top — falls back gracefully if not configured.
"""
import re
from typing import Any, Dict, List, Optional

from ai.groq_client import generate_response
from rag.retriever import retrieve_user_context, retrieve_transactions_by_category
from rag.context_builder import build_financial_context, build_category_context

# ── Category keywords ───────────────────────────────────────────
_CATEGORY_KEYWORDS = [
    "food", "groceries", "grocery", "dining", "restaurant",
    "rent", "housing", "home",
    "transport", "travel", "commute", "fuel", "cab", "uber",
    "entertainment", "movies", "streaming",
    "shopping", "clothes", "clothing",
    "medical", "health", "hospital", "medicine",
    "education", "school", "tuition",
    "utilities", "electricity", "water", "internet", "phone",
    "insurance", "emi", "loan",
]


def _detect_category(question: str) -> Optional[str]:
    q = question.lower()
    for kw in _CATEGORY_KEYWORDS:
        if kw in q:
            return kw
    return None


def _build_system_prompt(context: str, history: List[Dict[str, str]]) -> str:
    """
    Builds the grounded system prompt.
    Injects conversation history so the model can do multi-turn reasoning.
    """
    history_block = ""
    if history:
        lines = []
        for m in history[-6:]:   # last 6 messages max
            role  = "User" if m["role"] == "user" else "FinPass AI"
            lines.append(f"{role}: {m['content']}")
        history_block = "\n--- CONVERSATION HISTORY ---\n" + "\n".join(lines) + "\n---\n\n"

    return (
        f"You are FinPass AI, a precise and honest personal finance advisor.\n\n"
        f"RULES:\n"
        f"- Answer ONLY using the financial data provided below.\n"
        f"- Do NOT invent numbers. If the data is missing, say so.\n"
        f"- Use ₹ for Indian Rupees.\n"
        f"- Cite exact numbers. Be concise (2-4 sentences unless analysis requested).\n"
        f"- If spending is high, suggest one concrete improvement.\n\n"
        f"{history_block}"
        f"--- RETRIEVED FINANCIAL DATA ---\n{context}\n--- END DATA ---"
    )


def run_rag_chain(
    collection,
    email: str,
    question: str,
    extra_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    intent=None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline.
    Returns standardized dict consumed by AIOrchestrator.
    """

    # ── 1. Retrieve from MongoDB ─────────────────────────────────
    ctx = retrieve_user_context(collection, email)

    # Merge frontend-supplied overrides
    if extra_context:
        ctx.update({k: v for k, v in extra_context.items() if v})

    if not ctx:
        return {
            "success":      False,
            "response":     "I couldn't find your financial data. Please complete your profile.",
            "context_used": "none",
            "rag":          True,
        }

    # ── 2. Build context string ──────────────────────────────────
    # Check if intent gives us a specific category focus
    detected_category = None
    if intent and hasattr(intent, "entities"):
        detected_category = intent.entities.get("category")
    if not detected_category:
        detected_category = _detect_category(question)

    if detected_category:
        category_txns = retrieve_transactions_by_category(ctx, detected_category)
        context_str   = build_category_context(detected_category, category_txns, ctx)
        context_type  = f"category:{detected_category}"
    else:
        context_str  = build_financial_context(ctx)
        context_type = "full_profile"

    # ── 3. Generate ──────────────────────────────────────────────
    system_prompt = _build_system_prompt(context_str, conversation_history or [])
    full_prompt   = f"{system_prompt}\n\nUser Question: {question}"

    try:
        ai_response = generate_response(full_prompt)
        return {
            "success":      True,
            "response":     ai_response,
            "context_used": context_type,
            "rag":          True,
        }
    except Exception as e:
        return {
            "success":      False,
            "response":     f"AI generation failed: {str(e)}",
            "context_used": context_type,
            "rag":          True,
        }

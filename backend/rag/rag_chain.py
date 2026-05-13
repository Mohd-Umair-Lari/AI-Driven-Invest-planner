"""
rag/rag_chain.py
-----------------
Orchestrates the complete RAG pipeline:
  1. Retrieve  — fetch user data from MongoDB
  2. Augment   — build a grounded context string
  3. Generate  — inject context into prompt and call Groq

Usage:
    from rag.rag_chain import run_rag_chain
    result = run_rag_chain(collection, email="user@email.com", question="How much did I spend on food?")
"""

import re
from typing import Any, Dict

from ai.groq_client import generate_response
from rag.retriever import retrieve_user_context, retrieve_transactions_by_category
from rag.context_builder import build_financial_context, build_category_context

# ── Category keywords the system detects automatically ─────────
_CATEGORY_KEYWORDS = [
    "food", "groceries", "grocery", "dining", "restaurant",
    "rent", "housing", "home",
    "transport", "travel", "commute", "fuel", "cab", "uber",
    "entertainment", "movies", "streaming",
    "shopping", "clothes", "clothing",
    "medical", "health", "hospital", "medicine",
    "education", "school", "tuition",
    "utilities", "electricity", "water", "internet", "phone",
    "insurance",
    "emi", "loan",
]


def _detect_category(question: str) -> str | None:
    """
    Heuristically detect if the user is asking about a specific spending
    category so we can provide a hyper-focused context.
    """
    q = question.lower()
    for kw in _CATEGORY_KEYWORDS:
        if kw in q:
            return kw
    return None


def _build_system_prompt(context: str) -> str:
    return f"""You are FinPass AI, a precise and honest personal finance advisor.

IMPORTANT INSTRUCTIONS:
- Answer ONLY using the financial data provided below.
- Do NOT make up numbers. If the data doesn't contain the answer, say so clearly.
- Use ₹ for Indian Rupees.
- Be specific, cite exact numbers from the data.
- Keep responses concise (2-4 sentences max unless analysis is requested).
- If spending is high, suggest one concrete improvement.

--- RETRIEVED FINANCIAL DATA ---
{context}
--- END OF DATA ---
"""


def run_rag_chain(
    collection,
    email: str,
    question: str,
    extra_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline. Returns a dict with the AI response and metadata.

    Args:
        collection : MongoDB collection object
        email      : user's email to retrieve their data
        question   : user's natural language question
        extra_context : optional override/supplement to MongoDB data
                        (e.g., values sent directly from the frontend)
    """

    # ── Step 1: RETRIEVE ─────────────────────────────────────────
    ctx = retrieve_user_context(collection, email)

    # Merge any extra context passed from the frontend
    if extra_context:
        ctx.update({k: v for k, v in extra_context.items() if v})

    if not ctx:
        return {
            "success": False,
            "response": "I couldn't find your financial data. Please complete your profile first.",
            "context_used": "none",
            "rag": True,
        }

    # ── Step 2: AUGMENT ──────────────────────────────────────────
    detected_category = _detect_category(question)

    if detected_category:
        # Focused context for spending-category questions
        category_txns = retrieve_transactions_by_category(ctx, detected_category)
        context_str   = build_category_context(detected_category, category_txns, ctx)
        context_type  = f"category:{detected_category}"
    else:
        # Full financial profile context
        context_str  = build_financial_context(ctx)
        context_type = "full_profile"

    # ── Step 3: GENERATE ─────────────────────────────────────────
    system_prompt = _build_system_prompt(context_str)
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

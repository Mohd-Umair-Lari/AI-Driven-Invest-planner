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


def _build_system_prompt(context: str, history: List[Dict[str, str]], is_greeting: bool = False) -> str:
    """
    Builds a professional but conversational system prompt.
    - For greetings/smalltalk: warm but redirects to finance.
    - For financial queries: grounds the answer in user data.
    """
    history_block = ""
    if history:
        lines = []
        for m in history[-8:]:   # last 8 messages for better context
            role  = "User" if m["role"] == "user" else "FinPass AI"
            lines.append(f"{role}: {m['content']}")
        history_block = "\n--- CONVERSATION HISTORY ---\n" + "\n".join(lines) + "\n---\n\n"

    context_block = ""
    if context and not is_greeting:
        context_block = f"\n--- USER'S FINANCIAL PROFILE ---\n{context}\n--- END PROFILE ---\n\n"

    return (
        "You are FinPass AI, a professional AI-powered personal finance advisor for Indian investors.\n\n"
        "YOUR PERSONA:\n"
        "- You are knowledgeable, warm, and professional — like a trusted financial advisor.\n"
        "- You speak in a clear, friendly, and confident tone. Never robotic.\n"
        "- You remember the conversation context and refer back to it naturally.\n\n"
        "WHAT YOU DO:\n"
        "- Help users understand their spending, savings, investments, goals, and debt.\n"
        "- Provide personalized insights using the user's actual financial data below.\n"
        "- Answer general finance questions (SIP, mutual funds, EMI, tax, budgeting, etc.).\n"
        "- Respond warmly to greetings and small talk, then gently steer to financial topics.\n\n"
        "WHAT YOU DON'T DO:\n"
        "- Discuss topics completely unrelated to finance, money, or investing.\n"
        "- If asked about movies, coding, sports, etc. — politely decline and offer financial help instead.\n"
        "- Never invent numbers. Use ₹ for Indian Rupees. If data is missing, say so honestly.\n\n"
        "RESPONSE STYLE:\n"
        "- Keep responses concise (2-5 sentences for simple queries, more for deep analysis).\n"
        "- Use bullet points only when listing multiple items.\n"
        "- If spending is high, always suggest one concrete actionable improvement.\n"
        "- Don't start every message with 'Great question!' — vary your openings.\n\n"
        f"{history_block}"
        f"{context_block}"
    )


_GREETING_PATTERNS = [
    "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
    "good night", "howdy", "sup", "what's up", "how are you", "namaste",
    "hola", "who are you", "what can you do", "help", "start", "thanks",
    "thank you", "okay", "ok", "got it", "nice", "great", "cool"
]


def _is_greeting_or_smalltalk(question: str) -> bool:
    q = question.lower().strip()
    # Short messages with greeting words
    if len(q.split()) <= 5:
        return any(p in q for p in _GREETING_PATTERNS)
    return False


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
    - Detects greetings and handles them conversationally.
    - For financial queries, retrieves user data and grounds the answer.
    """

    is_greeting = _is_greeting_or_smalltalk(question)

    # ── 1. For greetings, skip heavy data retrieval ───────────────
    if is_greeting:
        # Fetch the user's first name for a personalized greeting
        user_doc = collection.find_one({"email": email}, {"Name": 1, "_id": 0})
        name = (user_doc or {}).get("Name", "").split()[0] if user_doc else ""

        system_prompt = _build_system_prompt("", conversation_history or [], is_greeting=True)
        full_prompt   = (
            f"{system_prompt}"
            f"The user's first name is: {name or 'there'}.\n\n"
            f"User says: {question}"
        )
        try:
            ai_response = generate_response(full_prompt)
            return {"success": True, "response": ai_response, "context_used": "greeting", "rag": False}
        except Exception as e:
            return {"success": True, "response": f"Hello{', ' + name if name else ''}! How can I help with your finances today?", "context_used": "greeting", "rag": False}

    # ── 2. Retrieve from MongoDB ─────────────────────────────────
    ctx = retrieve_user_context(collection, email)

    # Merge frontend-supplied overrides
    if extra_context:
        ctx.update({k: v for k, v in extra_context.items() if v})

    if not ctx:
        return {
            "success":      False,
            "response":     "I couldn't find your financial data. Please complete your profile first, then I can give you personalised insights!",
            "context_used": "none",
            "rag":          True,
        }

    # ── 3. Build context string ──────────────────────────────────
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

    # ── 4. Generate ──────────────────────────────────────────────
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
            "response":     f"I ran into an issue generating a response: {str(e)}. Please try again.",
            "context_used": context_type,
            "rag":          True,
        }


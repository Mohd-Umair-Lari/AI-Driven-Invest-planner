import re
from typing import Any, Dict, List, Optional

from ai.groq_client import generate_chat_response
from rag.retriever import retrieve_user_context, retrieve_transactions_by_category
from rag.context_builder import build_financial_context, build_category_context
from rag.embedder import embed_text, is_available as _embedding_available

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

_GREETING_ONLY = frozenset({
    "hi", "hello", "hey", "hola", "namaste", "howdy", "sup",
    "good morning", "good evening", "good afternoon", "good night",
    "what's up", "whats up",
})


def _detect_category(question: str) -> Optional[str]:
    q = question.lower()
    for kw in _CATEGORY_KEYWORDS:
        if kw in q:
            return kw
    return None


def _is_standalone_greeting(question: str, history: List[Dict[str, str]]) -> bool:
    """Only treat as greeting when there is no prior thread."""
    if history:
        return False
    q = question.lower().strip().rstrip("!?.")
    if q in _GREETING_ONLY:
        return True
    words = q.split()
    return len(words) <= 2 and any(q == g or q.startswith(g + " ") for g in _GREETING_ONLY)


def _build_system_prompt(
    context: str,
    history: List[Dict[str, str]],
    *,
    continuing: bool,
) -> str:
    context_block = ""
    if context:
        context_block = (
            f"\n--- USER'S FINANCIAL PROFILE (reference when relevant) ---\n"
            f"{context}\n--- END PROFILE ---\n"
        )

    continuation_rules = (
        "CONTINUATION (CRITICAL):\n"
        "- There is an ongoing conversation. Do NOT open with Hello, Hi, Hey, or Good to see you.\n"
        "- Do NOT re-introduce yourself. Answer the latest message as the next turn in the same chat.\n"
        "- Refer back to earlier topics naturally when the user follows up.\n"
    ) if continuing else (
        "FIRST MESSAGE:\n"
        "- You may greet briefly once if the user greeted you. Keep it to one short line, then help.\n"
    )

    return (
        "You are FinPass AI, a personal finance advisor for Indian investors.\n\n"
        "PERSONA:\n"
        "- Sound like ChatGPT in a finance thread: direct, natural, conversational — not a call-center script.\n"
        "- Never use filler openers: 'Great question!', 'Absolutely!', 'I'd be happy to help!'.\n"
        "- Use ₹ for amounts. Never invent numbers; say when data is missing.\n\n"
        f"{continuation_rules}\n"
        "SCOPE:\n"
        "- Finance, money, budgeting, investing, taxes, goals, debt, insurance.\n"
        "- Politely redirect off-topic questions back to money.\n\n"
        "STYLE:\n"
        "- 2–5 sentences for simple questions; more only when analysis needs it.\n"
        "- Bullets only for lists of 3+ items.\n"
        f"{context_block}"
    )


def run_rag_chain(
    collection,
    email: str,
    question: str,
    extra_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    intent=None,
) -> Dict[str, Any]:

    history = conversation_history or []
    continuing = len(history) > 0
    is_greeting = _is_standalone_greeting(question, history)

    if is_greeting:
        user_doc = collection.find_one({"email": email}, {"Name": 1, "_id": 0})
        name = (user_doc or {}).get("Name", "").split()[0] if user_doc else ""
        system_prompt = _build_system_prompt("", history, continuing=False)
        user_message = (
            f"The user's first name is {name or 'there'}. They said: {question}\n"
            "Reply with a brief friendly greeting and one sentence on how you can help with their finances."
        )
        try:
            ai_response = generate_chat_response(system_prompt, user_message, history)
            return {"success": True, "response": ai_response, "context_used": "greeting", "rag": False}
        except Exception:
            return {
                "success": True,
                "response": f"Hi{', ' + name if name else ''}! What would you like to explore — savings, investments, or your goals?",
                "context_used": "greeting",
                "rag": False,
            }

    ctx = retrieve_user_context(collection, email)

    if extra_context:
        ctx.update({k: v for k, v in extra_context.items() if v})

    if not ctx:
        return {
            "success": False,
            "response": "I couldn't find your financial data. Please complete your profile first, then I can give you personalised insights!",
            "context_used": "none",
            "rag": True,
        }

    semantic_chunks: List[str] = []
    vector_store = _get_vector_store(collection)

    if _embedding_available() and vector_store is not None:
        query_embedding = embed_text(question)
        if query_embedding:
            kb_chunks = vector_store.search_knowledge(query_embedding, limit=3)
            user_chunks = vector_store.search_user_chunks(email, query_embedding, limit=2)
            semantic_chunks = kb_chunks + user_chunks
        else:
            semantic_chunks = vector_store.keyword_search_knowledge(question, limit=2)
    elif vector_store is not None:
        semantic_chunks = vector_store.keyword_search_knowledge(question, limit=2)

    detected_category = None
    if intent and hasattr(intent, "entities"):
        detected_category = intent.entities.get("category")
    if not detected_category:
        detected_category = _detect_category(question)

    if detected_category:
        category_txns = retrieve_transactions_by_category(ctx, detected_category)
        context_str = build_category_context(detected_category, category_txns, ctx)
        context_type = f"category:{detected_category}+vector"
    else:
        context_str = build_financial_context(ctx)
        context_type = "full_profile+vector"

    if semantic_chunks:
        context_str += "\n\n=== RELEVANT FINANCIAL KNOWLEDGE ===\n"
        for i, chunk in enumerate(semantic_chunks, 1):
            context_str += f"\n[{i}] {chunk.strip()}\n"
        context_str += "=== END KNOWLEDGE ==="

    system_prompt = _build_system_prompt(context_str, history, continuing=continuing)

    try:
        ai_response = generate_chat_response(
            system_prompt,
            question,
            history,
        )
        return {
            "success": True,
            "response": ai_response,
            "context_used": context_type,
            "rag": True,
            "semantic_chunks": len(semantic_chunks),
        }
    except Exception as e:
        return {
            "success": False,
            "response": f"I ran into an issue generating a response: {str(e)}. Please try again.",
            "context_used": context_type,
            "rag": True,
        }


_vs_instance = None


def _get_vector_store(collection):

    global _vs_instance
    if _vs_instance is None:
        try:
            from rag.mongo_vector_store import MongoVectorStore
            db = collection.database
            _vs_instance = MongoVectorStore(db)
        except Exception as e:
            try:
                from loguru import logger
            except ImportError:
                import logging as _l
                logger = _l.getLogger("rag_chain")
            logger.warning(f"Could not init MongoVectorStore: {e}")
            return None
    return _vs_instance

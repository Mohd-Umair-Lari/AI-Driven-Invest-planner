import re
from typing import Any, Dict, List, Optional

from ai.groq_client import generate_response
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

def _detect_category(question: str) -> Optional[str]:
    q = question.lower()
    for kw in _CATEGORY_KEYWORDS:
        if kw in q:
            return kw
    return None

def _build_system_prompt(context: str, history: List[Dict[str, str]], is_greeting: bool = False) -> str:
    history_block = ""
    if history:
        lines = []
        for m in history[-8:]:
            role  = "User" if m["role"] == "user" else "FinPass AI"
            lines.append(f"{role}: {m['content']}")
        history_block = "\n--- CONVERSATION HISTORY ---\n" + "\n".join(lines) + "\n---\n\n"

    context_block = ""
    if context and not is_greeting:
        context_block = f"\n--- USER'S FINANCIAL PROFILE ---\n{context}\n--- END PROFILE ---\n\n"

    return (
        "You are FinPass AI, a professional AI-powered personal finance advisor for Indian investors.\n\n"
        "YOUR PERSONA:\n"
        "- You are knowledgeable, approachable, and professional — like a trusted financial advisor.\n"
        "- You speak in clear, natural English. Your tone is confident and helpful, never stiff.\n"
        "- You remember the conversation context and refer back to it naturally.\n\n"
        "GREETING RULES (IMPORTANT):\n"
        "- Use natural English greetings only: 'Hello', 'Hi', 'Hey', 'Good to see you'.\n"
        "- Don't repeat the same greeting phrase. Vary your openings across messages.\n"
        "- Don't start every response with 'Great question!' or 'Absolutely!' — be natural.\n\n"
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
        "- If spending is high, always suggest one concrete actionable improvement.\n\n"
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

    is_greeting = _is_greeting_or_smalltalk(question)

    if is_greeting:

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

    ctx = retrieve_user_context(collection, email)

    if extra_context:
        ctx.update({k: v for k, v in extra_context.items() if v})

    if not ctx:
        return {
            "success":      False,
            "response":     "I couldn't find your financial data. Please complete your profile first, then I can give you personalised insights!",
            "context_used": "none",
            "rag":          True,
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
        context_str   = build_category_context(detected_category, category_txns, ctx)
        context_type  = f"category:{detected_category}+vector"
    else:
        context_str  = build_financial_context(ctx)
        context_type = "full_profile+vector"

    if semantic_chunks:
        context_str += "\n\n=== RELEVANT FINANCIAL KNOWLEDGE ===\n"
        for i, chunk in enumerate(semantic_chunks, 1):
            context_str += f"\n[{i}] {chunk.strip()}\n"
        context_str += "=== END KNOWLEDGE ==="

    system_prompt = _build_system_prompt(context_str, conversation_history or [])
    full_prompt   = f"{system_prompt}\n\nUser Question: {question}"

    try:
        ai_response = generate_response(full_prompt)
        return {
            "success":        True,
            "response":       ai_response,
            "context_used":   context_type,
            "rag":            True,
            "semantic_chunks": len(semantic_chunks),
        }
    except Exception as e:
        return {
            "success":      False,
            "response":     f"I ran into an issue generating a response: {str(e)}. Please try again.",
            "context_used": context_type,
            "rag":          True,
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
                import logging as _l; logger = _l.getLogger("rag_chain")
            logger.warning(f"Could not init MongoVectorStore: {e}")
            return None
    return _vs_instance


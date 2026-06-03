
import os
from typing import Dict, List, Optional

_client = None

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set")
        _client = Groq(api_key=api_key)
    return _client

def generate_response(prompt: str, system_prompt: str = None) -> str:

    client = _get_client()

    if system_prompt:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]
    else:

        messages = [
            {
                "role": "system",
                "content": (
                    "You are FinPass AI, a professional AI-powered personal finance advisor "
                    "for Indian investors. You are knowledgeable, warm, and professional."
                ),
            },
            {"role": "user", "content": prompt},
        ]

    response = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        temperature=0.7,
        max_tokens=1024,
        frequency_penalty=0.4,
        presence_penalty=0.3,
    )
    return response.choices[0].message.content


def generate_chat_response(
    system_prompt: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Multi-turn chat: system + prior turns + latest user message."""
    client = _get_client()
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]
    for turn in (conversation_history or [])[-14:]:
        role = turn.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        content = (turn.get("content") or "").strip()
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        messages=messages,
        model=MODEL,
        temperature=0.65,
        max_tokens=1024,
        frequency_penalty=0.5,
        presence_penalty=0.35,
    )
    return response.choices[0].message.content
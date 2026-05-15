# backend/ai/groq_client.py
import os

# ── Lazy client init — never crashes at import time ────────────
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
    """
    Call the Groq LLM.
    - If system_prompt is given, it is used as the system message.
    - Otherwise the full prompt is sent as the user message with a minimal system role.
    """
    client = _get_client()

    if system_prompt:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]
    else:
        # Legacy: full prompt as user message
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
        frequency_penalty=0.4,  # Reduces repetitive phrases
        presence_penalty=0.3,   # Encourages topic variety
    )
    return response.choices[0].message.content
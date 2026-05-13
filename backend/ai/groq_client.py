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


def generate_response(prompt: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FinPass AI, a precise and honest personal finance advisor "
                    "focused on long-term planning, discipline, and explainable strategies."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        model=MODEL,
        temperature=0.5,
    )
    return response.choices[0].message.content
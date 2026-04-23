# groq_service.py (replaces vertex_service.py)
# All Vertex AI / Gemini logic removed. Now powered by Groq (LLaMA-3).

import os
from groq import Groq

_client = None


def initialize_vertex():
    """
    Previously initialised Vertex AI. Now validates the Groq client on startup.
    Raises EnvironmentError if GROQ_API_KEY is missing.
    """
    global _client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY env var is not set. AI features will be unavailable."
        )
    _client = Groq(api_key=api_key)


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY is not set.")
        _client = Groq(api_key=api_key)
    return _client


def generate_financial_insights(user_data: dict) -> str:
    """
    Generate structured financial insights using Groq (LLaMA-3).
    Returns a JSON array string.
    """
    client = _get_client()

    prompt = f"""You are a financial advisor for Indian investors.

Income: {user_data.get('income', 0)}
Expenses: {user_data.get('expenses', 0)}
Debt: {user_data.get('debt', 0)}
Investments: {user_data.get('investment', 0)}
Goal: {user_data.get('goal_amount', 0)} in {user_data.get('goal_time', 0)} months

Return ONLY a valid JSON array (no markdown, no explanation) like:

[
 {{
   "title": "...",
   "description": "...",
   "type": "positive|warning|suggestion|info",
   "category": "Goal|Tax|Savings|Investment|Debt",
   "impact": "High|Medium|Low"
 }}
]"""

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a financial assistant. Always respond with valid JSON only, no markdown."
            },
            {"role": "user", "content": prompt}
        ],
        model="llama3-8b-8192",
        temperature=0.4
    )

    return response.choices[0].message.content
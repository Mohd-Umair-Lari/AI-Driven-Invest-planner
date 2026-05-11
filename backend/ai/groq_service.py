# groq_service.py
# Groq (LLaMA-3) powered AI service for financial insights.

import os
from groq import Groq

_client = None


def _get_client() -> Groq:
    """Lazily initialise and return the Groq client."""
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. AI features will be unavailable."
            )
        _client = Groq(api_key=api_key)
    return _client


def initialize_groq():
    """
    Validates the Groq client on application startup.
    Raises EnvironmentError if GROQ_API_KEY is missing.
    """
    _get_client()
    print("✅ Groq AI client initialised successfully.")


def generate_financial_insights(user_data: dict) -> str:
    """
    Generate structured financial insights using Groq (LLaMA-3.1-8b-instant).
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
        model="llama-3.1-8b-instant",
        temperature=0.4
    )

    return response.choices[0].message.content

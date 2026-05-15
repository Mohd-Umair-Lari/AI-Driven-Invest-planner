

import os
from groq import Groq

_client = None

def _get_client() -> Groq:

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

    _get_client()
    print("✅ Groq AI client initialised successfully.")

def generate_financial_insights(user_data: dict) -> str:

    client = _get_client()

    prompt = f

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

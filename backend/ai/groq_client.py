# backend/ai/groq_client.py

from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama3-8b-8192"


def generate_response(prompt: str) -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a financial assistant focused on long-term planning, discipline, and explainable investment strategies."},
            {"role": "user", "content": prompt}
        ],
        model=MODEL,
        temperature=0.5
    )

    return response.choices[0].message.content
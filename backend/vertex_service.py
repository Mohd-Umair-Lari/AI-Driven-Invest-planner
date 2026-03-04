from google import genai
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def generate_financial_insights(user_data):

    prompt = f"""
    You are a financial advisor for Indian investors.

    Income: {user_data['income']}
    Expenses: {user_data['expenses']}
    Debt: {user_data['debt']}
    Investments: {user_data['investment']}
    Goal: {user_data['goal_amount']} in {user_data['goal_time']} months

    Return strictly JSON array like:

    [
      {{
        "title": "...",
        "description": "...",
        "type": "positive|warning|suggestion|info",
        "category": "Goal|Tax|Savings|Investment|Debt",
        "impact": "High|Medium|Low"
      }}
    ]
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text
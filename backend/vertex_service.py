import os
import json
from google.oauth2 import service_account
import google.generativeai as genai

def initialize_vertex():
    service_account_info = json.loads(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    )

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info
    )

    genai.configure(
        credentials=credentials,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"]
    )

def generate_financial_insights(user_data):

    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    You are a professional Indian financial strategist.

    User:
    Income: {user_data['income']}
    Expenses: {user_data['expenses']}
    Debt: {user_data['debt']}
    Investment: {user_data['investment']}
    Risk Profile: {user_data['risk']}
    Goal: {user_data['goal_amount']} in {user_data['goal_time']} months

    Return strictly valid JSON array:
    [
      {{
        "title": "...",
        "description": "...",
        "type": "positive | warning | suggestion | info",
        "category": "Goal | Tax | Savings | Investment | Debt",
        "impact": "High | Medium | Low"
      }}
    ]
    """

    response = model.generate_content(prompt)
    return response.text
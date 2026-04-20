import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

model = None


def initialize_vertex():
    global model

    gcp_sa = os.environ.get("GCP_SERVICE_ACCOUNT")
    gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    gcp_location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not gcp_sa or not gcp_project:
        raise EnvironmentError(
            "GCP_SERVICE_ACCOUNT or GOOGLE_CLOUD_PROJECT env vars are not set. "
            "Vertex AI features will be unavailable."
        )

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(gcp_sa)
    )

    vertexai.init(
        project=gcp_project,
        location=gcp_location,
        credentials=credentials
    )

    model = GenerativeModel("gemini-2.5-pro")


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

    response = model.generate_content(prompt)

    return response.text
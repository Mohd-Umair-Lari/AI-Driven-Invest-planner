import os
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

def initialize_vertex():
    service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info
    )

    vertexai.init(
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ["GOOGLE_CLOUD_LOCATION"],
        credentials=credentials
    )

def generate_financial_insights(user_data):

    model = GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(
        "Say hello in JSON format"
    )

    return response.text
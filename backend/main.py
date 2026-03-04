import os
import json
from datetime import datetime
from bson import ObjectId
from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
#from vertex_service import initialize_vertex, generate_financial_insights
import certifi
from vertex_service import generate_financial_insights
import google.generativeai as genai

from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent
from routes.intelligence_routes import intelligence_bp  


env_path = os.path.join(os.path.dirname(__file__), "nosave", ".env")
load_dotenv(dotenv_path=env_path)
#initialize_vertex()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "https://ai-driven-invest-planner.vercel.app"
            ]
        }
    },
    supports_credentials=True
)
app.register_blueprint(intelligence_bp, url_prefix="/api")

def connect_mongo():
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000
    )
    client.admin.command("ping")
    return client


client = connect_mongo()
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def ensure_onboarding(user):
    if "onboarding" not in user:
        onboarding = {
            "status": "not_started",
            "current_step": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        collection.update_one(
            {"email": user["email"]},
            {"$set": {"onboarding": onboarding}}
        )
        user["onboarding"] = onboarding


@app.route("/", methods=["GET"])
def health():
    return {
        "status": "ok",
        "service": "FinPass Backend",
        "version": "v1"
    }, 200


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password required"}), 400

    user = collection.find_one(
        {"email": email, "password": password},
        {"password": 0}
    )

    if not user:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    user["_id"] = str(user["_id"])
    ensure_onboarding(user)
    return jsonify({"status": "success", "user": user})


@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or {}

    name = (data.get("Name") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "Name, Email, and Password are required"}), 400

    if collection.find_one({"email": email}):
        return jsonify({"status": "error", "message": "Email already registered"}), 409

    doc = {
        "_id": ObjectId(),
        "Name": name,
        "email": email,
        "password": password,
        "Age": str(data.get("Age") or ""),
        "employement-status": data.get("employement-status", "Salaried"),
        "Goal": data.get("Goal", {}),
        "financials": data.get("financials", {}),
        "investments": data.get("investments", {}),
        "progress": data.get("progress", {}),
        "onboarding": {
            "status": "in_progress",
            "current_step": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
    }

    collection.insert_one(doc)
    doc.pop("password")
    doc["_id"] = str(doc["_id"])

    return jsonify({"status": "success", "user": doc}), 201


@app.route("/api/onboarding/start", methods=["POST"])
def start_onboarding():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    ensure_onboarding(user)

    if user["onboarding"]["status"] in ["not_started", "cancelled"]:
        onboarding = {
            "status": "in_progress",
            "current_step": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        collection.update_one(
            {"email": email},
            {"$set": {"onboarding": onboarding}}
        )
        user["onboarding"] = onboarding

    return jsonify({"status": "success", "onboarding": user["onboarding"]})


@app.route("/api/onboarding/save", methods=["POST"])
def save_onboarding():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    step = data.get("step", 0)
    payload = data.get("payload", {})

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    existing = user.get("onboarding", {}).get("data", {})

    merged_data = {
        **existing,
        **payload
    }

    collection.update_one(
        {"email": email},
        {
            "$set": {
                "onboarding.status": "in_progress",
                "onboarding.current_step": step,
                "onboarding.data": merged_data,
                "onboarding.last_updated": datetime.utcnow().isoformat()
            }
        }
    )

    return jsonify({"status": "saved"})

@app.route("/api/onboarding/cancel", methods=["POST"])
def cancel_onboarding():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    current_step = data.get("current_step")

    if not email:
        return jsonify({"error": "Email required"}), 400

    update = {
        "onboarding.status": "cancelled",
        "onboarding.last_updated": datetime.utcnow().isoformat()
    }

    if current_step is not None:
        update["onboarding.current_step"] = current_step

    collection.update_one(
        {"email": email},
        {"$set": update}
    )

    return jsonify({"status": "cancelled"})

@app.route("/api/onboarding/status/<email>", methods=["GET"])
def onboarding_status(email):
    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    onboarding = user.get("onboarding", {})

    return jsonify({
        "status": "success",
        "onboarding": {
            "state": onboarding.get("status"),
            "current_step": onboarding.get("current_step"),
            "data": onboarding.get("data", {})
        }
    })


@app.route("/api/onboarding/complete", methods=["POST"])
def complete_onboarding():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    onboarding = {
        "status": "completed",
        "current_step": None,
        "last_updated": datetime.utcnow().isoformat()
    }

    collection.update_one(
        {"email": email},
        {"$set": {"onboarding": onboarding}}
    )

    return jsonify({"status": "completed"})


@app.route("/api/user/<email>", methods=["GET"])
def api_get_user(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "user": user})


@app.route("/api/user/<email>", methods=["PUT"])
def api_update_user(email):
    data = request.get_json(silent=True) or {}

    update = {
        "Goal": data.get("Goal", {}),
        "financials": data.get("financials", {}),
        "investments": data.get("investments", {}),
        "progress": data.get("progress", {})
    }

    result = collection.update_one(
        {"email": email},
        {"$set": update}
    )

    if result.matched_count == 0:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"status": "success"})

@app.route("/api/deep-analysis", methods=["POST"])
def deep_analysis():
    user_data = request.json
    ai_response = generate_financial_insights(user_data)
    return jsonify(json.loads(ai_response))

@app.route("/api/analytics/<email>", methods=["GET"])
def analytics(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"analytics": compute_financial_health(user)})


@app.route("/api/predict/<email>", methods=["GET"])
def predict(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(goal_probability(user))


@app.route("/api/recommend/<email>", methods=["GET"])
def recommend(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"recommended_plan": generate_plan(user)})


@app.route("/api/goal-intelligence/<email>", methods=["GET"])
def goal_intelligence(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"goal_intelligence": compute_goal_intelligence(user)})

# @app.route("/test-vertex")
# def test_vertex():
#     try:
#         from vertexai.generative_models import GenerativeModel
#         model = GenerativeModel("gemini-1.5-flash")
#         response = model.generate_content("Return JSON: {\"message\": \"hello\"}")
#         return response.text
#     except Exception as e:
#         return str(e), 500

@app.route("/test-ai")
def test_ai():
    try:
        response = model.generate_content("Return JSON {\"hello\":\"world\"}")
        return response.text
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route("/api/agent/<email>", methods=["GET"])
def agent_api(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        goal_intel = compute_goal_intelligence(user)
        agent_response = run_agent(goal_intel)

        if not agent_response:
            agent_response = {
                "action": "HOLD",
                "message": "Decision data unavailable",
                "reason": "Incomplete user data"
            }

        return jsonify({
            "goal_intelligence": goal_intel,
            "agent": agent_response
        })

    except Exception as e:
        return jsonify({
            "agent": {
                "action": "ERROR",
                "message": "Decision computation failed",
                "reason": str(e)
            }
        }), 200
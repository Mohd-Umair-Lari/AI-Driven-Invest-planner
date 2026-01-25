import os
from datetime import datetime
from bson import ObjectId
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent


env_path = os.path.join(os.path.dirname(__file__), "nosave", ".env")
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


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
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    collection.update_one(
        {"email": email},
        {
            "$set": {
                "onboarding": {
                    "status": "in_progress",
                    "current_step": data.get("step", 0),
                    "data": data.get("payload", {}),
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
        }
    )

    return jsonify({"status": "saved"})


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
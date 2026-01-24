import os
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
from datetime import datetime


env_path = os.path.join(os.path.dirname(__file__), "nosave", ".env")
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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


def has_minimum_financial_data(user):
    goal = user.get("Goal") or {}
    financials = user.get("financials") or {}
    investments = user.get("investments") or {}
    target_amt = goal.get("target-amt") or {}
    target_time = goal.get("target-time") or {}
    monthly_income = financials.get("monthly-income") or {}
    risk_opt = investments.get("risk-opt") or {}
    invest_amt = investments.get("invest-amt") or {}

    required_fields = [
        target_amt,
        target_time,
        monthly_income,
        risk_opt,
        invest_amt
    ]

    return all(field is not None for field in required_fields)


def connect_mongo() -> MongoClient:
    client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
    )
    client.admin.command("ping")
    print("[Mongo] Connected successfully.")
    return client

client = connect_mongo()
db = client[DB_NAME]
collection = db[COLLECTION_NAME]


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

    return jsonify({
        "status": "success",
        "onboarding": user["onboarding"]
    })

@app.route("/api/onboarding/save", methods=["POST"])
def save_onboarding():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email required"}), 400

    collection.update_one(
        {"email": email},
        {
            "$set": {
                "onboarding": {
                    "current_step": data.get("step", 0),
                    "completed": False,
                    "data": data.get("payload", {})
                }
            }
        },
        upsert=True
    )

    return jsonify({"status": "saved"})

@app.route("/api/onboarding/load/<email>")
def load_onboarding(email):
    user = collection.find_one(
        {"email": email},
        {"onboarding": 1, "_id": 0}
    )
    return jsonify(user.get("onboarding", {}))


@app.route("/api/user/<email>/onboarding/cancel", methods=["POST"])
def cancel_onboarding(email):
    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    ensure_onboarding(user)

    # Do not allow cancellation if already completed
    if user["onboarding"]["status"] == "completed":
        return jsonify({"error": "Onboarding already completed"}), 400

    payload = request.get_json(silent=True) or {}
    step = payload.get("current_step", user["onboarding"]["current_step"])

    onboarding = {
        "status": "cancelled",
        "current_step": step,
        "last_updated": datetime.utcnow().isoformat()
    }

    collection.update_one(
        {"email": email},
        {"$set": {"onboarding": onboarding}}
    )

    return jsonify({"status": "cancelled"})

@app.route("/api/onboarding/status/<email>", methods=["GET"])
def onboarding_status(email):
    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    ensure_onboarding(user)

    return jsonify({
        "status": "success",
        "onboarding": {
            "state": user["onboarding"]["status"],
            "current_step": user["onboarding"]["current_step"]
        }
    })


@app.route("/api/onboarding/complete", methods=["POST"])
def complete_onboarding():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    ensure_onboarding(user)

    onboarding = {
        "status": "completed",
        "current_step": None,
        "last_updated": datetime.utcnow().isoformat()
    }

    collection.update_one(
        {"email": email},
        {"$set": {
            "onboarding": onboarding,
            "_onboarding_partial": False
        }}
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

    intelligence = compute_goal_intelligence(user)
    return jsonify({"goal_intelligence": intelligence})


@app.route("/api/agent/<email>", methods=["GET"])
def agent_api(email):
    user = collection.find_one({"email": email}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        goal_intel = compute_goal_intelligence(user)

        agent_response = run_agent(goal_intel)

        # 🔒 GUARANTEE STRUCTURE
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
        print("[AGENT ERROR]", e)
        return jsonify({
            "agent": {
                "action": "ERROR",
                "message": "Decision computation failed",
                "reason": str(e)
            }
        }), 200
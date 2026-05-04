import os
import re
from datetime import datetime
from bson import ObjectId
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import certifi
from groq_service import initialize_groq
from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent
from routes.intelligence_routes import intelligence_bp

# Load environment variables from .env file in backend root directory
load_dotenv()
# Initialize Groq AI (optional - gracefully handle if unavailable)
try:
    initialize_groq()
    print("✅ Groq AI initialized successfully")
except Exception as e:
    print(f"⚠️ Groq AI initialization skipped: {e}")

# Environment Variables
MONGO_URI = os.getenv("MONGO_URI", "").strip()
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI environment variable is not set. Please configure it in .env")

DB_NAME = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()
FLASK_ENV = os.getenv("FLASK_ENV", "development").strip()
PORT = int(os.getenv("PORT", 5000))

app = Flask(__name__)
# CORS configuration: Allow all Vercel deployments + localhost + production domain
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                # Development/local
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080",
                # Production - Allow all Vercel subdomains with regex
                re.compile(r"https://.*\.vercel\.app"),
                "https://ai-driven-invest-planner.vercel.app",
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


@app.route("/api/test-connection", methods=["GET"])
def test_connection():
    """Test endpoint to verify backend is accessible"""
    try:
        # Try to ping the database
        client.admin.command("ping")
        return jsonify({
            "status": "success",
            "message": "Backend is running",
            "database": "Connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Backend is running but database connection failed",
            "error": str(e)
        }), 500


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    user = collection.find_one({"email": email})

    if user:
        stored_password = user.get("password", "")
        # werkzeug hashes always start with the method prefix (scrypt:, pbkdf2:, argon2:)
        # check_password_hash returns False (not an exception) for plain-text input,
        # so try/except is NOT the right approach — use prefix detection instead.
        IS_HASHED = stored_password.startswith(("scrypt:", "pbkdf2:", "argon2:", "sha256$", "sha512$"))
        if IS_HASHED:
            password_valid = check_password_hash(stored_password, password)
        else:
            # Legacy: plain-text password stored directly in DB
            password_valid = (stored_password == password)

        if password_valid:
            user.pop("password", None)
            user["_id"] = str(user["_id"])
            ensure_onboarding(user)
            return jsonify({"status": "success", "user": user})

    return jsonify({"status": "error", "message": "Invalid credentials"}), 401



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

    hashed_pwd = generate_password_hash(password)
    print(f"📝 Signup: {email} - Password hashed successfully")

    doc = {
        "_id": ObjectId(),
        "Name": name,
        "email": email,
        "password": hashed_pwd,
        "Age": str(data.get("Age") or ""),
        "employment-status": data.get("employment-status", "Salaried"),
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
        return jsonify({"status": "error", "message": "User not found"}), 404

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
        return jsonify({"status": "error", "message": "Email required"}), 400

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

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
        return jsonify({"status": "error", "message": "Email required"}), 400

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
        return jsonify({"status": "error", "message": "User not found"}), 404

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
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "user": user})


@app.route("/api/user/<email>", methods=["PUT"])
def api_update_user(email):
    data = request.get_json(silent=True) or {}

    update = {
        "Name": data.get("Name", ""),
        "Age": str(data.get("Age", "")),
        "employment-status": data.get("employment-status", ""),
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
        return jsonify({"status": "error", "message": "User not found"}), 404

    print(f"✅ User profile updated: {email}")
    return jsonify({"status": "success"})

@app.route("/api/analytics/<email>", methods=["GET"])
def analytics(email):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"analytics": compute_financial_health(user)})


@app.route("/api/predict/<email>", methods=["GET"])
def predict(email):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify(goal_probability(user))


@app.route("/api/recommend/<email>", methods=["GET"])
def recommend(email):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"recommended_plan": generate_plan(user)})


@app.route("/api/goal-intelligence/<email>", methods=["GET"])
def goal_intelligence(email):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"goal_intelligence": compute_goal_intelligence(user)})

@app.route("/test-groq")
def test_groq():
    """Health-check endpoint to verify Groq AI is reachable."""
    try:
        from ai.groq_client import generate_response
        result = generate_response('Return exactly this JSON: {"message": "hello"}')
        return result, 200
    except Exception as e:
        return str(e), 500

@app.route("/api/analyze-finances/<email>", methods=["GET"])
def analyze_finances(email):
    try:
        print("📊 Analyzing finances for:", email)

        user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        financials = user.get("financials", {})
        goal = user.get("Goal", {})
        investments = user.get("investments", {})

        income = float(financials.get("monthly-income") or 0)
        expenses = float(financials.get("monthly-expenses") or 0)
        debt = float(financials.get("debt") or 0)
        risk = goal.get("risk", "moderate")
        invest_amt = float(investments.get("invest-amt") or 0)

        if income == 0:
            return jsonify({
                "status": "error",
                "message": "Please complete your financial profile first"
            }), 400

        # Build user profile dict for Groq prompt
        user_profile = {
            "income": income,
            "expenses": expenses,
            "risk": risk,
            "goal": goal.get("goal", "Wealth Building")
        }
        allocation = {
            "equity": 60 if risk == "high" else 50 if risk == "medium" else 30,
            "debt": 25 if risk == "high" else 35 if risk == "medium" else 50,
            "cash": 15 if risk == "high" else 15 if risk == "medium" else 20
        }

        # Try Groq AI
        try:
            from ai.groq_client import generate_response
            from ai.formatter import clean_response

            prompt = f"""Analyze this financial profile and return ONLY valid JSON (no markdown, no explanation):
Income: {income}
Expenses: {expenses}
Debt: {debt}
Monthly Investment: {invest_amt}
Risk Appetite: {risk}
Financial Goal: {goal.get('goal', 'Wealth Building')}
Target Amount: {goal.get('target-amt', 0)}
Target Timeline: {goal.get('target-time', 0)} months

Return ONLY this JSON format:
{{"financial_health_score": <0-100>, "analysis": "<2-3 sentence insight>", "recommendations": ["<r1>", "<r2>", "<r3>"], "investment_strategy": {{"equity": <0-100>, "debt": <0-100>, "cash": <0-100>}}}}"""

            raw = generate_response(prompt)
            cleaned = clean_response(re.sub(r"```json|```", "", raw))
            parsed = json.loads(cleaned)
            print("✅ Groq AI analysis successful")
            return jsonify(parsed)

        except Exception as ai_err:
            print(f"⚠️ Groq AI failed ({type(ai_err).__name__}: {ai_err}), using fallback")

            # Rule-based fallback
            savings_rate = (income - expenses) / income if income > 0 else 0
            debt_ratio = debt / income if income > 0 else 0

            health_score = 50
            if savings_rate > 0.3:
                health_score += 25
            if debt_ratio < 1:
                health_score += 15
            if expenses < income * 0.7:
                health_score += 10

            recommendations = []
            if debt_ratio > 2:
                recommendations.append("Focus on reducing high-interest debt first")
            if savings_rate < 0.1:
                recommendations.append("Aim to save at least 20% of your monthly income")
            if risk == "high":
                recommendations.append("Diversify across equity, debt and international funds")
            if not recommendations:
                recommendations = ["Continue your current financial plan", "Monitor monthly expenses regularly"]

            fallback = {
                "financial_health_score": min(100, health_score),
                "analysis": f"Your financial health is {'strong' if health_score > 70 else 'moderate' if health_score > 50 else 'needs improvement'}. Savings rate: {savings_rate * 100:.1f}%.",
                "recommendations": recommendations[:3],
                "investment_strategy": allocation
            }
            return jsonify(fallback)

    except Exception as e:
        print(f"❌ Error in analyze_finances: {str(e)}")
        return jsonify({
            "financial_health_score": 60,
            "analysis": "Unable to generate detailed analysis. Please ensure your profile is complete.",
            "recommendations": ["Review your financial data", "Ensure all fields are complete"],
            "investment_strategy": {"equity": 50, "debt": 35, "cash": 15}
        }), 200

@app.route("/api/init-test-data/<email>", methods=["POST"])
def init_test_data(email):
    """Initialize test user with sample financial data"""
    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    sample_data = {
        "financials": {
            "monthly-income": 75000,
            "monthly-expenses": 45000,
            "debt": 150000,
            "em-fund-opted": True
        },
        "Goal": {
            "goal": "Early Retirement",
            "target-amt": 5000000,
            "target-time": 120,
            "duration_months": 120,
            "risk": "moderate"
        },
        "investments": {
            "risk-opt": "moderate",
            "prefered-mode": "Monthly SIP",
            "invest-amt": 15000
        },
        "Age": "32",
        "Name": user.get("Name", "User"),
        "employment-status": "Salaried"
    }
    
    collection.update_one(
        {"email": email},
        {"$set": sample_data}
    )
    
    updated_user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    return jsonify({"status": "success", "user": updated_user})

@app.route("/api/ai/investment-insight/<email>", methods=["GET"])
def investment_insight(email):
    """
    Generate an AI-powered investment insight for a user.
    Fetches user data from DB using email and calls Groq LLaMA-3.
    """
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    financials  = user.get("financials", {})
    goal        = user.get("Goal", {})
    investments = user.get("investments", {})

    income      = float(financials.get("monthly-income") or 0)
    expenses    = float(financials.get("monthly-expenses") or 0)
    debt        = float(financials.get("debt") or 0)
    invest_amt  = float(investments.get("invest-amt") or 0)
    risk        = goal.get("risk", "moderate")

    if income == 0:
        return jsonify({
            "status": "error",
            "message": "User financial profile is incomplete. Please complete onboarding first."
        }), 400

    user_profile = {
        "income":      income,
        "expenses":    expenses,
        "debt":        debt,
        "invest_amt":  invest_amt,
        "risk":        risk,
        "goal":        goal.get("goal", "Wealth Building"),
        "target_amt":  float(goal.get("target-amt") or 0),
        "target_time": int(goal.get("target-time") or 0)
    }
    allocation = {
        "equity": 60 if risk == "high" else 50 if risk == "medium" else 30,
        "debt":   25 if risk == "high" else 35 if risk == "medium" else 50,
        "cash":   15 if risk == "high" else 15 if risk == "medium" else 20
    }

    try:
        insight = generate_investment_insight(user_profile, allocation)
        return jsonify({
            "status":       "success",
            "email":        email,
            "user_profile": user_profile,
            "allocation":   allocation,
            "insight":      insight
        })
    except Exception as e:
        return jsonify({
            "status":  "error",
            "message": f"AI insight generation failed: {str(e)}"
        }), 500


@app.route("/api/agent/<email>", methods=["GET"])
def agent_api(email):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

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
"""
main.py — Single entry point: Flask + FastAPI unified
======================================================
FastAPI is the outer ASGI app (serves /api/* with Pydantic validation + /docs).
Flask is mounted inside FastAPI at /flask for legacy compatibility.

Run locally:  uvicorn main:asgi_app --reload --port 5000
Deploy (HF):  uvicorn main:asgi_app --host 0.0.0.0 --port 7860
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional

import certifi
from bson import ObjectId
from dotenv import load_dotenv

# ── Flask imports ──────────────────────────────────────────────
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

# ── FastAPI imports ────────────────────────────────────────────
from fastapi import FastAPI, HTTPException, Path as FPath
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from pymongo import MongoClient

# ── Internal modules ───────────────────────────────────────────
from api.schemas import (
    AdvisorChatRequest,
    IntelligenceRequest,
    LoginRequest,
    OnboardingCancelRequest,
    OnboardingCompleteRequest,
    OnboardingSaveRequest,
    OnboardingStartRequest,
    SignupRequest,
    UserUpdateRequest,
)
from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent
from routes.intelligence_routes import intelligence_bp
from routes.advisor_routes import advisor_bp
from services.groq_service import initialize_groq

# ══════════════════════════════════════════════════════════════
#  Bootstrap
# ══════════════════════════════════════════════════════════════

load_dotenv()

try:
    initialize_groq()
    print("✅ Groq AI initialized")
except Exception as e:
    print(f"⚠️  Groq AI skipped: {e}")

MONGO_URI = os.getenv("MONGO_URI", "").strip()
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set.")

DB_NAME         = os.getenv("DB_NAME", "mockDB").strip()
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "userGoals").strip()
PORT            = int(os.getenv("PORT", 7860))

_mongo = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10_000,
    connectTimeoutMS=10_000,
    socketTimeoutMS=10_000,
)
_mongo.admin.command("ping")
db         = _mongo[DB_NAME]
collection = db[COLLECTION_NAME]

# ── Shared CORS origins ────────────────────────────────────────
_ORIGINS = [
    "http://localhost:3000", "http://localhost:5173", "http://localhost:8080",
    "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080",
    "https://ai-driven-invest-planner.vercel.app",
]

# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["_id"] = str(doc.get("_id", ""))
    doc.pop("password", None)
    return doc

def _ensure_onboarding(email: str, user: dict) -> dict:
    if "onboarding" not in user:
        ob = {"status": "not_started", "current_step": 0,
              "last_updated": datetime.utcnow().isoformat()}
        collection.update_one({"email": email}, {"$set": {"onboarding": ob}})
        user["onboarding"] = ob
    return user

# ══════════════════════════════════════════════════════════════
#  Flask App  (legacy WSGI — still handles Blueprint routes)
# ══════════════════════════════════════════════════════════════

flask_app = Flask(__name__)
CORS(flask_app, resources={r"/api/*": {"origins": _ORIGINS}}, supports_credentials=True)
flask_app.register_blueprint(intelligence_bp, url_prefix="/api")
flask_app.register_blueprint(advisor_bp,      url_prefix="/api")

# keep Flask health alive
@flask_app.route("/")
def _flask_health():
    return {"status": "ok", "engine": "flask"}

# ══════════════════════════════════════════════════════════════
#  FastAPI App  (primary ASGI — Pydantic validation + /docs)
# ══════════════════════════════════════════════════════════════

api = FastAPI(
    title="FinPass AI – Financial Advisor API",
    description="Pydantic-validated REST API. Swagger UI at **/docs**.",
    version="2.0.0",
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health ─────────────────────────────────────────────────────

@api.get("/", tags=["Health"])
async def health():
    return {"status": "ok", "service": "FinPass Backend", "version": "v2 (FastAPI+Flask)"}

@api.get("/api/test-connection", tags=["Health"])
async def test_connection():
    try:
        _mongo.admin.command("ping")
        return {"status": "success", "database": "Connected",
                "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Auth ───────────────────────────────────────────────────────

@api.post("/api/login", tags=["Auth"])
async def api_login(body: LoginRequest):
    user = collection.find_one({"email": body.email})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    stored = user.get("password", "")
    hashed = stored.startswith(("scrypt:", "pbkdf2:", "argon2:", "sha256$", "sha512$"))
    valid  = check_password_hash(stored, body.password) if hashed else stored == body.password
    if not valid:
        raise HTTPException(401, "Invalid credentials")
    user = _ensure_onboarding(body.email, user)
    return {"status": "success", "user": _serialize(user)}

@api.post("/api/signup", tags=["Auth"], status_code=201)
async def api_signup(body: SignupRequest):
    if collection.find_one({"email": body.email}):
        raise HTTPException(409, "Email already registered")
    doc = {
        "_id": ObjectId(),
        "Name": body.Name, "email": body.email,
        "password": generate_password_hash(body.password),
        "Age": body.Age or "",
        "employment-status": body.employment_status or "Salaried",
        "Goal": body.Goal or {}, "financials": body.financials or {},
        "investments": body.investments or {}, "progress": body.progress or {},
        "onboarding": {"status": "in_progress", "current_step": 0,
                       "last_updated": datetime.utcnow().isoformat()},
    }
    collection.insert_one(doc)
    return {"status": "success", "user": _serialize(doc)}

# ── Onboarding ────────────────────────────────────────────────

@api.post("/api/onboarding/start", tags=["Onboarding"])
async def onboarding_start(body: OnboardingStartRequest):
    user = collection.find_one({"email": body.email})
    if not user: raise HTTPException(404, "User not found")
    user = _ensure_onboarding(body.email, user)
    if user["onboarding"]["status"] in ("not_started", "cancelled"):
        ob = {"status": "in_progress", "current_step": 0,
              "last_updated": datetime.utcnow().isoformat()}
        collection.update_one({"email": body.email}, {"$set": {"onboarding": ob}})
        user["onboarding"] = ob
    return {"status": "success", "onboarding": user["onboarding"]}

@api.post("/api/onboarding/save", tags=["Onboarding"])
async def onboarding_save(body: OnboardingSaveRequest):
    user = collection.find_one({"email": body.email})
    if not user: raise HTTPException(404, "User not found")
    merged = {**user.get("onboarding", {}).get("data", {}), **body.payload}
    collection.update_one({"email": body.email}, {"$set": {
        "onboarding.status": "in_progress",
        "onboarding.current_step": body.step,
        "onboarding.data": merged,
        "onboarding.last_updated": datetime.utcnow().isoformat(),
    }})
    return {"status": "saved"}

@api.post("/api/onboarding/cancel", tags=["Onboarding"])
async def onboarding_cancel(body: OnboardingCancelRequest):
    upd: Dict[str, Any] = {"onboarding.status": "cancelled",
                            "onboarding.last_updated": datetime.utcnow().isoformat()}
    if body.current_step is not None:
        upd["onboarding.current_step"] = body.current_step
    collection.update_one({"email": body.email}, {"$set": upd})
    return {"status": "cancelled"}

@api.post("/api/onboarding/complete", tags=["Onboarding"])
async def onboarding_complete(body: OnboardingCompleteRequest):
    user = collection.find_one({"email": body.email})
    if not user: raise HTTPException(404, "User not found")
    collection.update_one({"email": body.email}, {"$set": {
        "onboarding": {"status": "completed", "current_step": None,
                       "last_updated": datetime.utcnow().isoformat()}}})
    return {"status": "completed"}

@api.get("/api/onboarding/status/{email}", tags=["Onboarding"])
async def onboarding_status(email: str = FPath(...)):
    user = collection.find_one({"email": email})
    if not user: raise HTTPException(404, "User not found")
    ob = user.get("onboarding", {})
    return {"status": "success", "onboarding": {
        "state": ob.get("status"), "current_step": ob.get("current_step"),
        "data": ob.get("data", {})}}

# ── User ───────────────────────────────────────────────────────

@api.get("/api/user/{email}", tags=["User"])
async def get_user(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    return {"status": "success", "user": user}

@api.put("/api/user/{email}", tags=["User"])
async def update_user(body: UserUpdateRequest, email: str = FPath(...)):
    result = collection.update_one({"email": email}, {"$set": {
        "Name": body.Name, "Age": str(body.Age or ""),
        "employment-status": body.employment_status or "",
        "Goal": body.Goal or {}, "financials": body.financials or {},
        "investments": body.investments or {}, "progress": body.progress or {},
    }})
    if result.matched_count == 0: raise HTTPException(404, "User not found")
    return {"status": "success"}

# ── Analytics ─────────────────────────────────────────────────

@api.get("/api/analytics/{email}", tags=["Analytics"])
async def analytics(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    return {"analytics": compute_financial_health(user)}

@api.get("/api/predict/{email}", tags=["Analytics"])
async def predict(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    return goal_probability(user)

@api.get("/api/recommend/{email}", tags=["Analytics"])
async def recommend(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    return {"recommended_plan": generate_plan(user)}

@api.get("/api/goal-intelligence/{email}", tags=["Analytics"])
async def goal_intelligence(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    return {"goal_intelligence": compute_goal_intelligence(user)}

@api.get("/api/agent/{email}", tags=["Agent"])
async def agent_api(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    try:
        intel = compute_goal_intelligence(user)
        resp  = run_agent(intel) or {"action": "HOLD", "message": "No data", "reason": "Incomplete profile"}
        return {"goal_intelligence": intel, "agent": resp}
    except Exception as e:
        return {"agent": {"action": "ERROR", "message": "Failed", "reason": str(e)}}

# ── AI Advisor Chat ────────────────────────────────────────────

@api.post("/api/advisor/chat", tags=["AI Advisor"])
async def advisor_chat(body: AdvisorChatRequest):
    from ai.groq_client import generate_response
    ctx = body.context
    prompt = (
        f"You are FinPass AI, a knowledgeable financial advisor.\n\n"
        f"User Profile: Income ₹{ctx.monthly_income:,.0f}, "
        f"Expenses ₹{ctx.monthly_expenses:,.0f}, Savings ₹{ctx.total_savings:,.0f}, "
        f"Debt ₹{ctx.debt:,.0f}, Risk: {ctx.risk_appetite}\n\n"
        f"Question: {body.question}\n\nProvide clear, actionable financial advice."
    )
    try:
        return {"success": True, "response": generate_response(prompt), "user_email": body.email}
    except Exception as e:
        raise HTTPException(500, f"AI generation failed: {e}")

# ── Intelligence ───────────────────────────────────────────────

@api.post("/api/intelligence/insights", tags=["Intelligence"])
async def intelligence_insights(body: IntelligenceRequest):
    from core.financial_state import FinancialState
    from services.intelligence_service import IntelligenceService
    try:
        state = FinancialState(**body.model_dump())
        return {"insights": IntelligenceService().run(state)}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Analyze Finances ───────────────────────────────────────────

@api.get("/api/analyze-finances/{email}", tags=["Analytics"])
async def analyze_finances(email: str = FPath(...)):
    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user: raise HTTPException(404, "User not found")
    fin   = user.get("financials", {})
    goal  = user.get("Goal", {})
    inv   = user.get("investments", {})
    income     = float(fin.get("monthly-income") or 0)
    expenses   = float(fin.get("monthly-expenses") or 0)
    debt       = float(fin.get("debt") or 0)
    invest_amt = float(inv.get("invest-amt") or 0)
    risk       = goal.get("risk", "moderate")
    if income == 0:
        raise HTTPException(400, "Please complete your financial profile first")
    allocation = {
        "equity": 60 if risk == "high" else 50 if risk == "medium" else 30,
        "debt":   25 if risk == "high" else 35 if risk == "medium" else 50,
        "cash":   15,
    }
    try:
        from ai.groq_client import generate_response
        from ai.formatter import clean_response
        prompt = (
            f"Analyze and return ONLY valid JSON:\n"
            f"Income:{income} Expenses:{expenses} Debt:{debt} Invest:{invest_amt} Risk:{risk}\n"
            f"Goal:{goal.get('goal','Wealth Building')} Target:{goal.get('target-amt',0)} "
            f"in {goal.get('target-time',0)} months\n"
            f'Return: {{"financial_health_score":<0-100>,"analysis":"...","recommendations":["..."],"investment_strategy":{{"equity":<n>,"debt":<n>,"cash":<n>}}}}'
        )
        raw = generate_response(prompt)
        return json.loads(clean_response(re.sub(r"```json|```", "", raw)))
    except Exception:
        sr = (income - expenses) / income if income else 0
        dr = debt / income if income else 0
        score = 50 + (25 if sr > 0.3 else 0) + (15 if dr < 1 else 0) + (10 if expenses < income * 0.7 else 0)
        recs = []
        if dr > 2: recs.append("Focus on reducing high-interest debt first")
        if sr < 0.1: recs.append("Aim to save at least 20% of monthly income")
        if not recs: recs = ["Continue your current plan", "Monitor expenses regularly"]
        return {"financial_health_score": min(100, score),
                "analysis": f"Savings rate: {sr*100:.1f}%.",
                "recommendations": recs[:3], "investment_strategy": allocation}

# ── Init Test Data (dev helper) ────────────────────────────────

@api.post("/api/init-test-data/{email}", tags=["Dev"])
async def init_test_data(email: str = FPath(...)):
    user = collection.find_one({"email": email})
    if not user: raise HTTPException(404, "User not found")
    sample = {
        "financials": {"monthly-income": 75000, "monthly-expenses": 45000,
                       "debt": 150000, "em-fund-opted": True},
        "Goal": {"goal": "Early Retirement", "target-amt": 5000000,
                 "target-time": 120, "risk": "moderate"},
        "investments": {"risk-opt": "moderate", "prefered-mode": "Monthly SIP", "invest-amt": 15000},
        "Age": "32", "employment-status": "Salaried",
    }
    collection.update_one({"email": email}, {"$set": sample})
    updated = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    return {"status": "success", "user": updated}

# ══════════════════════════════════════════════════════════════
#  Mount Flask inside FastAPI  &  export ASGI entry point
# ══════════════════════════════════════════════════════════════

# /flask/* → original Flask app (Blueprint routes, etc.)
api.mount("/flask", WSGIMiddleware(flask_app))

# Primary ASGI callable — used by uvicorn
asgi_app = api

# Legacy alias kept so old tooling that references `main:app` still works
app = asgi_app
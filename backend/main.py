import uuid
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import certifi
from bson import ObjectId
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from fastapi import FastAPI, HTTPException, Path as FPath, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware
from pymongo import MongoClient

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
from auth.password_reset import ForgotPasswordRequest, ResetPasswordRequest, VerifyResetTokenRequest
from auth.forgot_password import forgot_password_service
from auth.token_manager import token_manager
from analytics.financial_analytics import compute_financial_health
from ml.goal_predictor import generate_plan, goal_probability
from ml.goal_intelligence import compute_goal_intelligence
from agent.financial_agent import run_agent
from routes.intelligence_routes import intelligence_bp
from routes.advisor_routes import advisor_bp
from ai.groq_service import initialize_groq
from rag.rag_chain import run_rag_chain
from orchestrator.ai_orchestrator import AIOrchestrator
from memory.conversation_memory import ConversationMemory
from services.auth_service import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_access_token, hash_refresh_token, verify_refresh_token,
)
from config.logging_config import setup_logging

log = setup_logging()

load_dotenv()

try:
    initialize_groq()
    print("Groq AI initialized")
except Exception as e:
    print(f"Groq AI skipped: {e}")

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
db                = _mongo[DB_NAME]
collection        = db[COLLECTION_NAME]
conversations_col = db["conversations"]
documents_col     = db["documents"]

from rag.mongo_vector_store import MongoVectorStore
from rag.indexer import seed_knowledge_base, index_user_profile
_vector_store = MongoVectorStore(db)

import threading
def _seed_kb_async():
    try:
        n = seed_knowledge_base(_vector_store)
        if n > 0:
            print(f"Knowledge base seeded: {n} chunks")
        else:
            print("Knowledge base already seeded or embedding unavailable")
    except Exception as e:
        print(f"Knowledge base seeding skipped: {e}")

threading.Thread(target=_seed_kb_async, daemon=True).start()

def _trigger_user_indexing(email: str):

    def _do_index():
        try:
            user = collection.find_one({"email": email})
            if user:
                index_user_profile(_vector_store, user)
        except Exception as e:
            print(f"User indexing failed for {email}: {e}")
    threading.Thread(target=_do_index, daemon=True).start()

memory      = ConversationMemory(conversations_col)

def _get_orchestrator() -> AIOrchestrator:

    return AIOrchestrator(collection, conversations_col)

async def _require_auth(authorization: str = Header(default="")) -> str:

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    email = decode_access_token(token)
    if not email:
        raise HTTPException(401, "Token expired or invalid")
    return email

_ORIGINS = [
    "http://localhost:3000", "http://localhost:5173", "http://localhost:8080",
    "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080",
    "https://ai-driven-invest-planner.vercel.app",
]

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

flask_app = Flask(__name__)
CORS(flask_app, resources={r"/api/*": {"origins": _ORIGINS}}, supports_credentials=True)
flask_app.register_blueprint(intelligence_bp, url_prefix="/api")
flask_app.register_blueprint(advisor_bp,      url_prefix="/api")

@flask_app.route("/")
def _flask_health():
    return {"status": "ok", "engine": "flask"}

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

@api.get("/", tags=["Health"])
async def health():
    return {"status": "ok", "service": "FinPass Backend", "version": "v2 (FastAPI+Flask)"}

@api.get("/api/test-connection", tags=["Health"])
async def test_connection():
    try:
        _mongo.admin.command("ping")

        test_user = collection.find_one({"email": "test@example.com"})
        return {
            "status": "success", 
            "database": "Connected",
            "mongodb": "Accessible",
            "sample_query": "successful",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        log.error(f"Database connection error: {str(e)}")
        raise HTTPException(500, f"Database error: {str(e)}")

@api.post("/api/login", tags=["Auth"])
async def api_login(body: LoginRequest):
    try:

        log.info(f"Login attempt for: {body.email}")

        user = collection.find_one({"email": body.email})
        if not user:
            log.warning(f"User not found: {body.email}")
            raise HTTPException(401, "Invalid credentials")

        if not verify_password(body.password, user.get("password", "")):
            log.warning(f"Invalid password for user: {body.email}")
            raise HTTPException(401, "Invalid credentials")

        log.info(f"Password verified for: {body.email}")

        user = _ensure_onboarding(body.email, user)

        access  = create_access_token(body.email)
        refresh = create_refresh_token()

        collection.update_one(
            {"email": body.email},
            {"$set": {"refresh_token_hash": hash_refresh_token(refresh),
                      "last_login": datetime.utcnow().isoformat()}}
        )

        log.info(f"Login successful for: {body.email}")
        return {
            "status":        "success",
            "user":          _serialize(user),
            "access_token":  access,
            "refresh_token": refresh,
            "token_type":    "bearer",
        }

    except HTTPException:

        raise
    except Exception as e:
        log.error(f"Login error for {body.email}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Login failed: {str(e)}")

@api.post("/api/signup", tags=["Auth"], status_code=201)
async def api_signup(body: SignupRequest):
    try:
        log.info(f"Signup attempt for: {body.email}")

        if collection.find_one({"email": body.email}):
            log.warning(f"Email already registered: {body.email}")
            raise HTTPException(409, "Email already registered")

        doc = {
            "_id": ObjectId(),
            "Name": body.Name,
            "email": body.email,
            "password": hash_password(body.password),
            "Age": body.Age or "",
            "employment-status": body.employment_status or "Salaried",
            "Goal": body.Goal or {},
            "financials": body.financials or {},
            "investments": body.investments or {},
            "progress": body.progress or {},
            "onboarding": {
                "status": "in_progress",
                "current_step": 0,
                "last_updated": datetime.utcnow().isoformat()
            },
            "created_at": datetime.utcnow().isoformat(),
        }

        result = collection.insert_one(doc)
        log.info(f"User created: {body.email} (ID: {result.inserted_id})")

        access  = create_access_token(body.email)
        refresh = create_refresh_token()

        collection.update_one(
            {"email": body.email},
            {"$set": {"refresh_token_hash": hash_refresh_token(refresh)}}
        )

        _trigger_user_indexing(body.email)

        log.info(f"Signup successful for: {body.email}")

        return {
            "status":        "success",
            "user":          _serialize(doc),
            "access_token":  access,
            "refresh_token": refresh,
            "token_type":    "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Signup error for {body.email}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Signup failed: {str(e)}")

@api.post("/api/auth/refresh", tags=["Auth"])
async def refresh_token(body: dict):

    email   = body.get("email", "")
    refresh = body.get("refresh_token", "")
    if not email or not refresh:
        raise HTTPException(400, "email and refresh_token required")
    user = collection.find_one({"email": email})
    if not user or not user.get("refresh_token_hash"):
        raise HTTPException(401, "Invalid refresh token")
    if not verify_refresh_token(refresh, user["refresh_token_hash"]):
        raise HTTPException(401, "Invalid refresh token")
    new_access  = create_access_token(email)
    new_refresh = create_refresh_token()
    collection.update_one({"email": email},
        {"$set": {"refresh_token_hash": hash_refresh_token(new_refresh)}})
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}

@api.post("/api/auth/forgot-password", tags=["Auth"], status_code=200)
async def forgot_password(body: ForgotPasswordRequest):
    try:
        log.info(f"Forgot password request for: {body.email}")
        
        user = collection.find_one({"email": body.email})
        if not user:
            log.warning(f"Forgot password: User not found: {body.email}")
            return {
                "success": True,
                "message": "If an account exists with this email, you will receive a password reset link"
            }
        
        reset_token = token_manager.generate_reset_token(body.email, expires_in_hours=24)
        
        success, message = forgot_password_service.send_reset_email(body.email, reset_token)
        
        if success:
            log.info(f"Password reset email sent to: {body.email}")
            return {
                "success": True,
                "message": "Password reset email sent successfully. Check your inbox for the reset link."
            }
        else:
            log.error(f"Failed to send reset email to {body.email}: {message}")
            raise HTTPException(500, f"Failed to send reset email: {message}")
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Forgot password error for {body.email}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Error processing request: {str(e)}")

@api.post("/api/auth/verify-reset-token", tags=["Auth"])
async def verify_reset_token(body: VerifyResetTokenRequest):
    try:
        log.info("Verifying reset token")
        
        is_valid, email = token_manager.validate_reset_token(body.token)
        
        if not is_valid:
            log.warning("Invalid or expired reset token provided")
            raise HTTPException(400, "Invalid or expired reset token")
        
        log.info(f"Reset token verified for: {email}")
        return {
            "success": True,
            "email": email,
            "message": "Token is valid. You can now reset your password."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error verifying reset token: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Error verifying token: {str(e)}")

@api.post("/api/auth/reset-password", tags=["Auth"])
async def reset_password(body: ResetPasswordRequest):
    try:
        if body.new_password != body.confirm_password:
            raise HTTPException(400, "Passwords do not match")
        
        if len(body.new_password) < 8:
            raise HTTPException(400, "Password must be at least 8 characters long")
        
        log.info("Processing password reset")
        
        is_valid, email = token_manager.validate_reset_token(body.token)
        
        if not is_valid:
            log.warning("Invalid or expired token for password reset")
            raise HTTPException(400, "Invalid or expired reset token")
        
        user = collection.find_one({"email": email})
        if not user:
            log.warning(f"User not found for password reset: {email}")
            raise HTTPException(404, "User not found")
        
        new_password_hash = hash_password(body.new_password)
        
        collection.update_one(
            {"email": email},
            {"$set": {
                "password": new_password_hash,
                "password_reset_at": datetime.utcnow().isoformat(),
                "refresh_token_hash": None
            }}
        )
        
        token_manager.mark_token_as_used(body.token)
        
        success, message = forgot_password_service.send_password_changed_email(email)
        
        if success:
            log.info(f"Password successfully reset for: {email}")
        else:
            log.warning(f"Confirmation email failed for {email}: {message}")
        
        return {
            "success": True,
            "message": "Password has been reset successfully. You can now log in with your new password."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error resetting password: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Error resetting password: {str(e)}")

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

    _trigger_user_indexing(email)

    return {"status": "success"}

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

def _get_num(obj, *keys, default=0.0):

    for key in keys:
        val = (obj or {}).get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    return default

@api.get("/api/recommended-actions/{email}", tags=["Analytics"])
async def recommended_actions(email: str = FPath(...)):

    user = collection.find_one({"email": email}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(404, "User not found")

    fin        = user.get("financials") or {}
    inv        = user.get("investments") or {}
    goal       = user.get("Goal") or {}
    health     = compute_financial_health(user)

    income     = _get_num(fin, "monthly-income")
    expenses   = _get_num(fin, "monthly-expenses")
    debt       = _get_num(fin, "debt")
    invest_amt = _get_num(inv, "invest-amt")
    risk       = (inv.get("risk-opt") or "moderate").lower()
    timeline   = _get_num(goal, "target-time")
    target_amt = _get_num(goal, "target-amt")
    goal_name  = goal.get("goal", "your goal")
    sav_ratio  = health.get("savings_ratio", 0)
    exp_ratio  = health.get("expense_ratio", 0)
    fin_health = health.get("financial_health", "")
    surplus    = max(0, income - expenses - debt)

    actions = []

    em_fund = fin.get("em-fund-opted", False)
    if not em_fund or surplus < 5000:
        months_covered = (invest_amt / expenses) if expenses > 0 else 0
        if months_covered < 3:
            actions.append({
                "title": "Build Your Emergency Fund",
                "subtitle": f"You have less than 3 months of expenses (₹{expenses:,.0f}/mo) saved as a buffer. Aim for ₹{expenses * 6:,.0f}.",
                "priority": 1,
                "tag": "Critical",
                "color": "red",
            })

    if exp_ratio > 0.75 and income > 0:
        over_spend = expenses - (income * 0.6)
        actions.append({
            "title": "Reduce Monthly Expenses",
            "subtitle": f"You're spending {exp_ratio*100:.0f}% of income on expenses. Cutting ₹{over_spend:,.0f}/mo could free up significant savings.",
            "priority": 1 if exp_ratio > 0.85 else 2,
            "tag": "High Priority",
            "color": "orange",
        })

    debt_ratio = debt / income if income > 0 else 0
    if debt_ratio > 0.4:
        actions.append({
            "title": "Accelerate Debt Repayment",
            "subtitle": f"Your EMI/debt (₹{debt:,.0f}) is {debt_ratio*100:.0f}% of income. Prioritise clearing high-interest debt before increasing investments.",
            "priority": 2,
            "tag": "Debt Alert",
            "color": "red",
        })

    if sav_ratio > 0.25 and invest_amt > 0:
        sip_boost = round(invest_amt * 0.10 / 500) * 500
        actions.append({
            "title": f"Increase SIP by ₹{sip_boost:,.0f}/mo",
            "subtitle": f"Your savings rate is healthy at {sav_ratio*100:.0f}%. A 10% SIP step-up each year can significantly accelerate your corpus.",
            "priority": 3,
            "tag": "Growth",
            "color": "green",
        })
    elif sav_ratio > 0.1 and invest_amt == 0:
        invest_suggestion = round(surplus * 0.5 / 500) * 500
        actions.append({
            "title": "Start a SIP Investment",
            "subtitle": f"You have a monthly surplus of ₹{surplus:,.0f}. Starting a SIP of ₹{invest_suggestion:,.0f}/mo can help build long-term wealth.",
            "priority": 2,
            "tag": "Action Required",
            "color": "indigo",
        })

    if target_amt > 0 and timeline > 0 and income > 0:
        required_monthly = target_amt / timeline
        if invest_amt < required_monthly * 0.8:
            gap = required_monthly - invest_amt
            actions.append({
                "title": f"Top-up Investment for '{goal_name}'",
                "subtitle": f"To reach ₹{target_amt:,.0f} in {int(timeline)} months you need ~₹{required_monthly:,.0f}/mo. Current SIP is ₹{invest_amt:,.0f} — gap of ₹{gap:,.0f}.",
                "priority": 2,
                "tag": "Goal Gap",
                "color": "amber",
            })
        else:
            actions.append({
                "title": f"Stay the Course on '{goal_name}'",
                "subtitle": f"You're on track! Keep your ₹{invest_amt:,.0f} SIP consistent and review the plan every 6 months.",
                "priority": 4,
                "tag": "On Track",
                "color": "green",
            })

    age = _get_num(user, "Age")
    if age > 50 and risk in ("aggressive", "high"):
        actions.append({
            "title": "Review Risk Appetite",
            "subtitle": f"At age {int(age)}, an aggressive risk profile may expose you to significant volatility. Consider shifting 20-30% to debt/balanced funds.",
            "priority": 3,
            "tag": "Risk Review",
            "color": "amber",
        })
    elif age < 30 and risk in ("conservative", "low"):
        actions.append({
            "title": "Consider Higher-Growth Assets",
            "subtitle": f"At age {int(age)}, a conservative strategy may limit your long-term wealth. Consider allocating 40-60% to equity for better returns.",
            "priority": 3,
            "tag": "Opportunity",
            "color": "indigo",
        })

    if income > 50000:
        actions.append({
            "title": "Maximise 80C Deductions",
            "subtitle": f"With ₹{income:,.0f} monthly income, ensure you're fully using your ₹1.5L annual 80C limit via ELSS, PPF, or life insurance.",
            "priority": 4,
            "tag": "Tax Saving",
            "color": "indigo",
        })

    if not actions:
        actions.append({
            "title": "Complete Your Financial Profile",
            "subtitle": "Add your income, expenses, and investment details to receive personalised recommendations.",
            "priority": 1,
            "tag": "Setup Required",
            "color": "slate",
        })

    actions.sort(key=lambda x: x["priority"])
    return {"actions": actions[:5], "financial_health": fin_health, "savings_ratio": sav_ratio}

@api.post("/api/advisor/chat", tags=["AI Advisor"])
async def advisor_chat(body: AdvisorChatRequest):

    ctx        = body.context
    session_id = getattr(body, "session_id", None) or str(uuid.uuid4())
    extra = {
        "income":   ctx.monthly_income if ctx else 0,
        "expenses": ctx.monthly_expenses if ctx else 0,
        "debt":     ctx.debt if ctx else 0,
        "risk":     ctx.risk_appetite if ctx else "moderate",
    }
    orchestrator = _get_orchestrator()
    result = orchestrator.run(
        email=body.email,
        query=body.question,
        session_id=session_id,
        extra_context=extra,
    )
    if not result.get("success", True):
        raise HTTPException(500, result.get("response", "AI error"))
    return {**result, "user_email": body.email}

@api.post("/api/rag/chat", tags=["AI Advisor"])
async def rag_chat(body: AdvisorChatRequest):

    return await advisor_chat(body)

@api.get("/api/chat/sessions/{email}", tags=["Chat History"])
async def get_sessions(email: str = FPath(...)):

    return {"sessions": memory.list_sessions(email)}

@api.get("/api/chat/history/{email}/{session_id}", tags=["Chat History"])
async def get_history(email: str = FPath(...), session_id: str = FPath(...)):

    session = memory.get_session(email, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session

@api.delete("/api/chat/history/{email}/{session_id}", tags=["Chat History"])
async def clear_session(email: str = FPath(...), session_id: str = FPath(...)):

    memory.clear_session(email, session_id)
    return {"status": "cleared"}

@api.delete("/api/chat/history/{email}", tags=["Chat History"])
async def clear_all_sessions(email: str = FPath(...)):

    memory.clear_all(email)
    return {"status": "all sessions cleared"}

@api.post("/api/transactions/{email}", tags=["Transactions"], status_code=201)
async def add_transactions(email: str = FPath(...), transactions: list = None):

    if not transactions:
        raise HTTPException(400, "No transactions provided")
    result = collection.update_one(
        {"email": email},
        {"$push": {"transactions": {"$each": transactions}}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    return {"status": "success", "added": len(transactions)}

@api.get("/api/transactions/{email}", tags=["Transactions"])
async def get_transactions(email: str = FPath(...)):

    user = collection.find_one({"email": email}, {"_id": 0, "transactions": 1})
    if not user:
        raise HTTPException(404, "User not found")
    return {"transactions": user.get("transactions", [])}

@api.post("/api/intelligence/insights", tags=["Intelligence"])
async def intelligence_insights(body: IntelligenceRequest):
    from core.financial_state import FinancialState
    from services.intelligence_service import IntelligenceService
    try:
        state = FinancialState(**body.model_dump())
        return {"insights": IntelligenceService().run(state)}
    except Exception as e:
        raise HTTPException(500, str(e))

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

api.mount("/flask", WSGIMiddleware(flask_app))

asgi_app = api

app = asgi_app
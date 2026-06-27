"""
FinPass AI — Application Entry Point

Sets up FastAPI + Flask dual framework, CORS, security middleware,
and mounts all route modules. All route handlers live in routes/*.
"""

import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_cors import CORS
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.wsgi import WSGIMiddleware

from ai.groq_service import initialize_groq
from config.logging_config import setup_logging
from services.security_utils import SecurityHeaders


import db as _db


from routes.intelligence_routes import intelligence_bp
from routes.advisor_routes import advisor_bp


from routes.auth_routes import router as auth_router
from routes.onboarding_routes import router as onboarding_router
from routes.user_routes import router as user_router
from routes.analytics_routes import router as analytics_router
from routes.chat_routes import router as chat_router
from routes.transaction_routes import router as transaction_router
from routes.dev_routes import router as dev_router





log = setup_logging()

try:
    initialize_groq()
    print("Groq AI initialized")
except Exception as e:
    print(f"Groq AI skipped: {e}")





_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "https://ai-driven-invest-planner.vercel.app",
]

PORT = int(os.getenv("PORT", 7860))





flask_app = Flask(__name__)
CORS(flask_app, resources={r"/api/*": {"origins": _ORIGINS}}, supports_credentials=True)
flask_app.register_blueprint(intelligence_bp, url_prefix="/api")
flask_app.register_blueprint(advisor_bp, url_prefix="/api")


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


@api.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response = SecurityHeaders.apply_headers(response)
    return response






@api.get("/", tags=["Health"])
async def health():
    return {"status": "ok", "service": "FinPass Backend", "version": "v2 (FastAPI+Flask)"}


@api.get("/api/test-connection", tags=["Health"])
async def test_connection():
    try:
        _db._mongo.admin.command("ping")
        _db.collection.find_one({"email": "test@example.com"})
        return {
            "status": "success",
            "database": "Connected",
            "mongodb": "Accessible",
            "sample_query": "successful",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        log.error(f"Database connection error: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(500, f"Database error: {str(e)}")






api.include_router(auth_router)
api.include_router(onboarding_router)
api.include_router(user_router)
api.include_router(analytics_router)
api.include_router(chat_router)
api.include_router(transaction_router)
api.include_router(dev_router)





api.mount("/flask", WSGIMiddleware(flask_app))





asgi_app = api
app = asgi_app
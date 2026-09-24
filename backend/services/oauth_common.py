"""
Shared OAuth helpers used by all social-login providers (GitHub, Google, ...).

Keeps user upsert + app-session issuance in one place so each provider module
only implements provider-specific bits (authorize URL, token exchange, profile).
"""

from datetime import datetime, timezone

from db import collection, serialize, ensure_onboarding
from services.jwt_handler import JWTHandler, TokenValidator
from services.session_store import session_store
from config.logging_config import setup_logging

log = setup_logging()


def get_backend_base_url() -> str:
    """Public base URL of THIS backend (where providers send the OAuth code)."""
    import os
    return os.getenv(
        "BACKEND_BASE_URL",
        "https://umairlari-ai-financial-advisor-backend.hf.space",
    ).strip().rstrip("/")


def get_frontend_base_url() -> str:
    """Public base URL of the frontend (where we hand tokens back to the browser)."""
    import os
    return os.getenv(
        "FRONTEND_BASE_URL",
        "https://ai-driven-invest-planner.vercel.app",
    ).strip().rstrip("/")


def upsert_oauth_user(profile: dict, provider: str) -> dict:
    """
    Create or link a MongoDB user from a normalized OAuth profile.

    `profile` must contain: email, name, provider_id, provider_login, avatar_url.
    `provider` is e.g. "github" or "google" and drives the id/login field names.
    """
    email = profile["email"]
    now_iso = datetime.now(timezone.utc).isoformat()
    id_field = f"{provider}_id"
    login_field = f"{provider}_login"

    existing = collection.find_one({"email": email})
    if existing:
        collection.update_one(
            {"email": email},
            {
                "$set": {
                    id_field: profile["provider_id"],
                    login_field: profile["provider_login"],
                    "avatar_url": profile["avatar_url"],
                    "last_login": now_iso,
                }
            },
        )
        user = collection.find_one({"email": email})
        log.info(f"{provider} login linked to existing user: {email}")
    else:
        doc = {
            "Name": profile["name"],
            "email": email,
            id_field: profile["provider_id"],
            login_field: profile["provider_login"],
            "avatar_url": profile["avatar_url"],
            "auth_provider": provider,
            "Goal": {},
            "financials": {},
            "investments": {},
            "progress": {},
            "created_at": now_iso,
            "last_login": now_iso,
        }
        collection.insert_one(doc)
        user = collection.find_one({"email": email})
        log.info(f"New {provider} user created: {email}")

    return ensure_onboarding(email, user)


def create_app_session(user: dict) -> dict:
    """Issue our own JWT access/refresh tokens + session records (like /api/login)."""
    email = user["email"]
    user_id = str(user["_id"])

    access_token = JWTHandler.create_access_token(email, user_id)
    refresh_token = JWTHandler.create_refresh_token(email, user_id)

    access_claims = TokenValidator.validate_access_token(access_token)
    refresh_claims = TokenValidator.validate_refresh_token(refresh_token)

    if access_claims:
        session_store.create_session(
            email=email,
            user_id=user_id,
            jti=access_claims["jti"],
            token_type="access",
            expires_at=datetime.fromtimestamp(access_claims["exp"], timezone.utc),
        )
    if refresh_claims:
        session_store.create_session(
            email=email,
            user_id=user_id,
            jti=refresh_claims["jti"],
            token_type="refresh",
            expires_at=datetime.fromtimestamp(refresh_claims["exp"], timezone.utc),
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": serialize(user),
    }

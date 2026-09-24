"""
GitHub OAuth2 service.

Implements the Authorization Code flow:
  1. Build the GitHub authorize URL with CSRF state.
  2. Exchange the returned ?code for an access token.
  3. Fetch the GitHub user profile + primary email.
  4. Upsert the user into MongoDB (same userGoals collection as password auth).
  5. Issue our own JWT access/refresh tokens + sessions (same as /api/login).

Env vars required:
  GITHUB_CLIENT_ID
  GITHUB_CLIENT_SECRET
  FRONTEND_BASE_URL  (e.g. https://ai-driven-invest-planner.vercel.app)
"""

import secrets
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests

from db import collection, serialize, ensure_onboarding
from services.jwt_handler import JWTHandler, TokenValidator
from services.session_store import session_store
from config.logging_config import setup_logging

log = setup_logging()

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_USER_EMAILS_URL = "https://api.github.com/user/emails"

STATE_TTL_SECONDS = 600  # CSRF state is valid for 10 minutes

# In-memory CSRF state store: {state: {"created_at": epoch}}
_states = {}


def _get_client_id() -> str:
    import os
    client_id = os.getenv("GITHUB_CLIENT_ID", "").strip()
    if not client_id:
        raise ValueError("GITHUB_CLIENT_ID is not set.")
    return client_id


def _get_client_secret() -> str:
    import os
    client_secret = os.getenv("GITHUB_CLIENT_SECRET", "").strip()
    if not client_secret:
        raise ValueError("GITHUB_CLIENT_SECRET is not set.")
    return client_secret


def get_frontend_base_url() -> str:
    import os
    return os.getenv(
        "FRONTEND_BASE_URL",
        "https://ai-driven-invest-planner.vercel.app",
    ).strip().rstrip("/")


def build_authorize_url(redirect_path: str = "/static/callback.html") -> str:
    """Create the GitHub authorization URL with a fresh CSRF state."""
    client_id = _get_client_id()
    state = secrets.token_urlsafe(32)
    _states[state] = {"created_at": time.time()}

    # Opportunistic cleanup of expired states.
    now = time.time()
    for s in list(_states.keys()):
        if now - _states[s]["created_at"] > STATE_TTL_SECONDS:
            _states.pop(s, None)

    redirect_uri = f"{get_frontend_base_url()}{redirect_path}"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state,
        "allow_signup": "true",
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


def _consume_state(state: str) -> bool:
    """Validate and single-use-consume a CSRF state value."""
    if not state or state not in _states:
        return False
    created_at = _states.pop(state)["created_at"]
    return (time.time() - created_at) <= STATE_TTL_SECONDS


def exchange_code_for_token(code: str) -> str:
    """Exchange the OAuth code for a GitHub access token."""
    resp = requests.post(
        GITHUB_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": _get_client_id(),
            "client_secret": _get_client_secret(),
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        error = data.get("error_description", data.get("error", "unknown error"))
        raise ValueError(f"GitHub token exchange failed: {error}")
    return token


def fetch_github_user(access_token: str) -> dict:
    """Fetch the GitHub profile and primary (verified-preferred) email."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    user_resp = requests.get(GITHUB_USER_URL, headers=headers, timeout=15)
    user_resp.raise_for_status()
    profile = user_resp.json()

    email = profile.get("email")
    if not email:
        emails_resp = requests.get(GITHUB_USER_EMAILS_URL, headers=headers, timeout=15)
        if emails_resp.ok:
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            verified = next((e for e in emails if e.get("verified")), None)
            chosen = primary or verified or (emails[0] if emails else None)
            email = chosen.get("email") if chosen else None

    if not email:
        # Fallback so we always have a unique key for Mongo.
        email = profile.get("login", "") + "@users.noreply.github.com"

    return {
        "github_id": str(profile.get("id", "")),
        "github_login": profile.get("login", ""),
        "email": email.lower(),
        "name": profile.get("name") or profile.get("login", ""),
        "avatar_url": profile.get("avatar_url", ""),
    }


def upsert_github_user(github_user: dict) -> dict:
    """Create or link the MongoDB user document, mirroring password-auth users."""
    email = github_user["email"]
    now_iso = datetime.now(timezone.utc).isoformat()

    existing = collection.find_one({"email": email})
    if existing:
        collection.update_one(
            {"email": email},
            {
                "$set": {
                    "github_id": github_user["github_id"],
                    "github_login": github_user["github_login"],
                    "avatar_url": github_user["avatar_url"],
                    "last_login": now_iso,
                }
            },
        )
        user = collection.find_one({"email": email})
        log.info(f"GitHub login linked to existing user: {email}")
    else:
        doc = {
            "Name": github_user["name"],
            "email": email,
            "github_id": github_user["github_id"],
            "github_login": github_user["github_login"],
            "avatar_url": github_user["avatar_url"],
            "auth_provider": "github",
            "Goal": {},
            "financials": {},
            "investments": {},
            "progress": {},
            "created_at": now_iso,
            "last_login": now_iso,
        }
        collection.insert_one(doc)
        user = collection.find_one({"email": email})
        log.info(f"New GitHub user created: {email}")

    user = ensure_onboarding(email, user)
    return user


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


"""
Google OAuth2 service (Authorization Code flow).

Mirrors services/github_oauth.py:
  1. Build the Google authorize URL with CSRF state.
  2. Exchange the returned ?code for an access token.
  3. Fetch the Google userinfo (OpenID Connect).
  4. Upsert the user into MongoDB (shared helper).
  5. Issue our own JWT access/refresh tokens + sessions.

Env vars required:
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  BACKEND_BASE_URL  (where Google sends the code; defaults to the HF Space)
"""

import secrets
import time
from urllib.parse import urlencode

import requests

from services.oauth_common import (
    get_backend_base_url,
    get_frontend_base_url,
    upsert_oauth_user,
    create_app_session,
)
from config.logging_config import setup_logging

log = setup_logging()

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

CALLBACK_PATH = "/api/auth/google/callback"
STATE_TTL_SECONDS = 600  # CSRF state is valid for 10 minutes

# In-memory CSRF state store: {state: {"created_at": epoch}}
_states = {}


def _get_client_id() -> str:
    import os
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID is not set.")
    return client_id


def _get_client_secret() -> str:
    import os
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_secret:
        raise ValueError("GOOGLE_CLIENT_SECRET is not set.")
    return client_secret


def _redirect_uri() -> str:
    """Where Google sends the OAuth code — our own backend callback route."""
    return f"{get_backend_base_url()}{CALLBACK_PATH}"


def build_authorize_url() -> str:
    """Create the Google authorization URL with a fresh CSRF state."""
    client_id = _get_client_id()
    state = secrets.token_urlsafe(32)
    _states[state] = {"created_at": time.time()}

    now = time.time()
    for s in list(_states.keys()):
        if now - _states[s]["created_at"] > STATE_TTL_SECONDS:
            _states.pop(s, None)

    params = {
        "client_id": client_id,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"


def _consume_state(state: str) -> bool:
    """Validate and single-use-consume a CSRF state value."""
    if not state or state not in _states:
        return False
    created_at = _states.pop(state)["created_at"]
    return (time.time() - created_at) <= STATE_TTL_SECONDS


def exchange_code_for_token(code: str) -> str:
    """Exchange the OAuth code for a Google access token."""
    resp = requests.post(
        GOOGLE_TOKEN_URL,
        headers={"Accept": "application/json"},
        data={
            "client_id": _get_client_id(),
            "client_secret": _get_client_secret(),
            "code": code,
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        error = data.get("error_description", data.get("error", "unknown error"))
        raise ValueError(f"Google token exchange failed: {error}")
    return token


def fetch_google_user(access_token: str) -> dict:
    """Fetch the Google OpenID userinfo profile."""
    resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    profile = resp.json()

    email = (profile.get("email") or "").lower()
    if not email:
        raise ValueError("Google account did not return an email address.")

    return {
        "google_id": str(profile.get("sub", "")),
        "google_login": email.split("@")[0],
        "email": email,
        "name": profile.get("name") or email.split("@")[0],
        "avatar_url": profile.get("picture", ""),
    }


def upsert_google_user(google_user: dict) -> dict:
    """Create or link the MongoDB user document (delegates to shared helper)."""
    return upsert_oauth_user(
        {
            "email": google_user["email"],
            "name": google_user["name"],
            "provider_id": google_user["google_id"],
            "provider_login": google_user["google_login"],
            "avatar_url": google_user["avatar_url"],
        },
        provider="google",
    )

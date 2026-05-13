"""
services/auth_service.py
-------------------------
JWT authentication service.
- Short-lived access tokens (30 min)
- Long-lived refresh tokens (7 days) stored hashed in MongoDB
- Swap-ready: change algorithm in settings without touching routes
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from config.settings import get_settings

_settings = get_settings()
_pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ───────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    # Support legacy plain-text passwords during migration
    if hashed.startswith(("$2b$", "$2a$", "$argon2", "scrypt:")):
        return _pwd_ctx.verify(plain, hashed)
    return plain == hashed  # legacy plain-text fallback


# ── Token generation ───────────────────────────────────────────

def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": email, "exp": expire, "type": "access"}
    return jwt.encode(payload, _settings.JWT_SECRET, algorithm=_settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    """Opaque random token — stored hashed in MongoDB."""
    return secrets.token_urlsafe(48)


def decode_access_token(token: str) -> Optional[str]:
    """Returns the email (sub) if valid, else None."""
    try:
        payload = jwt.decode(
            token, _settings.JWT_SECRET, algorithms=[_settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.PyJWTError:
        return None


def hash_refresh_token(token: str) -> str:
    """Store a one-way hash so raw token never lives in DB."""
    return _pwd_ctx.hash(token)


def verify_refresh_token(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)

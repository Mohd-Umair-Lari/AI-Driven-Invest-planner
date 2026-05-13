"""
services/auth_service.py
-------------------------
JWT authentication service.
- passlib[bcrypt] used when available (new accounts get bcrypt)
- werkzeug fallback for existing accounts (scrypt/pbkdf2 hashes)
- hashlib fallback if passlib not installed
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


# ── passlib (optional) ─────────────────────────────────────────
try:
    from passlib.context import CryptContext
    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _HAS_PASSLIB = True
except ImportError:
    _pwd_ctx = None
    _HAS_PASSLIB = False

# ── PyJWT (optional) ───────────────────────────────────────────
try:
    import jwt as _pyjwt
    _HAS_JWT = True
except ImportError:
    _pyjwt = None
    _HAS_JWT = False

# ── Werkzeug (already required by Flask) ──────────────────────
from werkzeug.security import check_password_hash as _wz_check
from werkzeug.security import generate_password_hash as _wz_hash


JWT_SECRET    = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_EXPIRE_MIN = 30


# ── Password helpers ───────────────────────────────────────────

def hash_password(plain: str) -> str:
    """New accounts: use bcrypt when passlib available, else werkzeug scrypt."""
    if _HAS_PASSLIB:
        return _pwd_ctx.hash(plain)
    return _wz_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Handles every hash format stored in MongoDB:
    - werkzeug scrypt  (werkzeug 3.x): scrypt:...
    - werkzeug pbkdf2  (werkzeug 2.x): pbkdf2:sha256:...
    - passlib bcrypt:                  $2b$... / $2a$...
    - passlib argon2:                  $argon2...
    - plain text (legacy dev accounts)
    """
    # Werkzeug-formatted hashes — route back to werkzeug
    if hashed.startswith(("pbkdf2:", "scrypt:")):
        return _wz_check(hashed, plain)

    # Passlib-formatted hashes
    if hashed.startswith(("$2b$", "$2a$", "$argon2")):
        if _HAS_PASSLIB:
            return _pwd_ctx.verify(plain, hashed)
        # passlib not installed but hash is bcrypt — try werkzeug (will fail gracefully)
        return False

    # Legacy plain-text (dev/test only)
    return plain == hashed


# ── Token generation ───────────────────────────────────────────

def create_access_token(email: str) -> str:
    expire  = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MIN)
    payload = {"sub": email, "exp": expire, "type": "access"}
    if _HAS_JWT:
        return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # Fallback: simple HMAC token (not standards-compliant but functional)
    import base64, json
    header  = base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode()).decode()
    body    = base64.urlsafe_b64encode(json.dumps({"sub": email, "exp": expire.isoformat()}).encode()).decode()
    sig     = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{body}.{sig}"


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def decode_access_token(token: str) -> Optional[str]:
    if not _HAS_JWT:
        # Basic decode of our fallback token
        try:
            parts = token.split(".")
            import base64, json
            body = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
            return body.get("sub")
        except Exception:
            return None
    try:
        payload = _pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except Exception:
        return None


def hash_refresh_token(token: str) -> str:
    if _HAS_PASSLIB:
        return _pwd_ctx.hash(token)
    return hashlib.sha256(token.encode()).hexdigest()


def verify_refresh_token(plain: str, hashed: str) -> bool:
    if _HAS_PASSLIB and hashed.startswith(("$2b$", "$2a$")):
        return _pwd_ctx.verify(plain, hashed)
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

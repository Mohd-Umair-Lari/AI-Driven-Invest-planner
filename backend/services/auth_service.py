
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import bcrypt as _bcrypt_lib
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False

try:
    import jwt as _pyjwt
    _HAS_JWT = True
except ImportError:
    _pyjwt = None
    _HAS_JWT = False

from werkzeug.security import check_password_hash as _wz_check
from werkzeug.security import generate_password_hash as _wz_hash

JWT_SECRET    = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_EXPIRE_MIN = 30

def hash_password(plain: str) -> str:

    if _HAS_BCRYPT:
        salt = _bcrypt_lib.gensalt()
        return _bcrypt_lib.hashpw(plain.encode('utf-8'), salt).decode('utf-8')
    return _wz_hash(plain)

def verify_password(plain: str, hashed: str) -> bool:

    if hashed.startswith(("pbkdf2:", "scrypt:")):
        return _wz_check(hashed, plain)

    if hashed.startswith(("$2b$", "$2a$")):
        if _HAS_BCRYPT:
            try:
                return _bcrypt_lib.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
            except ValueError:
                return False
        return False

    return plain == hashed

def create_access_token(email: str) -> str:
    expire  = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MIN)
    payload = {"sub": email, "exp": expire, "type": "access"}
    if _HAS_JWT:
        return _pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    import base64, json
    header  = base64.urlsafe_b64encode(json.dumps({"alg": "HS256"}).encode()).decode()
    body    = base64.urlsafe_b64encode(json.dumps({"sub": email, "exp": expire.isoformat()}).encode()).decode()
    sig     = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{body}.{sig}"

def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)

def decode_access_token(token: str) -> Optional[str]:
    if not _HAS_JWT:

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
    if _HAS_BCRYPT:

        token_bytes = token.encode('utf-8')[:72]
        salt = _bcrypt_lib.gensalt()
        return _bcrypt_lib.hashpw(token_bytes, salt).decode('utf-8')
    return hashlib.sha256(token.encode()).hexdigest()

def verify_refresh_token(plain: str, hashed: str) -> bool:
    if _HAS_BCRYPT and hashed.startswith(("$2b$", "$2a$")):
        plain_bytes = plain.encode('utf-8')[:72]
        try:
            return _bcrypt_lib.checkpw(plain_bytes, hashed.encode('utf-8'))
        except ValueError:
            return False
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

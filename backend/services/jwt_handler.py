import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt as _pyjwt

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise ValueError(
            "CRITICAL: JWT_SECRET not set! Set JWT_SECRET in the deployment environment. "
            "Generating it in git or a local push does not provision the secret on the server. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    return secret

class JWTHandler:
    
    @staticmethod
    def create_access_token(email: str, user_id: str = None) -> str:
        """Create a short-lived JWT access token with standard claims."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
        jwt_secret = _get_jwt_secret()
        payload = {
            "sub": email,
            "user_id": user_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(8)
        }
        return _pyjwt.encode(payload, jwt_secret, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(email: str, user_id: str = None) -> str:
        """Create a longer-lived JWT refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        jwt_secret = _get_jwt_secret()
        payload = {
            "sub": email,
            "user_id": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(8)
        }
        return _pyjwt.encode(payload, jwt_secret, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def decode_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token with type checking."""
        try:
            payload = _pyjwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            if payload.get("type") != token_type:
                return None
            return payload
        except _pyjwt.ExpiredSignatureError:
            return None
        except _pyjwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_token_claims(token: str) -> Optional[Dict[str, Any]]:
        """Get claims from a token without type validation."""
        try:
            return _pyjwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        except Exception:
            return None


class PasswordHasher:
    """Secure password hashing with bcrypt."""
    
    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            import bcrypt
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        except ImportError:
            from werkzeug.security import generate_password_hash
            return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    @staticmethod
    def needs_rehash(stored: str) -> bool:
        """True if stored value is legacy plain text and should be upgraded."""
        if not stored or not isinstance(stored, str):
            return True
        return not stored.startswith(
            ("pbkdf2:", "scrypt:", "argon2:", "$2b$", "$2a$", "$2y$")
        )

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        """Verify password (bcrypt, werkzeug hashes, or legacy plain text)."""
        if not password or not hashed or not isinstance(hashed, str):
            return False

        if hashed.startswith(("pbkdf2:", "scrypt:", "argon2:")):
            from werkzeug.security import check_password_hash
            return check_password_hash(hashed, password)

        if hashed.startswith(("$2b$", "$2a$", "$2y$")):
            try:
                import bcrypt
                return bcrypt.checkpw(
                    password.encode("utf-8"), hashed.encode("utf-8")
                )
            except Exception:
                return False

        # Legacy accounts may have plain-text passwords from before auth hardening
        return hmac.compare_digest(password, hashed)


class TokenValidator:
    """Validates tokens against security policies."""
    
    @staticmethod
    def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate access token and return claims."""
        if not token:
            return None
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        claims = JWTHandler.decode_token(token, token_type="access")
        if not claims:
            return None
        
        # Additional validation: check required claims
        required_claims = ["sub", "type", "exp", "iat", "jti"]
        if not all(claim in claims for claim in required_claims):
            return None
        
        return claims
    
    @staticmethod
    def validate_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """Validate refresh token and return claims."""
        if not token:
            return None
        
        claims = JWTHandler.decode_token(token, token_type="refresh")
        if not claims:
            return None
        
        required_claims = ["sub", "type", "exp", "iat", "jti"]
        if not all(claim in claims for claim in required_claims):
            return None
        
        return claims
